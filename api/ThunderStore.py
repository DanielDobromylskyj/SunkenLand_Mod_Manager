import requests
import time
import os

from api.api_util import BaseAPI
from api.db_manager import MyDB, create_db
from mod.util import Mod, ModVersion, ModList

from SunkenLand_Mod_Manager.mod.util import VersionList


def get_full_path(name):
    appdata_path = os.getenv('APPDATA')
    path = os.path.join(appdata_path, name)

    if not os.path.exists(path):
        os.mkdir(path)

    return path


class ThunderStore(BaseAPI):
    def __init__(self, logger):
        self.logger = logger

        self.ready_cache()
        self.cache = self.load_cache()
        self.update_cache()

        # tests
        #time.sleep(2)
        #mods = self.get_trending_mods()
        #mod = mods[4]
        #print(mod)
        #versions = self.get_mod_versions(mod)
        #version = versions.versions[0]
        #self.download_mod_version(version)

    def load_cache(self):
        self.logger.info("THUNDERSTORE", "Loading Cache")

        return MyDB(os.path.join(get_full_path("sunkenland_mod_manager"), "thunderstore.db"))

    @staticmethod
    def is_login_required():
        return False

    def ready_cache(self):
        if not os.path.exists(os.path.join(get_full_path("sunkenland_mod_manager"), "thunderstore.db")):
            self.logger.info("THUNDERSTORE", "No cache found! Generating empty cache")
            create_db(os.path.join(get_full_path("sunkenland_mod_manager"), "thunderstore.db"), [
                {
                    "name": "Mods",
                    "args": [
                        ("uuid", "TEXT PRIMARY KEY"),
                        ("full_name", "TEXT"),
                        ("display_name", "TEXT"),
                        ("owner", "TEXT"),
                        ("web_url", "TEXT"),
                        ("rating", "INTEGER"),
                        ("deprecated", "BOOLEAN"),
                        ("last_update", "TEXT")
                    ]
                },
                {
                    "name": "Versions",
                    "args": [
                        ("mod_uuid", "TEXT"),
                        ("full_name", "TEXT"),
                        ("display_name", "TEXT"),
                        ("description", "TEXT"),
                        ("icon_path", "TEXT"),
                        ("version", "TEXT"),
                        ("dependencies", "TEXT"),
                        ("download_url", "TEXT"),
                        ("downloads", "INTEGER"),
                        ("file_size", "INTEGER"),
                        ("date_created", "TEXT"),
                        ("cache_data", "BLOB DEFAULT NULL"),
                        ("enabled", "BOOLEAN DEFAULT FALSE"),
                        ("FOREIGN KEY(mod_uuid)", "REFERENCES Mods(uuid)"),
                        ("PRIMARY KEY", "(mod_uuid, version)")
                    ]
                }
            ])
        else:
            self.logger.info("THUNDERSTORE", "Found cache database")

    def update_cache(self):
        mods = self.__get_mod_list()  # using API - its slow (and expensive for host), so try not to use it

        self.logger.info("THUNDERSTORE", f"Cache | Pulled {len(mods)} mods")

        mod_data = []
        version_data = []
        for mod in mods:

            mod_data.append((mod["full_name"], mod["name"], mod["owner"], mod["package_url"],
                             mod["uuid4"], mod["rating_score"], mod["is_deprecated"], mod["date_updated"]))

            for version in mod["versions"]:
                version_data.append((mod["uuid4"], version["name"], version["full_name"], version["description"], version["icon"],
                                     version["version_number"], str(version["dependencies"]),
                                     version["download_url"], version["downloads"], version["file_size"],
                                     version["date_created"]))

        self.logger.info("THUNDERSTORE", f'Cache | Prepared Mods')

        self.cache.insert_or_ignore_many("Mods",
                                         ("full_name", "display_name", "owner", "web_url",
                                          "uuid", "rating", "deprecated", "last_update"),
                                         mod_data)

        self.cache.insert_or_ignore_many("Versions",
                                         ("mod_uuid", "display_name", "full_name", "description", "icon_path", "version",
                                          "dependencies", "download_url", "downloads", "file_size", "date_created"),
                                         version_data)

        self.logger.info("THUNDERSTORE", "Cache | Update Complete")

    def __get_mod_list(self):
        start = time.time()
        results = requests.get("https://thunderstore.io/c/sunkenland/api/v1/package/").json()
        self.logger.info("THUNDERSTORE", f"GET | Mod List | Took {round((time.time() - start) * 1000)}ms")
        return results

    def search_for_mods(self, query):
        mod_info = self.cache.request(
            "Mods",
            "full_name LIKE ?;",
            "uuid, display_name, owner, web_url, rating, deprecated, last_update",
            (f"%{query}%",)
        )

        list_of_mods = ModList()
        for mod_data in mod_info:
            list_of_mods.add_mod(Mod(*mod_data))

        return list_of_mods

    def get_mod_versions(self, mod):
        versions = self.cache.request(
            "Versions",
            "mod_uuid = ?",
            "mod_uuid, display_name, description, icon_path, version, dependencies, download_url, downloads, file_size, date_created",
            (mod.mod_id,)
        )

        list_of_versions = VersionList()
        for version in versions:
            list_of_versions.add_version(ModVersion(*version))

        return list_of_versions

    def get_trending_mods(self, limit=10):
        mod_info = self.cache.request(
            "Mods",
            "deprecated = false",
            "uuid, display_name, owner, web_url, rating, deprecated, last_update",
            None,
            other=f"ORDER BY rating DESC LIMIT {limit}"
        )

        list_of_mods = ModList()
        for mod_data in mod_info:
            list_of_mods.add_mod(Mod(*mod_data))

        return list_of_mods

    def get_mod_version_cache(self, mod_version):
        result = self.cache.request(
            "Versions",
            "mod_uuid = ? AND version = ?",
            "cache_data",
            (mod_version.mod_id, mod_version.version)
        )

        if len(result) > 0:
            return result[0][0]

    def is_mod_version_enabled(self, mod_version):
        result = self.cache.request(
            "Versions",
            "mod_uuid = ? AND version = ?",
            "enabled",
            (mod_version.mod_id, mod_version.version)
        )

        return result[0][0]

    def __get_version_from_full_name(self, full_name):
        results = self.cache.request(
            "Versions",
            "full_name = ?",
            "mod_uuid, display_name, description, icon_path, version, dependencies, download_url, downloads, file_size, date_created",
            (full_name,)
        )

        if len(results) > 0:
            return ModVersion(*results[0])

    @staticmethod
    def __get_blob_from_url(download_url):
        return requests.get(download_url).content

    def __write_cache(self, mod_version, cache):
        self.cache.update(
            "Versions",
            ("cache_data",),
            "mod_uuid = ? AND version = ?",
            (cache, mod_version.mod_id, mod_version.version)
        )

    def __download(self, mod_version):
        self.logger.info("THUNDERSTORE",
                         f"DOWNLOADING | {mod_version.display_name} ({mod_version.version}) | {round(mod_version.file_size / (1024 ** 2), 2)}Mb")
        main_blob = self.__get_blob_from_url(mod_version.download_url)
        self.__write_cache(mod_version, main_blob)

        failed_dependency_count = 0
        for dependency in mod_version.dependencies:
            dependency_mod = self.__get_version_from_full_name(dependency)

            if not dependency_mod:
                self.logger.error("THUNDERSTORE", f"DEPENDENCY NOT FOUND | {dependency}")
                failed_dependency_count += 1
                continue

            if self.get_mod_version_cache(dependency_mod) is None:
                self.__download(dependency_mod)
            else:
                self.logger.info("THUNDERSTORE",
                                 f"DOWNLOADING | {dependency_mod.display_name} ({dependency_mod.version}) | Found In Cache")

    def download_mod_version(self, mod_version):
        cache_data = self.get_mod_version_cache(mod_version)

        if cache_data is None:
            self.__download(mod_version)

    def enable_mod_version(self, mod_version):
        raise NotImplementedError


    def disable_mod_version(self, mod_version):
        raise NotImplementedError



