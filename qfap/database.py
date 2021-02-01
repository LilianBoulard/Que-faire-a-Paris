import os
import pymongo
import logging
import dateutil.parser as dp

from time import time
from typing import List

from .event import Event


def assert_database(func):
    """
    Decorator used to assert the database attribute (`self._db`) is set.
    """
    def wrapper(self, *args, **kwargs):
        assert self._db is not None
        return func(self, *args, **kwargs)
    return wrapper


def assert_database_and_collection(func):
    """
    Decorator used to assert the collection attribute (`self._collection`) is set.
    Also asserts database attribute.
    """
    def wrapper(self, *args, **kwargs):
        assert self._collection is not None
        assert self._db is not None
        return func(self, *args, **kwargs)
    return wrapper


class Database:

    srv_env_var = 'QFAP_SERVER'
    srv_args = '?retryWrites=true&w=majority'

    def __init__(self, database_name: str = None, collection_name: str = None):
        # Get server's address
        db_addr = os.getenv(self.srv_env_var)
        if not db_addr:
            raise ValueError(f'{self.srv_env_var!r} environment variable is not set')

        # Create client (connect to the server)
        self._client = pymongo.MongoClient(f"{db_addr}{self.srv_args}")

        # Set the database to None by default ; if a database name is passed, we will try to switch.
        self._db: pymongo.database.Database = None
        if database_name:
            self.select_database(database_name)

        self._collection: pymongo.collection.Collection = None
        if collection_name:
            self.select_collection(collection_name)

    def select_database(self, db_name: str) -> None:
        """
        Switch instance's database.

        :param str db_name: The name of the database we want to switch to.
        :raises ValueError: If the database name is invalid.
        """
        available_databases = self._client.list_database_names()
        if db_name not in available_databases:
            raise ValueError(f'Invalid database name {db_name!r}. Pick one from {available_databases}')

        logging.info(f'Switching to database {db_name!r}')
        self._db = self._client.get_database(db_name)

    def select_collection(self, collection_name: str) -> None:
        available_collections = self._db.list_collection_names()
        if collection_name not in available_collections:
            raise ValueError(f'Invalid collection name {collection_name!r}. Pick one from {available_collections}')

        logging.info(f'Switching to collection {collection_name!r}')
        self._collection = self._db.get_collection(collection_name)

    @assert_database_and_collection
    def get_coming_x_events(self, num: int) -> List[Event]:
        """
        Queries the database to get the nearest incoming `num` events.

        :param int num: How many events we want to list.
        :return List[Event]: A list containing the Events, ordered from the closest to the most distant (in time).
        """
        criteria = 'date_start'
        # Filters events to keep only the future ones
        future_events = []
        current_dt = int(time())
        for info in self._collection.find():
            info = info['fields']
            info_dt = dp.parse(info[criteria]).timestamp()
            if info_dt > current_dt:
                future_events.append(info)

        future_events.sort(key=lambda x: x[criteria], reverse=False)

        return [Event(info) for info in future_events[:num]]

    @assert_database_and_collection
    def get_unique_event_by_id(self, identifier: int) -> Event:
        query = {
            'fields.id': str(identifier)
        }
        return Event(self._collection.find_one(query)['fields'])
