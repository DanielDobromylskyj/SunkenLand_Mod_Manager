import dearpygui.dearpygui as dpg
from threading import Thread

from logger import Logger

import api.NexusMods
import api.ThunderStore


class App:
    def __init__(self):
        self.logger = Logger()

        self.mod_apis = [api.ThunderStore.ThunderStore]
        self.loaded_mod_apis = []

    def __init_apis(self):
        self.logger.info("LOADER", f"Attempting to loading {len(self.mod_apis)} APIs...")
        for mod_index, mod_api in enumerate(self.mod_apis):
            self.logger.info("LOADER", f"Loading {mod_api.__name__} ({mod_index + 1}/{len(self.mod_apis)})")
            loaded_api = mod_api(self.logger)

            if loaded_api.is_login_required():
                self.logger.info("LOADER", f"{mod_api.__name__} API Required Auth/Login")
                self.__make_api_load_window(mod_api.__name__, loaded_api)

            self.logger.info("LOADER", f"Logged in to {mod_api.__name__}")
            self.loaded_mod_apis.append(loaded_api)

    def __make_api_load_window(self, api_name, loaded_api):
        # loaded_api.login()  -> then add it to loaded apis IF they agree / sso

        with dpg.window(label=f"Auth Required - {api_name}", tag="auth_window", width=400, height=200, no_resize=True,
                        no_close=True):
            dpg.add_text(f"To fetch mods from {api_name}, we need you to sign-in.")

    def __load_ui(self):  # Cut me some slack, 2nd time using dpg
        self.logger.info("APP", "Loading UI")

        with dpg.window(label="Main", tag="MainMenu", no_resize=True, no_close=True,
                        no_title_bar=True, no_move=True):
            dpg.add_text("This is Window.")

    def resize_window(self):
        dpg.configure_item("MainMenu", width=self.viewport_width, height=self.viewport_height)

    def viewport_resize_callback(self, sender, app_data):
        self.viewport_width, self.viewport_height = app_data[0], app_data[1]
        self.resize_window()

    def run(self):
        dpg.create_context()

        Thread(target=self.__init_apis, daemon=True).start()
        self.__load_ui()

        self.logger.info("APP", "Creating Viewport")
        dpg.create_viewport(title='Sunkenland Mod Manager')

        dpg.set_viewport_resize_callback(self.viewport_resize_callback)

        self.logger.info("APP", "Setting up dearpygui")
        dpg.setup_dearpygui()
        dpg.show_viewport()

        dpg.start_dearpygui()
        dpg.destroy_context()


if __name__ == "__main__":
    app = App()
    app.run()
