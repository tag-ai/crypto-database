"""
data_writer.py

A class for writing data to mongoDB, with a JSON fallback.

Author: Andrew Tan

"""
from pymongo import MongoClient
import json

class DataWriter:
    """
    Interfacing class to write to either Mongo or Json depending if it is available.
    """
    def __init__(self, hostname: str, port: int, json_outfile: str = 'outfile.json'):
        self.json_outfile = json_outfile
        try:
            print('Attempting to connect to mongo at {}:{}'.format(hostname, port))
            self.client = MongoClient(hostname, port)
            print('Connected!')
            self.db_is_available = True
        except:
            self.db_is_available = False
            print("Could not connect to mongo! Writing to JSON")

    def __bool__(self):
        # WARNING: Not python2 compatible
        return self.db_is_available

    def write_to_db(self, data: list, dbname: str, collection: str) -> None:
        """
        Pass a list of dictionaries to write in database.
        """
        db = self.client[dbname]
        c = db[collection]
        for d in data:
            c.insert(d, check_keys=False)

    def write_to_json(self, data: list, filename: str = '') -> None:
        f_name = filename if filename else self.json_outfile
        f_path = os.path.split(self.filename)[0]
        if f_path:
            if not os.path.exists(f_path):
                os.makedirs(f_path)
        with open(f_name, 'a+') as f:
            for d in data:
                json.dump(d, f)

    def write(self, data: list, dbname: str = '', collection: str = '',
                filename: str = '') -> None:
        if self.db_is_available:
            self.write_to_db(data, dbname, collection)
        else:
            self.write_to_json(data, filename)

    def get_collection_len(self, dbname: str, collection: str) -> int:
        if not self.db_is_available:
            return 0
        try:
            collection_len = self.client[dbname][collection].count()
        except:
            collection_len = 0
        return collection_len

    def flush(self, dbname: str) -> None:
        if self.db_is_available:
            self.client.drop_database(dbname)
