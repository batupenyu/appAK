import os
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from vercel.blob import BlobClient


@deconstructible
class VercelBlobStorage(Storage):
    def __init__(self):
        self.client = BlobClient()
        self.store_id = os.environ.get("BLOB_STORE_ID", "")

    def _save(self, name, content):
        content.seek(0)
        self.client.put(name, content.read(), access="private", overwrite=True)
        return name

    def url(self, name):
        return f"https://{self.store_id}.private.blob.vercel-storage.com/{name}"

    def exists(self, name):
        from vercel.blob.errors import BlobNotFoundError
        try:
            self.client.head(name)
            return True
        except BlobNotFoundError:
            return False

    def delete(self, name):
        self.client.delete(name)

    def _open(self, name, mode="rb"):
        from django.core.files.base import ContentFile
        result = self.client.get(name, access="private")
        data = b"".join(result.stream) if result else b""
        return ContentFile(data, name=name)

    def size(self, name):
        result = self.client.head(name)
        return result.size
