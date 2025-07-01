from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseResult

class ProjectController(BaseController):
    def __init__(self):
        super().__init__()
    