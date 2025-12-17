"""
RAG Pipeline module - Core orchestration logic.

Features:
- End-to-end query processing
- Streaming response generation
- Source citation
- Conversation context (optional)
"""
from collections.abc import Generator
from dataclasses import dataclass
from typing import Literal

from openai import AzureOpenAI

from .config import get_openai_token, get_settings
from .retriever import ContextBuilder, HybridRetriever, SearchResult


@dataclass
class RAGResponse:
    """Represents a complete RAG response."""

    answer: str
    sources: list[dict]
    context_used: str
    search_results: list[SearchResult]


class RAGPipeline:
    """
    Production-ready RAG pipeline.

    Orchestrates:
    1. Query understanding
    2. Context retrieval
    3. Response generation
    4. Source attribution
    """

    # System prompt for RAG responses
    DEFAULT_SYSTEM_PROMPT = """あなたは提供されたコンテキストに基づいて質問に回答するAIアシスタントです。

## 回答ルール
1. 提供されたコンテキストの情報のみを使用して回答する
2. コンテキストに該当情報がない場合は「提供された情報では回答できません」と明示する
3. 回答には必ず参照元を引用する（例：「[Source: xxx] によると...」）
4. 技術的な質問には正確かつ実用的な回答を心がける
5. 日本語で回答する

## 回答フォーマット
- 簡潔で構造化された回答を提供
- コード例がある場合はMarkdown形式で記述
- 不確実な情報は推測として明示"""

    def __init__(
        self,
        system_prompt: str | None = None,
        max_context_tokens: int = 4000,
    ):
        """
        Initialize RAG pipeline.

        Args:
            system_prompt: Custom system prompt (uses default if None)
            max_context_tokens: Maximum tokens for context window
        """
        settings = get_settings()

        self.retriever = HybridRetriever()
        self.context_builder = ContextBuilder(max_context_tokens)
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT

        # Initialize OpenAI client
        self.openai_client = AzureOpenAI(
            azure_endpoint=settings.openai_endpoint,
            azure_ad_token_provider=get_openai_token,
            api_version=settings.openai_api_version,
        )
        self.chat_deployment = settings.openai_deployment_chat

    def query(
        self,
        question: str,
        top_k: int = 5,
        search_mode: Literal["vector", "keyword", "hybrid"] = "hybrid",
        filters: str | None = None,
        stream: bool = False,
        conversation_history: list[dict] | None = None,
    ) -> RAGResponse | Generator[str, None, RAGResponse]:
        """
        Execute RAG query.

        Args:
            question: User question
            top_k: Number of context chunks to retrieve
            search_mode: Search strategy
            filters: OData filter for search
            stream: Whether to stream response
            conversation_history: Previous messages for context

        Returns:
            RAGResponse or Generator yielding chunks then RAGResponse
        """
        # Step 1: Retrieve relevant context
        search_results = self.retriever.search(
            query=question,
            top_k=top_k,
            mode=search_mode,
            filters=filters,
        )

        # Step 2: Build context
        context, sources = self.context_builder.build_context(search_results)

        # Step 3: Generate response
        if stream:
            return self._generate_streaming_response(
                question=question,
                context=context,
                sources=sources,
                search_results=search_results,
                conversation_history=conversation_history,
            )
        else:
            return self._generate_response(
                question=question,
                context=context,
                sources=sources,
                search_results=search_results,
                conversation_history=conversation_history,
            )

    def _build_messages(
        self,
        question: str,
        context: str,
        conversation_history: list[dict] | None = None,
    ) -> list[dict]:
        """Build message list for chat completion."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current question with context
        user_message = f"""## コンテキスト
{context}

## 質問
{question}"""

        messages.append({"role": "user", "content": user_message})

        return messages

    def _generate_response(
        self,
        question: str,
        context: str,
        sources: list[dict],
        search_results: list[SearchResult],
        conversation_history: list[dict] | None = None,
    ) -> RAGResponse:
        """Generate non-streaming response."""
        messages = self._build_messages(question, context, conversation_history)

        response = self.openai_client.chat.completions.create(
            model=self.chat_deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

        answer = response.choices[0].message.content or ""

        return RAGResponse(
            answer=answer,
            sources=sources,
            context_used=context,
            search_results=search_results,
        )

    def _generate_streaming_response(
        self,
        question: str,
        context: str,
        sources: list[dict],
        search_results: list[SearchResult],
        conversation_history: list[dict] | None = None,
    ) -> Generator[str, None, RAGResponse]:
        """Generate streaming response."""
        messages = self._build_messages(question, context, conversation_history)

        response = self.openai_client.chat.completions.create(
            model=self.chat_deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=True,
        )

        answer_parts = []
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                answer_parts.append(content)
                yield content

        # Return final response object
        return RAGResponse(
            answer="".join(answer_parts),
            sources=sources,
            context_used=context,
            search_results=search_results,
        )


class ConversationManager:
    """
    Manages multi-turn conversations for RAG.

    Features:
    - Conversation history tracking
    - Token-aware history truncation
    - Session persistence (optional)
    """

    def __init__(
        self,
        max_history_turns: int = 5,
        max_history_tokens: int = 2000,
    ):
        """
        Initialize conversation manager.

        Args:
            max_history_turns: Maximum conversation turns to retain
            max_history_tokens: Maximum tokens for history
        """
        self.max_turns = max_history_turns
        self.max_tokens = max_history_tokens
        self.conversations: dict[str, list[dict]] = {}

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """
        Add conversation turn.

        Args:
            session_id: Unique session identifier
            user_message: User's question
            assistant_message: Assistant's response
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        history = self.conversations[session_id]

        # Add new turn
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_message})

        # Truncate if needed
        while len(history) > self.max_turns * 2:
            history.pop(0)
            history.pop(0)

    def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for session."""
        return self.conversations.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
