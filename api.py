from websockets.sync.client import connect
import webbrowser
import requests
import uuid
import os
import json


class NexusMods:
    def __init__(self, logger_instance):
        self.logger = logger_instance
        self.api_key = self.__get_api_key()

    def __load_web_auth(self, user_uuid):
        application_slug = ""  # todo - get a slug linked to this
        webbrowser.open("https://www.nexusmods.com/sso?id="+user_uuid+"&application="+application_slug)
        self.logger.info("NexusModApi", "Launch Auth / Login Page")

    def __get_api_key(self) -> str | None:
        if os.path.exists("login_info.json"):
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




if __name__ == "__main__":
    from logger import Logger

    logger = Logger()
    NexusMods(logger)
