import json


def encode_json(dictionary: dict) -> str:
    """
    Takes a dictionary and returns a JSON-encoded string.

    :param dict dictionary: A dictionary.
    :return str: A JSON-encoded string.
    """
    return json.JSONEncoder().encode(dictionary)


def decode_json(json_string: str) -> dict:
    """
    Takes a message as a JSON string and unpacks it to get a dictionary.

    :param str json_string: A message, as a JSON string.
    :return dict: An unverified dictionary. Do not trust this data.
    """
    return json.JSONDecoder().decode(json_string)
