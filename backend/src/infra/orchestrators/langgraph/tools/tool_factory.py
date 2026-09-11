from typing import Annotated, List, Optional
import uuid
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from src.services.pdf_service import PDFService


class LangGraphToolFactory:
    def __init__(
        self,
        pdf_service: PDFService,
    ):
        self._pdf_service = pdf_service

    def get_all_tools(self) -> list:
        """Returns the complete toolkit bound to the agent."""
        return [
            self._build_hybrid_search_tool(),
            self._build_get_pages_in_range_tool(),
            self._build_get_toc_tool(),
            self._build_get_metadata_tool(),
        ]

    def _build_hybrid_search_tool(self):
        """Builds the autonomous retrieval and on-the-fly embedding tool."""
        service = self._pdf_service

        @tool("search_documents")
        async def search_documents(
            query: str, state: Annotated[dict, InjectedState]
        ) -> str:
            """
            Search the active document for specific information, context, or keywords.
            Use this tool to find factual answers from the user's PDF.

            Args:
                query: The semantic search query or keywords to look for.
            """
            doc_id = state.get("document_id")
            if not doc_id:
                return "No document_id found in state."

            try:
                # Executes hybrid search and lazily embeds missing vectors
                pages = await service.hybrid_retrieve(
                    doc_id=doc_id, query=query, limit=3
                )

                if not pages:
                    return "No relevant information found in the document. Try adjusting your search query."

                # Format the returned DTOs into a structured string for the LLM context window
                return "\n\n".join(
                    f"--- Page {p.page_num} ---\n{p.deep_content or p.content}"
                    for p in pages
                )

            except Exception as e:
                # Prevent the graph from crashing on temporary DB or API failures
                return f"Search failed due to a system error: {str(e)}. Tell the user to try again."

        return search_documents

    def _build_get_pages_in_range_tool(self):
        """Builds the tool to retrieve sequential document pages by page range."""
        service = self._pdf_service

        @tool("get_pages_in_range")
        async def get_pages_in_range(
            start_page: int, end_page: int, state: Annotated[dict, InjectedState]
        ) -> str:
            """
            Read specific sequential pages of the active document by page range.
            Maximum page range is 10 pages.

            Args:
                start_page: 1-indexed starting page number.
                end_page: 1-indexed ending page number (inclusive).
            """
            doc_id = state.get("document_id")
            if not doc_id:
                return "No document_id found in state."

            if start_page > end_page:
                return "Invalid page range: start_page must be less than end_page."
            if end_page - start_page > 10:
                return "Page range too large: maximum is 10 pages."

            try:
                pages = await service.get_pages_in_range(
                    doc_id=doc_id, start_page=start_page, end_page=end_page
                )
                if not pages:
                    return f"No pages found in range {start_page} to {end_page}."

                return "\n\n".join(
                    f"--- Page {p.page_num} ---\n{p.deep_content or p.content}"
                    for p in pages
                )
            except Exception as e:
                return f"Failed to retrieve pages in range: {str(e)}"

        return get_pages_in_range

    def _build_get_toc_tool(self):
        """Builds the tool to retrieve the document table of contents."""
        service = self._pdf_service

        @tool("get_document_toc")
        async def get_document_toc(state: Annotated[dict, InjectedState]) -> str:
            """
            Get the Table of Contents (bookmarks outline) of the active document.
            """
            doc_id = state.get("document_id")
            if not doc_id:
                return "No document_id found in state."

            try:
                toc = await service.get_document_toc(doc_id=doc_id)
                if not toc:
                    return "Document does not have a table of contents."

                lines = [
                    f"- {'  ' * (item.level - 1)}{item.title} (Page {item.page_num})"
                    for item in toc
                ]
                return "\n".join(lines)
            except Exception as e:
                return f"Failed to retrieve table of contents: {str(e)}"

        return get_document_toc

    def _build_get_metadata_tool(self):
        """Builds the tool to retrieve document header metadata."""
        service = self._pdf_service

        @tool("get_document_metadata")
        async def get_document_metadata(state: Annotated[dict, InjectedState]) -> str:
            """
            Get metadata (total pages, title, author, file size) of the active document.
            """
            doc_id = state.get("document_id")
            if not doc_id:
                return "No document_id found in state."

            try:
                meta = await service.get_document_metadata(doc_id=doc_id)
                return (
                    f"Title: {meta.title or 'Unknown'}\n"
                    f"Author: {meta.author or 'Unknown'}\n"
                    f"Total Pages: {meta.total_pages}\n"
                    f"File Size: {meta.file_size_bytes} bytes"
                )
            except Exception as e:
                return f"Failed to retrieve document metadata: {str(e)}"

        return get_document_metadata
