from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_app_settings
from src.core.dtos.llm_provider_dtos import LLMRouteConfigDTO, EmbeddingConfigDTO
from src.core.enums import EmbeddingProvider
from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.iproject_repository import IProjectRepository
from src.core.interfaces.idocument_page_repository import IDocumentPageRepository
from src.core.interfaces.ichat_repository import IChatRepository
from src.core.interfaces.imessage_repository import IMessageRepository
from src.core.interfaces.imedia_repository import IMediaRepository
from src.core.interfaces.iprovider_settings_repository import (
    IProviderSettingsRepository,
)
from src.core.interfaces.idocument_repository import IDocumentRepository
from src.core.interfaces.iembedding_provider import IEmbeddingProvider
from src.infra.llms.litellm_embedding_adapter import LiteLLMEmbeddingAdapter
from src.services.embedding_service import EmbeddingService

from src.infra.python_logger import PythonLogger
from src.infra.postgres_adapter import AsyncSessionLocal
from src.infra.repositories.project_repository import ProjectRepository
from src.infra.repositories.document_repository import DocumentRepository
from src.infra.repositories.document_page_repository import DocumentPageRepository
from src.infra.repositories.chat_repository import ChatRepository
from src.infra.repositories.message_repository import MessageRepository
from src.infra.repositories.media_repository import MediaRepository
from src.infra.repositories.provider_settings_repository import (
    ProviderSettingsRepository,
)

# Initialize logger wrapper
app_settings = get_app_settings()
_logger_instance = PythonLogger(
    name=app_settings.APP_NAME,
    app_state=app_settings.APP_ENV,
    level=app_settings.APP_LOG_LEVEL,
)

active_embedding_config = EmbeddingConfigDTO(
    provider=EmbeddingProvider.OLLAMA,
    model_name="nomic-embed-text-v2-moe",
    dimensions=768,
    base_url="http://localhost:11434",
)


async def get_logger() -> ILogger:
    """
    Dependency that provides an instance of ILogger.
    """
    return _logger_instance


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an AsyncSession per request, ensuring clean disposal/rollback.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_project_repository(
    session: AsyncSession = Depends(get_db_session),
    logger: ILogger = Depends(get_logger),
) -> IProjectRepository:
    """
    Dependency that injects the Project repository.
    """
    return ProjectRepository(session=session, logger=logger)


def get_document_repository(
    session: AsyncSession = Depends(get_db_session),
    logger: ILogger = Depends(get_logger),
) -> IDocumentRepository:
    """
    Dependency that injects the Document repository.
    """
    return DocumentRepository(session=session, logger=logger)


def get_document_page_repository(
    session: AsyncSession = Depends(get_db_session),
    logger: ILogger = Depends(get_logger),
) -> IDocumentPageRepository:
    """
    Dependency that injects the DocumentPage repository.
    """
    return DocumentPageRepository(session=session, logger=logger)


def get_chat_repository(
    session: AsyncSession = Depends(get_db_session),
    logger: ILogger = Depends(get_logger),
) -> IChatRepository:
    """
    Dependency that injects the Chat repository.
    """
    return ChatRepository(session=session, logger=logger)


def get_message_repository(
    session: AsyncSession = Depends(get_db_session),
    logger: ILogger = Depends(get_logger),
) -> IMessageRepository:
    """
    Dependency that injects the Message repository.
    """
    return MessageRepository(session=session, logger=logger)


def get_media_repository(
    session: AsyncSession = Depends(get_db_session),
    logger: ILogger = Depends(get_logger),
) -> IMediaRepository:
    """
    Dependency that injects the Media repository.
    """
    return MediaRepository(session=session, logger=logger)


def get_provider_settings_repository(
    session: AsyncSession = Depends(get_db_session),
    logger: ILogger = Depends(get_logger),
) -> IProviderSettingsRepository:
    """
    Dependency that injects the ProviderSettings repository.
    """
    return ProviderSettingsRepository(session=session, logger=logger)


def get_embedding_provider(
    logger: ILogger = Depends(get_logger),
) -> IEmbeddingProvider:
    """
    Dependency that injects the LiteLLM embedding adapter initialized with active_embedding_config.
    """
    return LiteLLMEmbeddingAdapter(config=active_embedding_config, logger=logger)


def get_fast_parser(logger: ILogger = Depends(get_logger)):
    import pymupdf
    from src.infra.pymupdf_parser import PyMuPDFParser

    return PyMuPDFParser(mupdf_client=pymupdf, logger=logger)


def get_vision_provider():
    from src.infra.llms.litellm_vision_adapter import LiteLLMVisionProvider
    from src.core.enums import ChatProvider

    vision_config = LLMRouteConfigDTO(
        provider=ChatProvider.OPENAI,
        model_name="gpt-4o",
        temperature=0.0,
    )
    return LiteLLMVisionProvider(config=vision_config)


def get_pdf_service(
    session: AsyncSession = Depends(get_db_session),
    parser=Depends(get_fast_parser),
    embedding_provider: IEmbeddingProvider = Depends(get_embedding_provider),
    page_repo: IDocumentPageRepository = Depends(get_document_page_repository),
    doc_repo: IDocumentRepository = Depends(get_document_repository),
    vision_llm=Depends(get_vision_provider),
    logger: ILogger = Depends(get_logger),
):
    from src.services.pdf_service import PDFService

    return PDFService(
        session=session,
        parser=parser,
        embedding_provider=embedding_provider,
        page_repo=page_repo,
        doc_repo=doc_repo,
        vision_llm=vision_llm,
        logger=logger,
    )


def get_embedding_service(
    document_page_repo: IDocumentPageRepository = Depends(get_document_page_repository),
    embedding_provider: IEmbeddingProvider = Depends(get_embedding_provider),
    logger: ILogger = Depends(get_logger),
) -> EmbeddingService:
    """
    Dependency that injects the EmbeddingService use case layer.
    """
    return EmbeddingService(
        document_page_repo=document_page_repo,
        embedding_provider=embedding_provider,
        logger=logger,
    )


def get_encryption_service():
    """
    Dependency that provides the EncryptionService for securing API keys.
    """
    from src.services.encryption_service import EncryptionService

    return EncryptionService()


def get_http_client(
    logger: ILogger = Depends(get_logger),
):
    """
    Dependency that provides an instance of IHTTPClient backed by HttpxClient.
    """
    import httpx
    from src.infra.httpx_adapter import HttpxClient

    return HttpxClient(client=httpx.AsyncClient(), logger=logger)


def get_tts_provider(
    logger: ILogger = Depends(get_logger),
    http_client=Depends(get_http_client),
):
    """
    Dependency that provides the configured text-to-speech provider.
    """
    import os
    from src.infra.tts import OpenAITTSProvider

    return OpenAITTSProvider(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        logger=logger,
        http_client=http_client,
    )


def get_llm_provider(
    logger: ILogger = Depends(get_logger),
):
    """
    Dependency that provides the default LiteLLMAdapter provider.
    """
    import os
    from src.infra.llms.litellm_adapter import LiteLLMAdapter
    from src.core.dtos.llm_provider_dtos import LLMRouteConfigDTO
    from src.core.enums import ChatProvider

    config = LLMRouteConfigDTO(
        provider=ChatProvider.OPENAI,
        model_name="gpt-4o-mini",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return LiteLLMAdapter(config=config, logger=logger)


def get_audio_script_prompt() -> str:
    """
    Dependency that provides the prompt template for generating audio scripts.
    """
    from src.core.prompts import AUDIO_SCRIPT_PROMPT_TEMPLATE

    return AUDIO_SCRIPT_PROMPT_TEMPLATE


def get_audio_explanation_service(
    pdf_service=Depends(get_pdf_service),
    llm_provider=Depends(get_llm_provider),
    tts_provider=Depends(get_tts_provider),
    script_prompt_template: str = Depends(get_audio_script_prompt),
):
    """
    Dependency that injects AudioExplanationService.
    """
    from src.services.audio_explanation_service import AudioExplanationService

    return AudioExplanationService(
        pdf_service=pdf_service,
        llm_provider=llm_provider,
        tts_provider=tts_provider,
        script_prompt_template=script_prompt_template,
    )

