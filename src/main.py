from fastapi import FastAPI
from requests import session
from routes import base, data, nlp
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBproviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

app = FastAPI()


async def startup_span():
    settings = get_settings()
    postgres_conn = (
        "postgresql+asyncpg://{username}:{password}@{host}:{port}/{db}".format(
            username=settings.POSTGRES_USERNAME,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            db=settings.POSTGRES_MAIN_DB,
        )
    )
    app.db_engine = create_async_engine(postgres_conn)
    app.db_client = sessionmaker(
        app.db_engine, class_=AsyncSession, expire_on_commit=False
    )
    llm_provider_factory = LLMProviderFactory(settings)
    vector_db_provider_factory = VectorDBProviderFactory(
        settings, db_client=app.db_client
    )

    app.generation_client = llm_provider_factory.create(settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    app.embedding_client = llm_provider_factory.create(settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(
        settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE
    )
    app.vector_db_client = vector_db_provider_factory.create(settings.VECTOR_DB_BACKEND)
    await app.vector_db_client.connect()
    app.template_parser = TemplateParser(
        language=settings.PRIMARY_LANGUAGE, default_language=settings.DEFAULT_LANGUAGE
    )


async def shutdown_span():
    app.db_engine.dispose()
    app.vector_db_client.disconnect()


app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
