from importlib import metadata
import re
from models.db_schemes.data_chunk import DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from .BaseController import BaseController
from models.db_schemes import Project
import json


class NLPController(BaseController):
    def __init__(
        self, vectordb_client=None, generation_client=None, embedding_client=None
    ):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

    def create_collection_name(self, project_id: str):
        return f"collection{project_id}".strip()

    def reset_vector_db_collection(self, project: Project):
        """
        Reset the vector database collection by deleting and recreating it.
        """
        collection_name = self.create_collection_name(project_id=project.id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vector_db_collection_info(self, project: Project):
        """
        Get information about the vector database collection.
        """
        collection_name = self.create_collection_name(project_id=project.id)
        collection_info = self.vectordb_client.get_collection_info(
            collection_name=collection_name
        )
        return json.loads(json.dumps(collection_info, default=lambda o: o.__dict__))

    def index_vector_db(
        self,
        project: Project,
        chunks: list[DataChunk],
        chunks_ids: list[int],
        do_reset: bool = False,
    ):
        """
        Index documents into the vector database collection.
        """
        # get collection name
        collection_name = self.create_collection_name(project_id=project.id)

        # manage items
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]
        vectors = [
            self.embedding_client.embed_text(
                text=text, document_type=DocumentTypeEnum.DOCUMENT.value
            )
            for text in texts
        ]

        # create collection if it does not exist
        _ = self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )
        # insert items into the collection

        result = self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=chunks_ids,
        )
        return True

    def search_vector_db(self, project: Project, query: str, limit: int = 5):
        """
        Search the vector database collection for similar documents.
        """
        collection_name = self.create_collection_name(project_id=project.id)
        vector = self.embedding_client.embed_text(
            text=query, document_type=DocumentTypeEnum.QUERY.value
        )
        if not vector:
            raise ValueError("The vector for the query is empty.")

        search_results = self.vectordb_client.search_by_vector(
            collection_name=collection_name, vector=vector, limit=limit
        )
        if not search_results:
            return False
        return search_results
