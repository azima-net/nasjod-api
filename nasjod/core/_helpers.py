import os
from uuid import uuid4


def image_path_upload(instance, filename):
    """Generate file path for a new file"""
    model_name = instance.__class__.__name__.lower()
    ext = filename.split(".")[-1]
    new_filename = f"{uuid4()}.{ext}"
    return os.path.join(f"upload/{model_name}", new_filename)
