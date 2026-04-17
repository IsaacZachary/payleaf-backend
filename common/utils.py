import json

def canonical_json(data):
    """
    Returns a canonical JSON string for hashing.
    Keys are sorted, and whitespace is minimized.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'))
