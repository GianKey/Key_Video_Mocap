from chunked_upload.models import ChunkedUpload,settings
from chunked_upload.settings import UPLOAD_PATH,STORAGE
import os.path
import time
from django.db import models
# Create your models here.


class MyChunkedUpload(ChunkedUpload):
    chunkedupload_ptr = models.OneToOneField(
        ChunkedUpload, parent_link=True,
        on_delete=models.CASCADE,
        primary_key=True,
    )
# Override the default ChunkedUpload to make the `user` field nullable
MyChunkedUpload._meta.get_field('user').null = True

