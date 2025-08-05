from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (
    DistanceMetricEnums,
    PgVectorDistanceEnums,
    PgVectorIndexTypeEnums,
    PgVectorTTableSchemeEnums,
)
import logging
from typing import List
from models.db_schemes import RetrievedDocument
from sqlalchemy.sql import text as sql_text
import json


class PGVectorProvider(VectorDBInterface):

    def __init__(
        self,
        db_client,
        distance_method: str,
        default_vector_size: int = 384,
    ):
        self.db_client = db_client
        self.distance_method = distance_method
        self.default_vector_size = default_vector_size
        self.pgvector_table_prefix = PgVectorTTableSchemeEnums._PREFIX.value

        self.logger = logging.getLogger("uvicorn")

        if distance_method == DistanceMetricEnums.COSINE.value:
            self.distance_method = PgVectorDistanceEnums.COSINE.value
        elif distance_method == DistanceMetricEnums.DOT.value:
            self.distance_method = PgVectorDistanceEnums.DOT.value
        elif distance_method == DistanceMetricEnums.EUCLIDEAN.value:
            self.distance_method = PgVectorDistanceEnums.COSINE.value

    async def connect(self):
        """Connect to the PostgreSQL database."""
        async with self.db_client as session:
            async with session.begin():
                await session.execute(
                    sql_text("CREATE EXTENSION IF NOT EXISTS vector;")
                )

        await session.commit()

    def disconnect(self):
        pass

    async def is_collection_exist(self, collection_name: str) -> bool:
        """Check if a collection exists in the PostgreSQL database."""
        record = None
        async with self.db_client as session:
            async with session.begin():
                list_tbl = sql_text(
                    """
                    SELECT * FROM pg_tables WHERE table_name = :collection_name;
                    """
                )
                result = await session.execute(
                    list_tbl, {"collection_name": {collection_name}}
                )  # it was done this way to avoid SQL injection
                record = result.scalar_one_or_none()
                return record

    async def list_all_collections(self) -> List[str]:
        records = []
        """List all collections in the PostgreSQL database."""
        async with self.db_client as session:
            async with session.begin():
                list_tbl = sql_text(
                    """
                    SELECT table_name FROM pg_tables WHERE table_name LIKE :prefix;
                    """
                )
                result = await session.execute(
                    list_tbl, {"prefix": {self.pgvector_table_prefix}}
                )
                records = result.scalars().all()
        return records

    async def get_collection_info(self, collection_name: str) -> dict:
        """Get information about a specific collection."""
        record = None
        async with self.db_client as session:
            async with session.begin():
                table_info_sql = sql_text(
                    """
                    SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                    FROM pg_tables
                    WHERE table_name = :collection_name;
                    """
                )
                count_sql = sql_text(
                    """
                    SELECT COUNT(*) FROM :collection_name;
                    """
                )
                table_info = await session.execute(
                    table_info_sql, {"collection_name": {collection_name}}
                )
                record_count = await session.execute(
                    count_sql, {"collection_name": {collection_name}}
                )
                table_data = table_info.fetchone()
                if not table_data:
                    return None
                return {
                    "table_info": dict(table_data),
                    "record_count": record_count,
                }

    async def delete_collection(self, collection_name: str) -> bool:
        async with self.db_client as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")
                delete_table_sql = sql_text(
                    """
                    DROP TABLE IF EXISTS :collection_name;
                    """
                )
                await session.execute(
                    delete_table_sql, {"collection_name": collection_name}
                )
                await session.commit()
        return True

    async def create_collection(
        self, collection_name: str, embedding_dimension: int, do_reset: bool
    ) -> bool:
        if do_reset:
            _ = await self.delete_collection(collection_name)
        is_collection_exist = await self.is_collection_exist(collection_name)
        if not is_collection_exist:
            async with self.db_client as session:
                async with session.begin():
                    create_table_sql = sql_text(
                        f"""
                        CREATE TABLE {collection_name} (
                            {PgVectorTTableSchemeEnums.ID.value}  BIGSERIAL PRIMARY KEY,
                            {PgVectorTTableSchemeEnums.TEXT.value} TEXT,
                            {PgVectorTTableSchemeEnums.VECTOR.value} VECTOR({embedding_dimension}),
                            {PgVectorTTableSchemeEnums.METADATA.value} JSONB DEFAULT \'{{}}\',
                            {PgVectorTTableSchemeEnums.CHUNK_ID.value} Integer,
                            FOREIGN KEY ({PgVectorTTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(id)
                        );
                        """
                    )
                    await session.execute(create_table_sql)
                    await session.commit()
            return True
        return False

    async def insert_one(
        self, collection_name, text, vector, metadata=None, record_id=None
    ):
        is_exist = await self.is_collection_exist(collection_name)
        if not is_exist:
            self.logger.error(
                f" can't insert into Collection {collection_name} that does not exist."
            )
            return False
        if not record_id:
            self.logger.error(f"can't insert without record_id :{collection_name}.")
            return False
        async with self.db_client as session:
            async with session.begin():
                insert_sql = sql_text(
                    f"""
                    INSERT INTO {collection_name} (
                        {PgVectorTTableSchemeEnums.TEXT.value},
                        {PgVectorTTableSchemeEnums.VECTOR.value},
                        {PgVectorTTableSchemeEnums.METADATA.value},
                        {PgVectorTTableSchemeEnums.CHUNK_ID.value}
                    ) VALUES (
                        :text,
                        :vector,
                        :metadata,
                        :chunk_id
                    );
                    """
                )
                await session.execute(
                    insert_sql,
                    {
                        "record_id": record_id,
                        "text": text,
                        "vector": "[" + ",".join(map(str, vector)) + "]",
                        "metadata": metadata,
                        "chunk_id": record_id,
                    },
                )
                await session.commit()
        return True

    async def insert_many(
        self,
        collection_name,
        texts,
        vectors,
        metadata=None,
        record_ids=None,
        batch_size=50,
    ):
        is_exist = await self.is_collection_exist(collection_name)
        if not is_exist:
            self.logger.error(
                f" can't insert into Collection {collection_name} that does not exist."
            )
            return False
        if len(vectors) != len(record_ids):
            self.logger.error(
                f"Vectors and record_ids must have the same length for collection {collection_name}."
            )
            return False
        if not metadata or len(metadata) == 0:
            metadata = [None] * len(texts)

        async with self.db_client as session:
            async with session.begin():
                insert_sql = sql_text(
                    f"""
                    INSERT INTO {collection_name} 
                        {PgVectorTTableSchemeEnums.TEXT.value},
                        {PgVectorTTableSchemeEnums.VECTOR.value},
                        {PgVectorTTableSchemeEnums.METADATA.value},
                        {PgVectorTTableSchemeEnums.CHUNK_ID.value}
                    VALUES (
                        :text,
                        :vector,
                        :metadata,
                        :chunk_id
                    );
                    """
                )
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i : i + batch_size]
                    batch_vectors = vectors[i : i + batch_size]
                    batch_metadata = metadata[i : i + batch_size] if metadata else None
                    batch_record_ids = record_ids[i : i + batch_size]

                    await session.execute(
                        insert_sql,
                        [
                            {
                                "text": text,
                                "vector": "[" + ",".join(map(str, vector)) + "]",
                                "metadata": meta,
                                "chunk_id": record_id,
                            }
                            for text, vector, meta, record_id in zip(
                                batch_texts,
                                batch_vectors,
                                batch_metadata,
                                batch_record_ids,
                            )
                        ],
                    )
                await session.commit()
        return True

    async def search_by_vector(self, collection_name, vector, limit):
        is_exist = await self.is_collection_exist(collection_name)
        if not is_exist:
            self.logger.error(
                f" can't search in Collection {collection_name} that does not exist."
            )
            return []
        vector_str = "[" + ",".join(map(str, vector)) + "]"
        async with self.db_client as session:
            async with session.begin():
                search_sql = sql_text(
                    f"""
                    SELECT {PgVectorDistanceEnums.TEXT.value} as text , 1 - ({PgVectorTTableSchemeEnums.VECTOR.value} <-> :vector) as score
                    FROM {collection_name}
                    ORDER BY  score DESC
                    LIMIT {limit};
                    """
                )
                result = await session.execute(search_sql, {"vector": vector_str})
                records = result.fetchall()
                return [
                    RetrievedDocument(
                        text=record.text,
                        score=record.score,
                    )
                    for record in records
                ]
