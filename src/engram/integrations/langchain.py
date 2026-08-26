"""LangChain integration — Retriever + ChatMessageHistory backed by Engram."""

from __future__ import annotations

from typing import Any, Sequence

try:
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from engram.client import MemoryClient


def _check_langchain():
    if not HAS_LANGCHAIN:
        raise ImportError(
            "LangChain integration requires langchain-core. "
            "Install with: pip install engram[langchain]"
        )


class MemoryRetriever(BaseRetriever if HAS_LANGCHAIN else object):
    """LangChain retriever that searches Engram's hybrid memory."""

    client: Any  # MemoryClient
    user_id: str
    tenant_id: str = "default"
    top_k: int = 10
    token_budget: int = 4000

    class Config:
        arbitrary_types_allowed = True

    async def _aget_relevant_documents(self, query: str, **kwargs) -> list:
        _check_langchain()
        ctx = await self.client.search(
            query,
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            top_k=self.top_k,
            token_budget=self.token_budget,
        )
        docs = []
        for block in ctx.blocks:
            docs.append(Document(
                page_content=block.content,
                metadata={
                    "node_id": block.node_id,
                    "score": block.score,
                    "timestamp": block.timestamp.isoformat(),
                },
            ))
        return docs

    def _get_relevant_documents(self, query: str, **kwargs) -> list:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._aget_relevant_documents(query, **kwargs)
        )


class MemoryChatHistory(BaseChatMessageHistory if HAS_LANGCHAIN else object):
    """LangChain chat history backed by Engram memory."""

    def __init__(
        self,
        client: MemoryClient,
        user_id: str,
        session_id: str,
        tenant_id: str = "default",
    ):
        _check_langchain()
        self.client = client
        self.user_id = user_id
        self.session_id = session_id
        self.tenant_id = tenant_id
        self._messages: list = []

    @property
    def messages(self) -> list:
        return self._messages

    async def aadd_messages(self, messages: Sequence) -> None:
        formatted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append({"role": "user", "content": msg.content})
                self._messages.append(msg)
            elif isinstance(msg, AIMessage):
                formatted.append({"role": "assistant", "content": msg.content})
                self._messages.append(msg)

        if formatted:
            await self.client.add(
                messages=formatted,
                user_id=self.user_id,
                session_id=self.session_id,
                tenant_id=self.tenant_id,
            )

    def add_messages(self, messages: Sequence) -> None:
        import asyncio
        asyncio.get_event_loop().run_until_complete(self.aadd_messages(messages))

    async def aclear(self) -> None:
        self._messages.clear()

    def clear(self) -> None:
        self._messages.clear()
