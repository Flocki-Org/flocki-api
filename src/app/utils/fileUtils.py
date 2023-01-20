import os
from mimetypes import guess_extension

class FileUtils:
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
