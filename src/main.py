from fastapi import FastAPI
from routes import base, data, nlp
from pymongo import AsyncMongoClient as Client
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBproviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser

app = FastAPI()


async def startup_span():
    settings = get_settings()
    app.mongo_conn = Client(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]
    llm_provider_factory = LLMProviderFactory(settings)
    vector_db_provider_factory = VectorDBProviderFactory(settings)

    app.generation_client = llm_provider_factory.create(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    app.embedding_client = llm_provider_factory.create(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(
        settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE
    )
    app.vector_db_client = vector_db_provider_factory.create(settings.VECTOR_DB_BACKEND)
    app.vector_db_client.connect()
    app.template_parser = TemplateParser(
        language=settings.PRIMARY_LANGUAGE, default_language=settings.DEFAULT_LANGUAGE
    )


async def shutdown_span():
    await app.mongo_conn.close()
    app.vector_db_client.disconnect()


app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
