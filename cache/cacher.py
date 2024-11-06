import sqlite3
import threading
import time
import os


class Cache:
    def __init__(self, name: str, update_callback):
        self.path = self.get_full_path(name)
        self.last_cache_update = -1
        self.time_between_cache_updates = 30 * 60
        self.update_callback = update_callback

    @staticmethod
    def get_full_path(name):
        appdata_path = os.getenv('APPDATA')
        path = os.path.join(appdata_path, name)

        if not os.path.exists(path):
            os.mkdir(path)

        return path

    def get_db_path(self):
        return os.path.join(self.path, 'cache.db')

    def db_exists(self):
        return os.path.exists(self.get_db_path())

    def create_db(self):
        conn = sqlite3.connect(self.get_db_path())
        cursor = conn.cursor()

        # Create Mods table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Mods (
            full_name TEXT,
            display_name TEXT,
            owner TEXT,
            web_url TEXT,
            uuid TEXT PRIMARY KEY,
            rating INTEGER,
            deprecated BOOLEAN,
            last_update TEXT
        )
        ''')

        # Create Versions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Versions (
            mod_uuid TEXT,
            display_name TEXT,
            description TEXT,
            icon_path TEXT,
            version TEXT,
            dependencies TEXT,
            download_url TEXT,
            downloads INTEGER,
            file_size INTEGER,
            date_created TEXT,
            cache_data BLOB DEFAULT NULL,
            FOREIGN KEY(mod_uuid) REFERENCES Mods(uuid)
        )
        ''')

        # Commit and close the connection
        conn.commit()
        conn.close()

    def get_db(self):
        if self.db_exists():
            return sqlite3.connect(self.get_db_path())

    def clear_cache(self):
        os.remove(self.get_db_path())

    def force_update_cache(self):
        self.last_cache_update = time.time()
        threading.Thread(target=self.update_callback, daemon=True).start()

    def update_cache_if_required(self):
        if time.time() - self.time_between_cache_updates > self.last_cache_update:
            self.force_update_cache()

    def push_mod(self, full_name, display_name, owner, web_url, mod_uuid4, rating, deprecated, last_update):
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.execute('''
        INSERT OR REPLACE INTO Mods (full_name, display_name, owner, web_url, uuid, rating, deprecated, last_update)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (full_name, display_name, owner, web_url, mod_uuid4, rating, deprecated, last_update))

        conn.commit()
        conn.close()

    def push_mod_version(self, mod_uuid, display_name, desc, icon_path, version, dependencies, download_url, downloads, file_size, date_created):
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO Versions (mod_uuid, display_name, description, icon_path, version, dependencies, download_url, downloads, file_size, date_created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (mod_uuid, display_name, desc, icon_path, version, dependencies, download_url, downloads, file_size,
              date_created))

        conn.commit()
        conn.close()

    def push_many_mods(self, data):
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.executemany('''
        INSERT INTO Mods (full_name, display_name, owner, web_url, uuid, rating, deprecated, last_update)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

        conn.commit()
        conn.close()

    def push_many_versions(self, data):
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.executemany('''
        INSERT INTO Versions (mod_uuid, display_name, description, icon_path, version, dependencies, download_url, downloads, file_size, date_created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

        conn.commit()
        conn.close()

    def search_for_mod(self, search_term):
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM Mods
        WHERE full_name LIKE ?
        ''', ('%' + search_term + '%',))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_mod_versions(self, mod_uuid):
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM Versions
        WHERE mod_uuid = ?
        ''', (mod_uuid,))


        results = cursor.fetchall()
        conn.close()

        return results

