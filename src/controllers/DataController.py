from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseResult

class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 104_857_6 # convert MB to bytes 

    def validate_uploaded_file(self,file: UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseResult.FILE_TYPE_NOT_SUPPORTED.value
        
        if file.size > self.app_settings.FILE_MAX_SIZE *self.size_scale:
            return False,ResponseResult.FILE_SIZE_EXCEEDED.value
        
        return True,ResponseResult.FILE_VALIDATED_SUCCESS.value