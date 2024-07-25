import hashlib


def create_hash(password):
    hash_md5 = hashlib.new("md5")
    hash_md5.update(password.encode())
    return hash_md5.hexdigest()


PASSWORD = create_hash("your password here")
