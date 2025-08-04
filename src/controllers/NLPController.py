from models.db_schemes.data_chunk import DataChunk
from .BaseController import BaseController
from models.db_schemes import Project, retrieved_document
from stores.llm.LLMEnums import DocumentTypeEnum
import json


class NLPController(BaseController):
    def __init__(
        self,
        vectordb_client=None,
        generation_client=None,
        embedding_client=None,
        template_parser=None,
    ):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        return f"collection{project_id}".strip()

    def reset_vector_db_collection(self, project: Project):
        """
        Reset the vector database collection by deleting and recreating it.
        """
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vector_db_collection_info(self, project: Project):
        """
        Get information about the vector database collection.
        """
        collection_name = self.create_collection_name(project_id=project.project_id)
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
        collection_name = self.create_collection_name(project_id=project.project_id)

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
        collection_name = self.create_collection_name(project_id=project.project_id)
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

    def answer_rag_question(self, project: Project, query: str, limit: int = 5):
        """
        Answer a question using the RAG approach.
        """

        answer, full_prompt, chat_history = None, None, None
        retrieved_document = self.search_vector_db(
            project=project, query=query, limit=limit
        )
        if not retrieved_document:
            return answer, full_prompt, chat_history

        # construct llm prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")
        document_prompt = "\n".join(
            [
                self.template_parser.get(
                    "rag", "document_prompt", {"doc_num": idx, "chunk_text": doc.text}
                )
                for idx, doc in enumerate(retrieved_document)
            ]
        )
        footer_prompt = self.template_parser.get(
            "rag", "footer_prompt", {"query": query}
        )
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt, role=self.generation_client.enums.SYSTEM.value
            ),
        ]
        full_prompt = "\n\n".join([document_prompt, footer_prompt])

        # Generate an answer using the generation client
        answer = self.generation_client.generate_text(
            prompt=full_prompt, chat_history=chat_history
        )
        return answer, full_prompt, chat_history
