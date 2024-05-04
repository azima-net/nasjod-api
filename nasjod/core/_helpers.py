import os
from uuid import uuid4


def user_photo_file_path(instance, filename):
    """Generate file path for a new user photo"""
    ext = filename.split(".")[-1]
    filename = f"{uuid4()}.{ext}"

    return os.path.join("upload/user/", filename)
