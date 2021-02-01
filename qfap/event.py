import logging

from typing import Set


# Every event should have this structure.
event_structure = {
    'id': str,
    'title': str,
    'lead_text': str,  # Some kind of summary / interesting and quick information on the event.
    'description': str,
    'tags': list,
    'date_start': str,
    'date_end': str,
    'updated_at': str,
    'date_description': str,  # Date as a sentence (with HTML). e.g: "Le mardi 2 février 2021<br />de 20h à 22h<br />"
    'category': str,
    'occurrences': str,
    'programs': str,  # External description and link to the program
    'contact_name': str,
    'price_detail': str,
    'price_type': str,
    'address_name': str,
    'address_street': str,
    'address_city': str,
    'address_zipcode': str,
    'lat_lon': list,
    'access_type': str,
    'access_phone': str,
    'access_mail': str,
    'access_link': str,
    'contact_url': str,
    'contact_phone': str,
    'contact_mail': str,
    'contact_facebook': str,
    'contact_twitter': str,
    'cover_url': str,
    'cover': {
        'id': str,
        'mimetype': str,
        'format': str,
        'color_summary': list,
        'filename': str,
        'width': int,
        'height': int,
        'thumbnail': bool
    },
    'cover_alt': str,  # Alt description for the image
    'cover_credit': str,  # Source credit
    'url': str,
    'transport': str,
    'pmr': int,  # Accessibility for people with reduced mobility
    'deaf': int,  # Accessibility for deaf people
    'blind': int,  # Accessibility for blind people
}


def validate_fields(dictionary: dict, struct: dict):
    """
    Takes a dictionary and an architecture and checks if the types and structure are valid.
    Corrects the dictionary if necessary. The output dict is valid.
    Recursive only in dictionaries. All other types are not iterated through (e.g. lists).

    Example arch: {"content": str, "meta": {"time_sent": int, "digest": str, "aes": str}}

    :param dict dictionary: A dictionary to check.
    :param dict struct: Dictionary containing the levels of architecture.
    """

    def is_int(value) -> bool:
        """
        Tests a value to check if it is an integer or not.
        """
        try:
            int(value)
        except ValueError:
            return False
        else:
            return True

    if not isinstance(dictionary, dict):
        logging.error(f"Argument 'dictionary' needs to be a dict, is {type(dictionary)}: {dictionary}")
        return dictionary
    if not isinstance(struct, dict):
        logging.error(f"Argument 'struct' needs to be a dict, is {type(struct)}: {struct}")
        return dictionary

    for key, struct_value in struct.items():
        if key not in dictionary:
            if isinstance(struct_value, dict):
                dictionary[key] = struct_value
            else:
                # `struct_value` is a `type` object
                # We therefore create a new instance
                dictionary[key] = struct_value()
            continue
        else:
            dict_value = dictionary[key]

        if isinstance(struct_value, type):
            # If value is a type object, we want to check that the value from the dict is of this type.
            if struct_value is int:
                if not is_int(dict_value):
                    logging.warning(f"Couldn't cast to int {key!r}: {dict_value!r}")
                    dictionary[key] = 0
        elif isinstance(struct_value, dict):
            # If value is a dict, we want to call this function recursively.
            dictionary[key] = validate_fields(dict_value, struct_value)

    if len(dictionary) != len(struct):
        difference = set(dictionary.keys()).symmetric_difference(set(struct.keys()))
        logging.warning(f'Leftover fields in the dictionary: {difference}')
        for dif in difference:
            print(f"{dif}={dictionary[dif]}")

    return dictionary


def validate_info(func):
    """
    Decorator used to validate the event information passed is valid.
    That way, we can be assured all events have exactly the same information.
    """
    def wrapper(*args, **kwargs):
        if len(args) > 0:
            dictionary = args[0]
        elif len(kwargs) > 0:
            dictionary = kwargs['info']
        else:
            raise ValueError(f"Missing required argument 'info'. ({args}, {kwargs})")
        return func(validate_fields(dictionary, event_structure))
    return wrapper


@validate_info
class Event:

    def __init__(self, info: dict):
        self.set_attributes(info)

    def set_attributes(self, attr: dict):
        for key, value in attr.items():
            self.__setattr__(key, value)

    def get_occurrences(self) -> set:
        return set(self.occurrences.split('_'))

    def get_tags(self) -> Set[str]:
        return set(self.tags.split(';'))

    def get_lead_text_snippet(self, limit: int = 95) -> str:
        if len(self.lead_text) > limit:
            snippet = self.lead_text[:limit - 3].strip() + '...'
        else:
            snippet = self.lead_text
        return snippet

