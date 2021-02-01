import os
import pymongo
import logging

from time import time
from typing import List, Tuple

from .event import Event
from .utils import convert_iso8601_to_timestamp


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
    def get_coming_x_events_by_category(self, num: int) -> List[Event]:
        pass

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
            info_dt = convert_iso8601_to_timestamp(info[criteria])
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

    @assert_database_and_collection
    def get_all_categories(self) -> dict:
        """
        Gathers all the categories from the database.
        :return dict: A dictionary containing for each key a main category, and as the value a list of sub-categories.
        """

        def treat_cat(cat: str) -> Tuple[str, str]:
            """
            Takes a category and splits it, returning a tuple containing (1) the main category, (2) the sub-category.
            :param str cat: A category. e.g: "Musique -> Concert"
            """
            main_cat, sub_cat = cat.split('>')
            main_cat = main_cat.strip('-').strip(' ')
            sub_cat = sub_cat.strip(' ')
            return main_cat, sub_cat

        categories = {}
        for info in self._collection.find():
            # *Technically* it would be smarter to create an event with each info,
            # but it's not the most optimized way of doing it.
            # Here, we will assume `category` is never missing.
            # If by any mean it is missing, it will raise a KeyError.
            main_category, sub_category = treat_cat(info['fields']['category'])
            if main_category in categories.keys():
                if sub_category not in categories[main_category]:
                    categories[main_category].append(sub_category)
            else:
                categories[main_category] = [sub_category]

        return categories

    @assert_database_and_collection
    def search(self, f: Filter):
        pass
