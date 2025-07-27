from enum import Enum

class VectorDBProvider(Enum):
    QDRANT = "qdrant"

class DistanceMetricEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"