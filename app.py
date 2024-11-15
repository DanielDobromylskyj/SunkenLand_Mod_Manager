import dearpygui.dearpygui as dpg
from functools import partial
from threading import Thread
import time
import os

from logger import Logger

import api.NexusMods
import api.ThunderStore


def wrap_text(text, max_length):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 > max_length:
            lines.append(current_line)
            current_line = word
        else:
            if current_line:
                current_line += " "
            current_line += word

    if current_line:
        lines.append(current_line)

    return "\n".join(lines)


def hard_wrap(text, max_length):
    words = list(text)
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 > max_length:
            lines.append(current_line)
            current_line = word
        else:
            current_line += word

    if current_line:
        lines.append(current_line)

    return "\n".join(lines)


class App:
    def __init__(self):
        self.logger = Logger()

        self.mod_apis = [api.ThunderStore.ThunderStore]
        self.loaded_mod_apis = []

        self.font_path = os.path.abspath("fonts/OpenSans.ttf")

        self.loaded_mods = []
        self.loaded_mods_display = []

        self.loaded_mod_versions = []
        self.loaded_mod_versions_display = []

        self.selected_version = None
        self.current_mod_api = None

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

        print("Go!")
        self.__get_trending_mods()

    def __get_trending_mods(self):
        self.loaded_mods = []
        mods_per_api = 100 // len(self.loaded_mod_apis)

        for loaded_api in self.loaded_mod_apis:
            mods = loaded_api.get_trending_mods(limit=mods_per_api)

            for mod in mods:
                self.loaded_mods.append((loaded_api, mod))

        self.__update_mod_display()

    def __update_mod_display(self):
        self.loaded_mods_display = [mod.display_name for loaded_api, mod in self.loaded_mods]
        dpg.configure_item("mod_display", items=self.loaded_mods_display)
        self.load_items()

    def __search_callback(self, *args):
        self.loaded_mods = []
        search_value = dpg.get_value("search_input")

        for loaded_api in self.loaded_mod_apis:
            mods = loaded_api.search_for_mods(search_value)

            for mod in mods:
                self.loaded_mods.append((loaded_api, mod))

        self.__update_mod_display()

    def get_mod_from_name(self, name):
        return self.loaded_mods[self.loaded_mods_display.index(name)][1]

    def get_mod_api_from_name(self, name):
        return self.loaded_mods[self.loaded_mods_display.index(name)][0]

    def get_mod_api_from_id(self, mod_id):
        for loaded_api, mod in self.loaded_mods:
            if mod.id == mod_id:
                return loaded_api

    def __update_preview_version(self, sender, app_data, user_data):
        self.selected_version = self.loaded_mod_versions[self.loaded_mod_versions_display.index(app_data)]
        text = self.selected_version.desc

        dpg.set_value("viewing_description", wrap_text(text, 70))
        dpg.set_item_label("viewing_download_button", f"Download (version {self.selected_version.version})")

        dpg.show_item("viewing_description")
        dpg.show_item("viewing_description_seperator")
        dpg.show_item("viewing_download_button")

    def __update_preview(self, sender, app_data, user_data):
        mod = self.get_mod_from_name(app_data)
        mod_api = self.get_mod_api_from_name(app_data)

        self.current_mod_api = mod_api
        self.loaded_mod_versions = mod_api.get_mod_versions(mod)
        self.loaded_mod_versions.reverse()

        self.loaded_mod_versions_display = [version.version for version in self.loaded_mod_versions]

        dpg.set_value("viewing_title", f"Mod: {mod.display_name} {'(DEPRECATED)' if mod.deprecated else ''}")
        dpg.set_value("viewing_details", f"Made By: {mod.mod_owner}\nWeb: {hard_wrap(mod.web_url, 65)}\nRating: {mod.rating}\nUUID: {mod.mod_id}")
        dpg.configure_item("viewing_versions", items=self.loaded_mod_versions_display)

        self.__update_preview_version(sender, self.loaded_mod_versions_display[0], user_data)

    def __download_clicked(self):
        self.logger.info("APP", "Starting Mod Download")

        self.current_mod_api.download_mod_version(self.selected_version)
        self.load_items()

    def __load_ui(self):  # Cut me some slack, 2nd time using dpg
        self.logger.info("APP", "Loading UI")

        with dpg.window(label="Main", tag="MainMenu", no_resize=True, no_close=True,
                        no_title_bar=True, no_move=True):
            dpg.add_text("Sunkenland Mod Manager - Supporting Thunderstore.io & NexusMods (one day)")

            with dpg.tab_bar():
                with dpg.tab(label="My Mods", tag="my_mod_tab"):
                    with dpg.group(horizontal=True):
                        with dpg.child_window(width=250, height=-10) as self.list_window:
                            self.load_items()

                        with dpg.child_window(width=500, height=-10):
                            dpg.add_text("No Mod", tag="viewing_title2")
                            dpg.add_separator()
                            dpg.add_text("No Data", tag="viewing_details2")
                            dpg.add_separator()
                            dpg.add_text("No Desc", tag="viewing_description2", show=False)
                            dpg.add_separator(show=False, tag="viewing_description_seperator2")

                with dpg.tab(label="Search Mods"):
                    with dpg.group(horizontal=True):
                        with dpg.child_window(width=250, height=-10):
                            dpg.add_text("Search")
                            dpg.add_input_text(label="", tag="search_input", hint="Type to search...", width=230, callback=self.__search_callback)
                            dpg.add_text("Mods:")

                            dpg.add_listbox(self.loaded_mods_display, tag="mod_display", label="", width=230, num_items=35, callback=self.__update_preview)

                        with dpg.child_window(width=500, height=-10):
                            dpg.add_text("No Mod", tag="viewing_title")
                            dpg.add_separator()
                            dpg.add_text("No Data", tag="viewing_details")
                            dpg.add_separator()

                            dpg.add_text("No Desc", tag="viewing_description", show=False)
                            dpg.add_separator(show=False, tag="viewing_description_seperator")

                            dpg.add_button(label="Download", tag=f"viewing_download_button", callback=self.__download_clicked, show=False)

                            dpg.add_text("Versions:")
                            dpg.add_listbox(items=[], tag="viewing_versions", width=484, callback=self.__update_preview_version)

    def load_items(self, *args):
        dpg.delete_item(self.list_window, children_only=True)

        for i, display_item in enumerate(self.loaded_mods_display):
            api, mod = self.loaded_mods[i]
            mod_versions = api.get_mod_versions(mod)
            for version in mod_versions:
                has_cache = api.get_mod_version_cache(version)

                if has_cache:
                    enabled = api.is_mod_version_enabled(version) is True

                    with dpg.group(horizontal=True, parent=self.list_window):
                        dpg.add_checkbox(label="", default_value=enabled, tag=f"my_mod_list_enable_flag:{i}:{version.version}",
                                         callback=self.toggle_item)

                        dpg.add_button(label=f"{display_item} ({version.version})", width=180, tag=f"my_mod_list_button:{i}:{version.version}",
                                       callback=self.load_item_details)

    def toggle_item(self, item_tag, sender, data):
        item = self.loaded_mods[int(item_tag.split(":")[1])]
        item["active"] = not item["active"]
        self.load_items()

    def load_item_details(self, item_tag, sender, data):
        mod_api, mod = self.loaded_mods[int(item_tag.split(":")[1])]
        versions = mod_api.get_mod_versions(mod)
        version = versions[item_tag.split(":")[2]]

        dpg.set_value("viewing_title2", f"Mod: {mod.display_name} {'(DEPRECATED)' if mod.deprecated else ''}")
        dpg.set_value("viewing_details2", f"Made By: {mod.mod_owner}\nWeb: {hard_wrap(mod.web_url, 65)}\nRating: {mod.rating}\nUUID: {mod.mod_id}")

        dpg.set_value("viewing_description2", f"Description for {wrap_text(version.desc, 70)}")

        dpg.show_item("viewing_description2")
        dpg.show_item("viewing_description_seperator2")

    def resize_window(self):
        dpg.configure_item("MainMenu", width=self.viewport_width, height=self.viewport_height)

    def viewport_resize_callback(self, sender, app_data):
        self.viewport_width, self.viewport_height = app_data[0], app_data[1]
        self.resize_window()

    def run(self):
        dpg.create_context()

        self.__load_ui()
        Thread(target=self.__init_apis, daemon=False).start()

        self.logger.info("APP", "Creating Viewport")
        dpg.create_viewport(title='Mod Manager')

        dpg.set_viewport_resize_callback(self.viewport_resize_callback)

        self.logger.info("APP", "Setting up dearpygui")
        dpg.setup_dearpygui()
        dpg.show_viewport()

        dpg.start_dearpygui()
        dpg.destroy_context()


if __name__ == "__main__":
    app = App()
    app.run()
