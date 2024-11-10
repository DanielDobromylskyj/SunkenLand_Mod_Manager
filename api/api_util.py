

class BaseAPI:
    def __init__(self):
        pass

    def get_trending_mods(self) -> list:
        raise NotImplementedError

    def get_mod_versions(self, mod) -> dict:
        raise NotImplementedError

    def download_mod_version(self, mod_version):
        raise NotImplementedError

    def search_for_mods(self, search_query: str) -> list:
        raise NotImplementedError

    def enable_mod_version(self, mod_version):
        raise NotImplementedError

    def disable_mod_version(self, mod_version):
        raise NotImplementedError
