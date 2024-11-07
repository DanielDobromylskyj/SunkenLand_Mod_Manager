from websockets.sync.client import connect
import webbrowser
import requests
import uuid
import os
import json

from api.api_wrappers import cache_with_timeout as cache_with_timeout
from api.api_util import BaseAPI


class NexusMods(BaseAPI):  # Testing | Do I need to make server to handle api calls?
    def __init__(self, logger_instance):
        self.logger = logger_instance
        self.game_domain = "sunkenland"
        self.api_key = None
        self.headers = None

    def login(self):
        self.api_key = self.__get_api_key()
        self.headers = {
            "apikey": self.api_key,
        }

    @staticmethod
    def is_login_required():
        return not os.path.exists("login_info.json")

    def __load_web_auth(self, user_uuid):
        self.logger.fatal("NexusModApi",
                          "Web Auth is currently not available, to login, go to 'https://next.nexusmods.com/settings/api-keys', get your personal API key (FOR TESTING ONLY).\nThen, create a 'login_info.json' file, and add \"{'api_key':'<your-api-key>'}\"")

        application_slug = "NonValidApplication"  # todo - sso
        webbrowser.open("https://www.nexusmods.com/sso?id=" + user_uuid + "&application=" + application_slug)
        self.logger.info("NexusModApi", "Launched Auth / Login Page")

    def __get_api_key(self, force_web_auth=False):
        if os.path.exists("login_info.json") and not force_web_auth:
            self.logger.info("NexusModApi", "Loading Api Key")
            with open("login_info.json", "r") as f:
                login_info = json.load(f)

            return login_info["api_key"]
        else:
            self.logger.info("NexusModApi", "Generating UUID and Token")
            with connect("wss://sso.nexusmods.com") as websocket:
                user_uuid = str(uuid.uuid4())

                websocket.send(json.dumps({
                    "id": user_uuid,
                    "token": None,
                    "protocol": 2
                }))

                response = json.loads(websocket.recv())

                if response["success"] is False:
                    self.logger.fatal("NexusModApi", f"Failed to generate UUID and Token ({response['error']})")

                self.logger.info("NexusModApi", "UUID and Token Generated, Loading Auth page")
                self.__load_web_auth(user_uuid)

                response = json.loads(websocket.recv())

                if response["success"] is False:
                    self.logger.fatal("NexusModApi", f"Failed to get API-key ({response['error']})")

                with open("login_info.json", "w") as f:
                    json.dump({"api_key": response["data"]["api_key"]}, f)

                return response["data"]["api_key"]

    @cache_with_timeout(60)  # 60s
    def get_trending_mods(self):
        self.logger.info("NexusModApi", "GET | trending")

        response = requests.get(f"https://api.nexusmods.com/v1/games/{self.game_domain}/mods/trending.json",
                                headers=self.headers)
        return response.json()

    @cache_with_timeout(60)  # 60s
    def get_mod_info(self, mod_id: str):
        self.logger.info("NexusModApi", "GET | mod info | " + mod_id)

        response = requests.get(f"https://api.nexusmods.com/v1/games/{self.game_domain}/mods/{mod_id}.json",
                                headers=self.headers)
        return response.json()

    def download_file(self, mod_id, file):
        self.logger.info("NexusModApi", f"DOWNLOAD | {file['name']} | file_id={file['file_id']}")
        # todo - Find out how / if  I can do this

    def download_mod(self, mod_id: str):
        self.logger.info("NexusModApi", "GET | download | mod_id=" + mod_id)

        # Get all download files for a game
        response = requests.get(f"https://api.nexusmods.com/v1/games/{self.game_domain}/mods/{mod_id}/files.json",
                                headers=self.headers).json()

        for file in response["files"]:  # find the main file | todo - make it version controlled
            if file["category_name"] == "MAIN":
                self.download_file(mod_id, file)

if __name__ == "__main__":
    from logger import Logger

    logger = Logger()
    mods = NexusMods(logger)
    mods.download_mod("41")
