"""QA engine: keyword search + LLM prompt.

`call_llm` is imported lazily inside `answer()` so the file imports
cleanly even when the LLM client is not configured.
"""
from typing import List, Dict, Any, Optional
from .knowledge_base import KnowledgeBase


class QAEngine:
    """One-shot QA: retrieve chunks, ask the LLM."""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base
        self.llm_client = None

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        if not documents:
            return ""

        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get('metadata', {}).get('source', 'unknown')
            score = doc.get('score', 0)
            content = doc.get('content', '')[:500]

            context_parts.append(
                f"[Doc {i}]\nsource: {source}\nrelevance: {score:.2f}\ncontent:\n{content}\n---"
            )

        return "\n".join(context_parts)

    def _build_prompt(self, question: str, context: str) -> str:
        if context:
            return (
                "Answer the question using the documents below.\n"
                "If the answer is not in the documents, say so explicitly.\n\n"
                f"Documents:\n{context}\n\nQuestion: {question}"
            )
        return f"Answer the question briefly.\n\nQuestion: {question}"

    async def answer(self, question: str, llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Answer `question` using retrieved chunks.

        With `llm_config` we ask the model via `call_llm`; without it, we
        fall back to a stub answer that says how many chunks matched.
        """
        search_results = self.knowledge_base.search(question, top_k=5)
        context = self._format_context(search_results)
        prompt = self._build_prompt(question, context)

        if llm_config:
            try:
                from services.llm_service import call_llm
                answer_text = (await call_llm(prompt)) or ""

                return {
                    'success': True,
                    'answer': answer_text or f"Question: {question}; matched {len(search_results)} documents",
                    'context': context,
                    'sources': [doc.get('metadata', {}).get('source', '') for doc in search_results],
                    'model': llm_config.get('model'),
                    'provider': llm_config.get('provider'),
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'qa_engine_error',
                }
        else:
            return {
                'success': True,
                'answer': f"Question: {question}; matched {len(search_results)} documents (LLM not configured)",
                'context': context,
                'sources': [doc.get('metadata', {}).get('source', '') for doc in search_results],
            }

    async def chat(self, question: str, llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Chat-mode answer (alias for answer)."""
        return await self.answer(question, llm_config)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        return self.knowledge_base.search(query, top_k)

    def get_stats(self) -> Dict[str, Any]:
        """Return KB stats."""
        return self.knowledge_base.get_stats()


class ConversationalQAEngine(QAEngine):
    """Conversational QA with history."""

    def __init__(self, knowledge_base: KnowledgeBase):
        super().__init__(knowledge_base)
        self.conversation_history: List[Dict[str, str]] = []

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': self._get_timestamp()
        })

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()

    def _build_conversational_prompt(self, question: str, context: str) -> str:
        history = "\n".join([
            f"{item['role']}: {item['content']}"
            for item in self.conversation_history[-5:]
        ])

        if context:
            prompt = (
                "You are a QA assistant. Answer using the provided documents.\n\n"
                f"Conversation history:\n{history}\n\n"
                f"Reference documents:\n{context}\n\n"
                f"Current question: {question}\n\n"
                "Rules:\n"
                "1. Prefer answers from the reference documents.\n"
                "2. Consider conversation history for context.\n"
                "3. Cite the source when quoting a document.\n"
                "4. If the documents don't contain the answer, say so.\n"
                "5. Keep answers concise and natural.\n"
            )
        else:
            prompt = (
                "You are a QA assistant.\n\n"
                f"Conversation history:\n{history}\n\n"
                f"Current question: {question}\n\n"
                "Answer concisely.\n"
            )

        return prompt

    async def answer(self, question: str, llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Answer with conversation history."""
        self.add_to_history('user', question)

        search_results = self.knowledge_base.search(question, top_k=5)
        context = self._format_context(search_results)
        prompt = self._build_conversational_prompt(question, context)

        if llm_config:
            try:
                from services.llm_service import call_llm
                answer_text = (await call_llm(prompt)) or ""
                self.add_to_history('assistant', answer_text)

                return {
                    'success': True,
                    'answer': answer_text,
                    'context': context,
                    'sources': [doc.get('metadata', {}).get('source', '') for doc in search_results],
                    'conversation_history': self.conversation_history,
                    'model': llm_config.get('model'),
                    'provider': llm_config.get('provider'),
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'qa_engine_error',
                }
        else:
            answer_text = f"Question: {question}\n\nFound {len(search_results)} relevant documents. Configure an LLM for detailed answers."
            self.add_to_history('assistant', answer_text)

            return {
                'success': True,
                'answer': answer_text,
                'context': context,
                'sources': [doc.get('metadata', {}).get('source', '') for doc in search_results],
                'conversation_history': self.conversation_history,
            }

    def clear_history(self):
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation_history
