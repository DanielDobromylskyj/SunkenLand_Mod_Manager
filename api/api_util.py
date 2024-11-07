

class BaseAPI:
    def __init__(self):
        pass

    def get_trending_mods(self) -> list:
        raise NotImplementedError

    def get_mod_info(self, mod_id: str) -> dict:
        raise NotImplementedError

    def download_mod(self, mod_id: str):
        raise NotImplementedError

    def search_for_mods(self, search_query: str) -> list:
        raise NotImplementedError
