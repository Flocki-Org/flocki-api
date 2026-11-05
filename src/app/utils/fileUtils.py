import os
from mimetypes import guess_extension

from starlette.datastructures import Headers

class FileUtils:
    @staticmethod
    def use_jpg_content_type(file):
        # UploadFile.content_type is read-only. Replacing the header keeps the
        # previous assignment of image/jpg, which is what gets stored and used
        # when guessing the file extension.
        if file.content_type == 'image/jpeg':
            headers = dict(file.headers.items())
            headers['content-type'] = 'image/jpg'
            file.headers = Headers(headers)

    @staticmethod
    def get_file_extension(file):
        extension = guess_extension(file.content_type)
        if extension is None:
            # get file extension from filename
            extension = os.path.splitext(file.filename)[1]
            if extension is None:
                raise Exception("no file extension found")
        #remove leading dot if starts with dot
        if extension.startswith('.'):
            extension = extension[1:]
        return extension
