from enum import Enum


class LLMEnums(Enum):
    OPENAI = "openai"
    COHERE = "cohere"
    GEMINI = "gemini"


class OpenAiEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class GeminiEnums(Enum):
    SYSTEM = "model"
    USER = "user"
    ASSISTANT = "assistant"


class CohereEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    DOCUMENT = "search_document"
    QUERY = "search_query"


class DocumentTypeEnum(Enum):
    DOCUMENT = "document"
    QUERY = "query"


class DocumentTypeEnumGemini(Enum):
    RETRIEVAL_QUERY = "retrieval_query"  # Specifies the given text is a query in a search or retrieval setting.
    RETRIEVAL_DOCUMENT = "retrieval_document"  # Specifies the given text is a document in a search or retrieval setting.
    SEMANTIC_SIMILARITY = "semantic_similarity"  # Specifies the given text will be used for Semantic Textual Similarity (STS).
    CLASSIFICATION = "classification"  # Specifies that the embeddings will be used for classification.
    CLUSTERING = (
        "clustering"  # Specifies that the embeddings will be used for clustering.
    )
