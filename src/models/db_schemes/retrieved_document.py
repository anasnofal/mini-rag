from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId


class RetrievedDocument(BaseModel):
    text: str
    score: float
