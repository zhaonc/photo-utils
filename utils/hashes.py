import hashlib


def chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk

def get_hash(file, first_chunk_only=False, hash_algo=hashlib.sha1):
    # https://github.com/TheLastGimbus/GooglePhotosTakeoutHelper/blob/155b0cfe3dc9f7b4d06081d7d4d6c9ec635096ef/google_photos_takeout_helper/__main__.py#L208
    hashobj = hash_algo()
    with open(file, 'rb') as f:
        if first_chunk_only:
            hashobj.update(f.read(1024))
        else:
            for chunk in chunk_reader(f):
                hashobj.update(chunk)
    return hashobj.digest()