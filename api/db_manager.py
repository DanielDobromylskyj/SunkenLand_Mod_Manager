import os
import sqlite3

"""
table_data format:

[
    {
        "name": 'name',
        "args": [("name1", "type"), ...]
    },
    ...
]

"""


def create_db(path, table_data):
    db = sqlite3.connect(path)
    cursor = db.cursor()

    for table in table_data:
        cursor.execute(f"CREATE TABLE {table['name']} ({', '.join([
            f"{col} {datatype}" for col, datatype in table['args']
        ])});")

        db.commit()

    cursor.close()
    db.close()


def does_db_exist(path):
    return os.path.exists(path)


class DatabaseFailure(Exception):
    pass


class Cursor:
    def __init__(self, my_db):
        self.db = my_db.get_db()
        self.cursor = self.db.cursor()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params if params else ())

    def executemany(self, sql, params):
        self.cursor.executemany(sql, params if params else ())

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        data = self.cursor.fetchone()
        return data[0] if len(data) != 0 else []

    def commit_to_db(self):
        self.db.commit()

    def return_with_data(self, return_one=False):
        results = self.fetchall() if return_one is False else self.fetchone()
        self.close()
        return results

    def close(self):
        self.cursor.close()
        self.db.close()


class MyDB:
    def __init__(self, path):
        self.path = path

    def get_db(self):
        if does_db_exist(self.path):
            return sqlite3.connect(self.path)
        raise DatabaseFailure("Database does not exist")

    def request(self, table, conditions, columns, param_data, other=""):
        """ WARNING table/data/conditions ARE NOT INJECTION SAFE, DO NOT USE USER INPUTS """

        cursor = Cursor(self)
        cursor.execute(f"SELECT {columns} FROM {table} WHERE {conditions} {other}", param_data)
        return cursor.return_with_data()

    def insert(self, table, param_names, param_data):
        cursor = Cursor(self)
        cursor.execute(
            f"INSERT INTO {table} ({', '.join(param_names)}) VALUES ({", ".join(['?' for i in range(len(param_data))])})",
            param_data)

        cursor.commit_to_db()
        cursor.close()

    def update(self, table, param_names: tuple, conditions, param_data):
        cursor = Cursor(self)

        cursor.execute(f"UPDATE {table} SET {' = ?, '.join(param_names)} = ? WHERE {conditions}", param_data)

        cursor.commit_to_db()
        cursor.close()

    def delete(self, table, param_names, param_data):
        cursor = Cursor(self)
        cursor.execute(f"DELETE FROM {table} WHERE {param_names}", param_data)

        cursor.commit_to_db()
        cursor.close()

    def insert_or_ignore_many(self, table, param_names, param_data):
        cursor = Cursor(self)

        cursor.executemany(
            f"INSERT OR IGNORE INTO {table} ({', '.join(param_names)}) VALUES ({", ".join(['?' for i in range(len(param_names))])})",
            param_data)

        cursor.commit_to_db()
        cursor.close()
