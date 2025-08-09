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
        index_threshold: int = 100,
    ):
        self.db_client = db_client
        self.distance_method = distance_method
        self.default_vector_size = default_vector_size
        self.pgvector_table_prefix = PgVectorTTableSchemeEnums._PREFIX.value
        self.default_index_name = lambda collection_name: f"{collection_name}_index"
        self.index_threshold = index_threshold

        if distance_method == DistanceMetricEnums.COSINE.value:
            distance_method = PgVectorDistanceEnums.COSINE.value
        elif distance_method == DistanceMetricEnums.DOT.value:
            distance_method = PgVectorDistanceEnums.DOT.value
        self.distance_method = distance_method
        self.logger = logging.getLogger("uvicorn")

    async def connect(self):
        """Connect to the PostgreSQL database."""
        async with self.db_client() as session:
            async with session.begin():
                try:
                    await session.execute(sql_text("CREATE EXTENSION vector;"))
                    await session.commit()
                except Exception as e:
                    # Only ignore the error if it's about the extension already existing
                    if "pg_extension_name_index" in str(e) or "already exists" in str(
                        e
                    ):
                        self.logger.warning(
                            "Vector extension already exists, skipping creation."
                        )
                    else:
                        self.logger.error(f"Error ensuring vector extension: {e}")
                        raise

    def disconnect(self):
        pass

    async def is_collection_exist(self, collection_name: str) -> bool:
        """Check if a collection exists in the PostgreSQL database."""
        record = None
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text(
                    f"""
                    SELECT * FROM pg_tables WHERE tablename = :collection_name;
                    """
                )
                result = await session.execute(
                    list_tbl, {"collection_name": collection_name}
                )  # it was done this way to avoid SQL injection
                record = result.scalar_one_or_none()
                return record

    async def list_all_collections(self) -> List[str]:
        records = []
        """List all collections in the PostgreSQL database."""
        async with self.db_client() as session:
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
        async with self.db_client() as session:
            async with session.begin():
                table_info_sql = sql_text(
                    f"""
                    SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                    FROM pg_tables
                    WHERE tablename = :collection_name;
                    """
                )
                count_sql = sql_text(
                    f"""
                    SELECT COUNT(*) FROM {collection_name};
                    """
                )
                table_info = await session.execute(
                    table_info_sql, {"collection_name": collection_name}
                )
                record_count = await session.execute(count_sql)
                table_data = table_info.fetchone()
                if not table_data:
                    return None
                return {
                    "table_info": {
                        "schema_name": table_data[0],
                        "table_name": table_data[1],
                        "table_owner": table_data[2],
                        "tablespace": table_data[3],
                        "has_indexes": table_data[4],
                    },
                    "record_count": record_count.scalar_one(),
                }

    async def delete_collection(self, collection_name: str) -> bool:
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")
                delete_table_sql = sql_text(
                    f"""
                    DROP TABLE IF EXISTS {collection_name};
                    """
                )
                await session.execute(delete_table_sql)
                await session.commit()
        return True

    async def create_collection(
        self, collection_name: str, embedding_dimension: int, do_reset: bool
    ) -> bool:
        if do_reset:
            _ = await self.delete_collection(collection_name)
        is_collection_exist = await self.is_collection_exist(collection_name)
        if not is_collection_exist:
            async with self.db_client() as session:
                async with session.begin():
                    create_table_sql = sql_text(
                        f"""
                        CREATE TABLE {collection_name} (
                            {PgVectorTTableSchemeEnums.ID.value}  BIGSERIAL PRIMARY KEY,
                            {PgVectorTTableSchemeEnums.TEXT.value} TEXT,
                            {PgVectorTTableSchemeEnums.VECTOR.value} VECTOR({embedding_dimension}),
                            {PgVectorTTableSchemeEnums.METADATA.value} JSONB DEFAULT \'{{}}\',
                            {PgVectorTTableSchemeEnums.CHUNK_ID.value} Integer,
                            FOREIGN KEY ({PgVectorTTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)
                        );
                        """
                    )
                    await session.execute(create_table_sql)
                    await session.commit()
            return True
        return False

    async def is_index_exist(self, collection_name: str) -> bool:
        index_name = self.default_index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                index_sql = sql_text(
                    f"""
                    SELECT 1 FROM pg_indexes WHERE tablename = :collection_name
                    AND indexname = :index_name;
                    """
                )
                result = await session.execute(
                    index_sql,
                    {"collection_name": collection_name, "index_name": index_name},
                )
                return result.scalar_one_or_none() is not None

    async def create_vector_index(
        self, collection_name: str, index_type: str = PgVectorIndexTypeEnums.HNSW.value
    ) -> bool:
        if await self.is_index_exist(collection_name):
            return False

        async with self.db_client() as session:
            async with session.begin():
                count_sql = sql_text(
                    f"""
                    SELECT COUNT(*) FROM {collection_name};
                    """
                )
                result = await session.execute(count_sql)
                record_count = result.scalar_one()
                if record_count < self.index_threshold:

                    return False
                self.logger.info(
                    f"START:Creating index for collection {collection_name} with type {index_type}."
                )
                index_name = self.default_index_name(collection_name)
                create_index_sql = sql_text(
                    f"""
                    CREATE INDEX {index_name} ON {collection_name} USING {index_type} (
                    {PgVectorTTableSchemeEnums.VECTOR.value} {self.distance_method}
                    );
                    """
                )
                await session.execute(create_index_sql)
                await session.commit()
                self.logger.info(
                    f"END:Created index for collection {collection_name} with type {index_type}."
                )
        return True

    async def reset_vector_index(
        self, collection_name: str, index_type: str = PgVectorIndexTypeEnums.HNSW.value
    ) -> bool:
        if await self.is_index_exist(collection_name):
            self.logger.info(f"Resetting index for collection {collection_name}.")
            index_name = self.default_index_name(collection_name)
            async with self.db_client() as session:
                async with session.begin():
                    drop_index_sql = sql_text(
                        f"""
                        DROP INDEX IF EXISTS {index_name};
                        """
                    )
                    await session.execute(drop_index_sql)
                    await session.commit()
        return await self.create_vector_index(collection_name, index_type)

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
        async with self.db_client() as session:
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
                        "metadata": (
                            json.dumps(metadata, ensure_ascii=False)
                            if metadata
                            else "{}"
                        ),
                        "chunk_id": record_id,
                    },
                )
                await session.commit()
        await self.create_vector_index(
            collection_name=collection_name,
            index_type=PgVectorIndexTypeEnums.HNSW.value,
        )
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

        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(
                    f"""
                    INSERT INTO {collection_name}( 
                        {PgVectorTTableSchemeEnums.TEXT.value},
                        {PgVectorTTableSchemeEnums.VECTOR.value},
                        {PgVectorTTableSchemeEnums.METADATA.value},
                        {PgVectorTTableSchemeEnums.CHUNK_ID.value}
                        )
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
                                "metadata": (
                                    json.dumps(meta, ensure_ascii=False)
                                    if meta
                                    else "{}"
                                ),
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
        await self.create_vector_index(
            collection_name=collection_name,
            index_type=PgVectorIndexTypeEnums.HNSW.value,
        )
        return True

    async def search_by_vector(self, collection_name, vector, limit):
        is_exist = await self.is_collection_exist(collection_name)
        if not is_exist:
            self.logger.error(
                f" can't search in Collection {collection_name} that does not exist."
            )
            return []
        vector_str = "[" + ",".join(map(str, vector)) + "]"
        async with self.db_client() as session:
            async with session.begin():
                search_sql = sql_text(
                    f"""
                    SELECT {PgVectorTTableSchemeEnums.TEXT.value} as text , 1 - ({PgVectorTTableSchemeEnums.VECTOR.value} <-> :vector) as score
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
