import requests

class Mod:
    def __init__(self, mod_id, display_name, owner, web_url, rating, deprecated, last_updated):
        self.mod_id = mod_id
        self.display_name = display_name
        self.mod_owner = owner
        self.web_url = web_url
        self.rating = rating
        self.deprecated = deprecated
        self.last_updated = last_updated


class ModVersion:
    def __init__(self, mod_id, display_name, desc, icon_path, version, dependencies, download_url, downloads, file_size, date_created, cache=None):
        self.mod_id = mod_id
        self.display_name = display_name
        self.desc = desc
        self.icon_path = icon_path
        self.version = version
        self.dependencies = dependencies
        self.download_url = download_url
        self.downloads = downloads
        self.file_size = file_size
        self.date_created = date_created

        self.cache = cache

    def __get_via_download(self, uuid) -> bytes:
        return self.cache.download_version_callback(uuid)

    def get(self, uuid) -> bytes:
        if self.cache.mod_version_is_cached(uuid):
            return self.cache.get_version_cache(uuid)
        else:
            return self.__get_via_download(uuid)


class ModList:
    def __init__(self):
        self.mods = []

    def add_mod(self, mod):
        self.mods.append(mod)

    def __iter__(self):
        for mod in mods:
            yield mod

    def __getitem__(self, item):
        for mod in self:
            if mod.mod_id == item:
                return mod
