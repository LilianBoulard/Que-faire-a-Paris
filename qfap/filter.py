import logging

from .utils import decode_json

from typing import List


class Filter:

    """

    This class implements a `Filter` object.
    It will be used to forge advanced queries.

    """

    def __init__(self, global_operator: bool = True, text_filter: str = None, price_type: bool = None,
                 category: str = None, tags: list = None, tags_operator: bool = None,
                 pmr: int = None, deaf: int = None, blind: int = None):
        """
        :param bool global_operator: Operator to use on all queries. True for "and", False for "or".
        :param str text_filter: Filter used on the description and the title.
        :param bool price_type: Price type as a boolean: False for "gratuit", True for "payant".
        :param str category: The category it classifies in. e.g: "Concerts -> Folk"
        :param list tags: A list of tags.
        :param bool tags_operator: Operator to use on the tags, True for "and", False for "or".
        :param int pmr: Whether the event is suited for people with reduced mobility. 1 for yes, 0 for no.
        :param int deaf: Same as above, for deaf people.
        :param int blind: Same as above, for blind people.
        """

        self._global_operator = global_operator
        self._text_filter = text_filter
        self._price_type = price_type
        self._category = category
        self._tags = tags
        self._tags_operator = tags_operator
        self._pmr = pmr
        self._deaf = deaf
        self._blind = blind

    def text_filter(self) -> str:
        field1 = 'title'
        field2 = 'description'
        value = self._text_filter
        query = '{"$or": '
        query += '['
        query += '{'
        query += f'"fields.{field1}": ' + '{"$regex": ' + f'"{value}"' + '}'
        query += '}, {'
        query += f'"fields.{field2}": ' + '{"$regex": ' + f'"{value}"' + '}'
        query += '}'
        query += ']'
        query += '}'
        return query

    def price_type(self) -> str:
        field = 'price_type'
        value = "payant" if self._price_type else "gratuit"
        query = '{'
        query += f'"fields.{field}": "{value}"'
        query += '}'
        return query

    def category(self) -> str:
        field = 'category'
        value = self._category
        query = '{'
        query += f'"fields.{field}": "{value}"'
        query += '}'
        return query

    def tags(self) -> str:
        field = 'tags'
        query = '{'
        if len(self._tags) > 1:
            operator = '$and' if self._tags_operator else '$or'
            query += f'{operator}: '
            query += '['
            for tag in self._tags:
                query += '{'
                query += f'"fields.{field}": ' + '{"$regex": ' + f'".*{tag}.*' + '"}'
                query += '},'
            else:
                query = query[:-1]
            query += ']'
        elif len(self._tags) == 1:
            tag = self._tags[0]
            query += f'"fields.{field}": ' + '{"$regex": ' + f'".*{tag}.*' + '"}'
        query += '}'
        return query

    def pmr(self):
        field = 'pmr'
        value = self._pmr
        query = '{'
        query += f'"fields.{field}": {value}'
        query += '}'
        return query

    def deaf(self):
        field = 'deaf'
        value = self._deaf
        query = '{'
        query += f'"fields.{field}": {value}'
        query += '}'
        return query

    def blind(self):
        field = 'blind'
        value = self._blind
        query = '{'
        query += f'"fields.{field}": {value}'
        query += '}'
        return query

    def aggregate_all_queries(self, queries: List[str]) -> str or None:
        if len(queries) > 1:
            operator = "$and" if self._global_operator else "$or"
            query = '{'
            query += f'"{operator}": ['
            for q in queries:
                query += f'{q},'
            else:
                query = query[:-1]
            query += ']}'
        elif len(queries) == 1:
            query = queries[0]
        else:
            query = None
        return query

    def forge_query(self) -> dict:
        queries = []

        if self._text_filter is not None:  # We explicit "is not None" because some values are boolean.
            queries.append(self.text_filter())

        if self._price_type is not None:
            queries.append(self.price_type())

        if self._category is not None:
            queries.append(self.category())

        if self._tags is not None:
            queries.append(self.tags())

        if self._pmr is not None:
            queries.append(self.pmr())

        if self._deaf is not None:
            queries.append(self.deaf())

        if self._blind is not None:
            queries.append(self.blind())

        query = self.aggregate_all_queries(queries)
        if query is not None:
            logging.debug(f'{query=}')
            return decode_json(query)
        else:
            return {}
