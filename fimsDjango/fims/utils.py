from hashids import Hashids
from django.conf import settings

# Initialize Hashids with the project's salt
hashids = Hashids(salt=settings.HASHIDS_SALT, min_length=8)

def encode_id(pk):
    """Encodes an integer primary key into a hashid."""
    return hashids.encode(pk)

def decode_id(hashid):
    """
    Decodes a hashid string back to an integer primary key.
    Returns None if decoding fails.
    """
    decoded = hashids.decode(hashid)
    if decoded:
        return decoded[0]
    return None