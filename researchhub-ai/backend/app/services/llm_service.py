"""
llm_service.py – Groq Llama-3.3-70b-versatile inference for research Q&A.
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    MODEL = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.3       # Low temp → precise, research-focused answers
    MAX_TOKENS = 2048

    SYSTEM_PROMPT = (
        "You are a research assistant helping analyse academic literature. "
        "Provide precise, evidence-based answers grounded in the papers supplied. "
        "When relevant insights appear in the context, cite them explicitly. "
        "Be concise, structured, and always acknowledge when information is limited."
    )

    def __init__(self):
        self._client = None   # lazily initialised on first request

    def _get_client(self):
        """Return (and lazily create) the Groq client."""
        if self._client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY is not set. "
                    "Add it to your .env file and restart the server."
                )
            from groq import Groq
            self._client = Groq(api_key=api_key)
        return self._client

    # ── Public API ─────────────────────────────────────────────────────────
    def generate_research_answer(
        self,
        query: str,
        context_chunks: List[str],
        chat_history: Optional[List[dict]] = None,
    ) -> str:
        """
        Build a RAG prompt from *context_chunks* + *query*, send to Groq,
        and return the model's answer string.
        """
        context = "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant context found."

        user_message = (
            f"Context from research papers:\n{context}\n\n"
            f"Question:\n{query}\n\n"
            "Provide a clear research-focused answer summarising the key insights."
        )

        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if chat_history:
            messages.extend(chat_history[-6:])   # last 3 turns
        messages.append({"role": "user", "content": user_message})

        response = self._get_client().chat.completions.create(
            model=self.MODEL,
            messages=messages,
            temperature=self.TEMPERATURE,
            max_tokens=self.MAX_TOKENS,
        )
        return response.choices[0].message.content

    def summarise_paper(self, title: str, abstract: str) -> str:
        """Return a 2-3 sentence summary of a paper."""
        prompt = (
            f"Summarise this research paper in 2-3 sentences:\n"
            f"Title: {title}\nAbstract: {abstract}"
        )
        response = self._get_client().chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=256,
        )
        return response.choices[0].message.content


llm_service = LLMService()
