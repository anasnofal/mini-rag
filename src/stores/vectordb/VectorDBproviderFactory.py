from .providers import QdrantDbProvider
from .VectorDBEnums import VectorDBProvider
from controllers.BaseController import BaseController


class VectorDBProviderFactory:
    def __init__(self, config: dict):
        self.config = config
        self.base_controller = BaseController()

    def create(self, provider: str):
        if provider == VectorDBProvider.QDRANT.value:
            db_path = self.base_controller.get_database_path(self.config.VECTOR_DB_PATH)
            return QdrantDbProvider(
                db_path=db_path,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            )
        return None
