from enum import Enum


class ResponseResult(Enum):
    FILE_VALIDATED_SUCCESS = "file_validate_successfully"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    PROCESSING_FAILED = "processing_failed"
    PROCESSING_SUCCESS = "processing_success"
    NO_FILES_FOUND = "no_files_found"
    CHUNK_CREATION_SUCCESS = "chunk_creation_success"
    FILE_ID_ERROR = "file_id_error"
    PROJECT_NOT_FOUND = "project_not_found"
    INSERT_INTO_VECTOR_DB_ERROR = "insert_into_vector_db_error"
    INSERT_INTO_VECTOR_DB_SUCCESS = "insert_into_vector_db_success"
    Vector_db_collection_retrieved = "vector_db_collection_retrieved"
