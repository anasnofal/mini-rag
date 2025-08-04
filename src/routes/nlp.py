from venv import logger
from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from requests import request
from controllers import NLPController
from routes.schemes import nlp
from routes.schemes.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
import logging
from models import ResponseResult

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["NLP", "api_v1"],
)


@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: int, push_request: PushRequest):
    """Push an index to the NLP service for a specific project."""
    project_model = await ProjectModel.create_instance(request.app.db_client)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseResult.PROJECT_NOT_FOUND.value},
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    has_records = True
    page_no = 1
    inserted_items = 0
    idx = 0
    while has_records:
        page_chunks = await chunk_model.get_chunks_by_project_id(
            project_id=project.project_id,
            page_no=page_no,
        )
        if len(page_chunks):
            page_no += 1

        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break

        chunks_ids = list(range(idx, idx + len(page_chunks)))
        idx += len(page_chunks)

        is_inserted = nlp_controller.index_vector_db(
            project=project,
            chunks=page_chunks,
            chunks_ids=chunks_ids,
            do_reset=push_request.do_reset,
        )
        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": ResponseResult.INSERT_INTO_VECTOR_DB_ERROR.value},
            )
        inserted_items += len(page_chunks)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseResult.INSERT_INTO_VECTOR_DB_SUCCESS.value,
            "inserted_items_count": inserted_items,
        },
    )


@nlp_router.get("/index/info/{project_id}")
async def get_index_info(request: Request, project_id: int):
    """Get information about the index for a specific project."""
    project_model = await ProjectModel.create_instance(request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseResult.PROJECT_NOT_FOUND.value},
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    collection_info = nlp_controller.get_vector_db_collection_info(project=project)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseResult.VECTOR_DB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info,
        },
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(
    request: Request, project_id: int, search_request: SearchRequest
):
    project_model = await ProjectModel.create_instance(request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseResult.PROJECT_NOT_FOUND.value},
        )
    nlp_controller = NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    search_results = nlp_controller.search_vector_db(
        project=project,
        query=search_request.query,
        limit=search_request.limit,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseResult.VECTOR_DB_SEARCH_SUCCESS.value,
            "search_results": [result.dict() for result in search_results],
        },
    )


@nlp_router.post("/index/answer/{project_id}")
async def answer_index(
    request: Request, project_id: int, search_request: SearchRequest
):
    project_model = await ProjectModel.create_instance(request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseResult.PROJECT_NOT_FOUND.value},
        )
    nlp_controller = NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    answer, full_prompt, chat_history = nlp_controller.answer_rag_question(
        project=project,
        query=search_request.query,
        limit=search_request.limit,
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseResult.RAG_ANSWER_ERROR.value,
                "message": "No relevant documents found for the query.",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseResult.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history,
        },
    )
