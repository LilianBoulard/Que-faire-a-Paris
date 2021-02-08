import os
import random
import shelve
import pymongo
import logging

from time import time
from typing import List, Set

from .event import Event
from .filter import Filter


class Database:

    srv_env_var: str = 'QFAP_SERVER'
    srv_args: str = '?retryWrites=true&w=majority'

    def __init__(self, database_name: str, collection_name: str):
        # Get server's address
        db_addr = os.getenv(self.srv_env_var)
        if not db_addr:
            raise ValueError(f'{self.srv_env_var!r} environment variable is not set')

        # Create client (connect to the server)
        self._client = pymongo.MongoClient(f"{db_addr}{self.srv_args}")

        # Select database and collection
        self._select_database(database_name)
        self._select_collection(collection_name)

        self._preprocess()

    def _preprocess(self) -> None:
        """
        Is in charge of creating a cache, which will hold often-computed information.
        """
        self.cache = Cache(self._db, self._collection)

        for info in self._collection.find():
            self.cache.store_category(info)

    def _select_database(self, db_name: str) -> None:
        """
        Select instance's database.

        :param str db_name: The name of the database we want to switch to.
        :raises ValueError: If the database name is invalid.
        """
        available_databases = self._client.list_database_names()
        if db_name not in available_databases:
            raise ValueError(f'Invalid database name {db_name!r}. Pick one from {available_databases}')

        logging.info(f'Selecting database {db_name!r}')
        self._db: pymongo.database.Database = self._client.get_database(db_name)

    def _select_collection(self, collection_name: str) -> None:
        """
        Select instance's collection

        :param str collection_name: The name of the collection we want to switch to.
        :raises ValueError: If the database name is invalid.
        """
        available_collections = self._db.list_collection_names()
        if collection_name not in available_collections:
            raise ValueError(f'Invalid collection name {collection_name!r}. Pick one from {available_collections}')

        logging.info(f'Selecting collection {collection_name!r}')
        self._collection: pymongo.collection.Collection = self._db.get_collection(collection_name)

    def get_future_events(self, additional_filter: dict = None) -> List[Event]:
        current_time = int(time())
        if not additional_filter:
            additional_filter = {}
        additional_filter.update({'fields.date_start': {'$gt': current_time}})
        future_events = self._collection.find(additional_filter, {'fields': 1})
        return [Event(info['fields']) for info in future_events]

    def get_future_events_by_category(self, category: str) -> List[Event]:
        return self.get_future_events({'fields.category': category})

    def get_coming_events_by_category(self, num: int, category: str) -> List[Event]:
        """
        Queries the database to get the nearest incoming `num` events in the category specified.

        :param int num: How many events we want to list.
        :param str category: The category to search in. e.g: "Concerts -> Jazz"
        :return List[Event]: A list containing the Events, ordered from the closest to the most distant (in time).
        """
        future_events = self.get_future_events_by_category(category)
        future_events.sort(key=lambda x: x.date_start, reverse=False)
        return future_events[:num]

    def get_random_coming_events_by_category(self, num: int, category: str, random_state: int) -> List[Event]:
        random.seed(random_state)
        future_events = self.get_future_events_by_category(category)
        random.shuffle(future_events)
        return future_events[:num]

    def get_coming_events(self, num: int) -> List[Event]:
        """
        Queries the database to get the nearest incoming `num` events.

        :param int num: How many events we want to list.
        :return List[Event]: A list containing the Events, ordered from the closest to the most distant (in time).
        """
        future_events = self.get_future_events()
        future_events.sort(key=lambda x: x.date_start, reverse=False)
        return future_events[:num]

    def get_unique_event_by_id(self, identifier: int) -> Event:
        return Event(self._collection.find_one({'fields.id': str(identifier)})['fields'])

    def create_filter_from_args(self, args: dict) -> Filter:
        """
        Takes the arguments of a Flask request, and returns a corresponding Filter.
        """
        keys = args.keys()
        filter_args = {}

        if 'search' in keys:
            filter_args.update({"text_filter": args.get('search')})
        if 'category' in keys:
            if not args.get('category') == "":
                filter_args.update({"category": args.get('category')})
        if 'price_type' in keys:
            filter_args.update({"price_type": False if args.get('price_type') == '1' else True})
        if 'future' in keys:
            pass

        if 'pmr' in keys:
            filter_args.update({"pmr": 1})
        if 'blind' in keys:
            filter_args.update({"blind": 1})
        if 'deaf' in keys:
            filter_args.update({"deaf": 1})

        f = Filter(**filter_args)
        return f

    def search(self, f: Filter, limit: int = 0) -> List[Event]:
        """
        Searches the database using a filter.

        :param Filter f: The Filter instance to use.
        :param int limit: The maximum number of items we want to return.
        :return list: List of events if some were found, empty otherwise.
        """
        query = f.forge_query()
        returned_events = self._collection.find(query).limit(limit)
        return [Event(info['fields']) for info in returned_events]

    def get_occurrences(self, identifier: str) -> Set[int]:
        timestamps = self.cache.get_timestamps(identifier)
        return set(timestamps['occurrences'])


class Cache:

    cache_folder: str = '.cache/qfap/'

    def __init__(self, db, collection):
        self.create_cache_dir()
        self._empty_cache()

        self._db = db
        self._collection = collection

        self.categories_db = self._get_db('cats')

    def create_cache_dir(self) -> None:
        """
        Creates the cache directory.
        """
        try:
            os.makedirs(self.cache_folder)
        except FileExistsError:
            pass

    def _empty_cache(self) -> None:
        # Removes all the files contained in the cache folder
        for fl in os.listdir(self.cache_folder):
            os.remove(os.path.join(self.cache_folder, fl))

    def _get_db(self, db_name: str) -> shelve.DbfilenameShelf:
        """
        Gets the database specified.
        Creates it if not present.
        Needs for the directory to exist.

        :param str db_name: The database name (the file name).
        :return shelve.DbfilenameShelf:
        """
        db_path = os.path.join(self.cache_folder, db_name)
        db = shelve.open(db_path)
        logging.info(f'Opened cache file {db_path!r}')
        return db

    ######################
    # CATEGORIES SECTION #
    ######################

    def store_category(self, info) -> None:
        """
        Checks if the category of the event is already known, if it is not, store it.
        """
        # *Technically* it would be smarter to create an event with each info,
        # but it's not the most optimized way of doing it.
        # Here, we will assume `category` is never missing.
        # If by any mean it is missing, it will raise a KeyError.
        category = info['fields']['category']
        main_category, sub_category = category.split('>')
        main_category = main_category.strip('-').strip(' ')
        sub_category = sub_category.strip(' ')

        if main_category in self.categories_db.keys():
            if sub_category not in self.categories_db[main_category]:
                sub_categories = self.categories_db[main_category]
                sub_categories.append(sub_category)
                self.categories_db[main_category] = sub_categories
            else:
                return
        else:
            self.categories_db[main_category] = [sub_category]

        self.categories_db.sync()

    def get_all_categories(self) -> dict:
        """
        Gathers all the categories from the database.

        :return dict: A dictionary containing for each key a main category, and as the value a list of sub-categories.
        """
        return {k: v for k, v in self.categories_db.items()}
