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

    def __str__(self):
        return f"<Mod mod_id={self.mod_id}, display_name={self.display_name}, mod_owner={self.mod_owner}>"


class ModVersion:
    def __init__(self, mod_id, display_name, desc, icon_path, version, dependencies, download_url, downloads, file_size, date_created, cache=None):
        self.mod_id = mod_id
        self.display_name = display_name
        self.desc = desc
        self.icon_path = icon_path
        self.version = version
        self.dependencies = eval(dependencies)
        self.download_url = download_url
        self.downloads = downloads
        self.file_size = file_size
        self.date_created = date_created

        self.cache = cache

    def __get_via_download(self) -> bytes:
        return self.cache.download_version_callback(self)

    def get(self) -> bytes:
        if self.cache.mod_version_is_cached(self.mod_id, self.version):
            return self.cache.get_version_cache(self.mod_id, self.version)
        else:
            return self.__get_via_download()

    def __str__(self):
        return f"<ModVersion mod_id={self.mod_id}, display_name={self.display_name}, version={self.version}, file_size={self.file_size}, dependencies={self.dependencies}>"


class ModList:
    def __init__(self):
        self.mods = []

    def add_mod(self, mod):
        self.mods.append(mod)

    def __iter__(self):
        for mod in self.mods:
            yield mod

    def __getitem__(self, item):
        for mod in self:
            if mod.mod_id == item:
                return mod
