from enum import Enum


class VectorDBProvider(Enum):
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"


class DistanceMetricEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"


class PgVectorTTableSchemeEnums(Enum):
    ID = "id"
    TEXT = "text"
    VECTOR = "vector"
    METADATA = "metadata"
    CHUNK_ID = "chunk_id"
    _PREFIX = "pgvector"


class PgVectorDistanceEnums(Enum):
    COSINE = "vector_cosine_ops"
    DOT = "vector_L2_ops"


class PgVectorIndexTypeEnums(Enum):
    HNSW = "hnsw"
    IVFFLAT = "ivfflat"
