from curses import meta
from os import path
from unittest import result
from stores.vectordb.VectorDBEnums import DistanceMetricEnums
from ..VectorDBInterface import VectorDBInterface
from qdrant_client import QdrantClient, models
from typing import List
import uuid
from models.db_schemes import RetrievedDocument
import logging


class QdrantDbProvider(VectorDBInterface):
    def __init__(self, db_path: str, distance_method: str):
        self.db_path = db_path
        self.distance_method = None
        self.client = None

        if distance_method == DistanceMetricEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMetricEnums.DOT.value:
            self.distance_method = models.Distance.DOT
        elif distance_method == DistanceMetricEnums.EUCLIDEAN.value:
            self.distance_method = models.Distance.EUCLIDEAN

        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Connect to the Qdrant database."""
        self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        """Close the connection to the Qdrant database."""
        self.client = None

    def is_collection_exist(self, collection_name: str) -> bool:
        """Check if a collection exists in the Qdrant database."""
        return self.client.collection_exists(collection_name=collection_name)

    def list_all_collections(self) -> list:
        """List all collections in the Qdrant database."""
        return self.client.get_collections()

    def get_collection_info(self, collection_name: str) -> dict:
        """Get information about a specific collection."""
        return self.client.get_collection(collection_name=collection_name)

    def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ) -> bool:
        """Create a new collection in the Qdrant database."""
        if do_reset:
            _ = self.delete_collection(collection_name)

        if not self.is_collection_exist(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=self.distance_method
                ),
            )
            return True
        return False

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the Qdrant database."""
        if self.is_collection_exist(collection_name):
            return self.client.delete_collection(collection_name=collection_name)
        return False

    def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: list,
        metadata: dict = None,
        record_id: str = None,
    ) -> bool:
        """Insert a single document into a collection."""
        if not self.is_collection_exist(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False
        if not vector or len(vector) == 0:
            self.logger.error("Vector is empty or not provided.")
            return False
        if record_id is None:
            record_id = str(uuid.uuid4())
        try:
            _ = self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=record_id,
                        vector=vector,
                        payload={
                            "text": text,
                            "metadata": metadata if metadata else {"text": text},
                        },
                    )
                ],
            )
        except Exception as e:
            self.logger.error(
                f"Error inserting document into collection {collection_name}: {e}"
            )
            return False
        return True

    def insert_many(
        self,
        collection_name: str,
        texts: list[str],
        vectors: list[list],
        metadata: list[dict] = None,
        record_ids: list[str] = None,
        batch_size: int = 50,
    ) -> bool:
        """Insert multiple documents into a collection."""
        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            record_ids = list(range(len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.PointStruct(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x],
                        "metadata": (
                            batch_metadata[x]
                            if batch_metadata[x]
                            else {"text": batch_texts[x]}
                        ),
                    },
                )
                for x in range(len(batch_texts))
            ]
            try:
                result = self.client.upsert(
                    collection_name=collection_name,
                    points=batch_records,
                )
            except Exception as e:
                self.logger.error(
                    f"Error inserting batch into collection {collection_name}: {e}"
                )
                return False
        return True

    def search_by_vector(self, collection_name: str, vector: list, limit: int):
        """Search for documents in a collection based on a query vector."""
        result = self.client.query_points(
            collection_name=collection_name, query=vector, limit=limit
        )
        if not result.points or len(result.points) == 0:
            self.logger.warning(
                f"No results found for query in collection {collection_name}"
            )
            return None
        return [
            RetrievedDocument(
                **{
                    "score": doc.score,
                    "text": doc.payload["text"],
                }
            )
            for doc in result.points
        ]
