from fastapi import FastAPI, APIRouter, Depends
from helpers.config import get_settings, Settings
import os
from datetime import datetime


base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)


@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    return {
        "app_name": app_name,
        "app_version": app_version,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
