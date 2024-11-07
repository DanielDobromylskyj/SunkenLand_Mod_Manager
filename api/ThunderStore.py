from cache.cacher import Cache
import requests
import time

from api.api_util import BaseAPI


class ThunderStore(BaseAPI):
    def __init__(self, logger):
        self.logger = logger

        self.cache = self.load_cache()
        self.ready_cache()

        # tests
        time.sleep(5)
        print("Getting mods")
        mods = self.search_for_mods("r2modman")

        for mod in mods:
            vers = self.get_mod_available_versions(mod)
            for ver in vers:
                if (ver.display_name == "r2modman") and (ver.version == "3.0.0"):
                    print(ver)
                    ver.get()

    def load_cache(self):
        self.logger.info("THUNDERSTORE", "Loading Cache")

        return Cache(
            "thunderstore",
            update_callback=self.update_cache,
            download_version_callback=self.download_callback
        )

    @staticmethod
    def is_login_required():
        return False

    def ready_cache(self):
        if not self.cache.db_exists():
            self.logger.info("THUNDERSTORE", "No cache found! Generating empty cache")
            self.cache.create_db()
        else:
            self.logger.info("THUNDERSTORE", "Found cache database")

        self.cache.update_cache_if_required()

    def download_dependency(self, dependency):
        self.logger.info("THUNDERSTORE", f"Downloading | Dependency | {dependency}")

    def download_callback(self, mod_version):
        self.logger.info("THUNDERSTORE", f"Downloading | Mod | {mod_version}")

        self.logger.info("THUNDERSTORE", f"Downloading | Mod | Getting dependencies")
        for dependency in mod_version.dependencies:
            self.download_dependency(dependency)

        self.logger.info("THUNDERSTORE", f"Downloading | Mod | Getting main file")

        response = requests.get(mod_version.download_url)
        return response.content

    def update_cache(self):
        mods = self.__get_mod_list()  # using API - its slow (and expensive for host), so try not to use it

        self.logger.info("THUNDERSTORE", f"Cache | Pulled {len(mods)} mods")

        mod_data = []
        version_data = []
        for mod in mods:

            mod_data.append((mod["full_name"], mod["name"], mod["owner"], mod["package_url"],
                             mod["uuid4"], mod["rating_score"], mod["is_deprecated"], mod["date_updated"]))

            for version in mod["versions"]:
                version_data.append((mod["uuid4"], version["name"], version["description"], version["icon"],
                                     version["version_number"], str(version["dependencies"]),
                                     version["download_url"], version["downloads"], version["file_size"],
                                     version["date_created"]))

        self.logger.info("THUNDERSTORE", f'Cache | Prepared Mods')

        self.cache.clear_cache()
        with self.cache.lock:
            self.cache.push_many_mods(mod_data)
            self.cache.push_many_versions(version_data)

        self.logger.info("THUNDERSTORE", "Cache | Update Complete")

    def __get_mod_list(self):
        start = time.time()
        results = requests.get("https://thunderstore.io/api/v1/package/?game=sunkenland").json()
        self.logger.info("THUNDERSTORE", f"GET | Mod List | Took {round((time.time() - start) * 1000)}ms")
        return results

    def search_for_mods(self, query):
        return self.cache.search_for_mod(query)

    def get_mod_available_versions(self, mod):
        if type(mod) is str:
            return self.cache.get_mod_versions(mod)
        return self.cache.get_mod_versions(mod.mod_id)
