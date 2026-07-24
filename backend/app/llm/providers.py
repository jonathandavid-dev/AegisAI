import abc
import re
import json
import asyncio
import httpx
from typing import AsyncGenerator
from app.config.settings import settings

class BaseLLMProvider(abc.ABC):
    """Abstract interface defining the text generation execution contract."""
    
    @abc.abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Sends prompt to LLM and returns the text completion result."""
        pass

    @abc.abstractmethod
    async def generate_text_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Sends prompt to LLM and yields token-by-token response chunks."""
        pass

class MockProvider(BaseLLMProvider):
    """Grounded mock provider generating deterministic offline responses based on context."""
    
    def generate_text(self, prompt: str) -> str:
        # 1. Handle query rewriting prompt
        if "STANDALONE QUESTION:" in prompt:
            followup_match = re.search(r"FOLLOW-UP QUESTION\n(.*?)(?:\n--------------------------------|\Z)", prompt, re.DOTALL)
            if followup_match:
                return followup_match.group(1).strip()
            return "What degree does Jonathan hold and which institute did he graduate from?"

        # 2. Extract context block
        context_match = re.search(r"CONTEXT\n(.*?)(?:\n--------------------------------|\Z)", prompt, re.DOTALL)
        context_block = context_match.group(1).strip() if context_match else ""
        
        # 3. Extract question
        question_match = re.search(r"QUESTION\n(.*)$", prompt, re.DOTALL)
        question = question_match.group(1).strip() if question_match else ""
        
        if not context_block or context_block == "No context available.":
            return "I am sorry, but the requested information is not available in the supplied documents."
            
        # Clean source markers out of context
        clean_context = re.sub(r"\[Source \d+: [^\]]+\]", "", context_block).strip()
        
        # Segment the context into sentences or bullet points for matching
        segments = []
        for line in clean_context.split("\n"):
            line = line.strip()
            if line:
                # Split on sentence terminals or bullet points
                sub_segments = re.split(r"(?<=[.!?])\s+|[•\-\*]\s+", line)
                for sub in sub_segments:
                    sub = sub.strip()
                    if sub:
                        segments.append(sub)
                        
        # Extract keywords from the question (words > 3 chars, lowercase)
        keywords = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 3]
        
        # Score segments by keyword frequency
        scored_segments = []
        for seg in segments:
            score = sum(1 for kw in keywords if kw in seg.lower())
            if score > 0:
                scored_segments.append((score, seg))
                
        if scored_segments:
            # Sort by highest score first
            scored_segments.sort(key=lambda x: x[0], reverse=True)
            # Take the top matching segments (up to 3) and combine them into a coherent answer
            selected = []
            for _, seg in scored_segments[:3]:
                if seg not in selected:
                    selected.append(seg)
            answer = " ".join(selected)
            if not answer.endswith("."):
                answer += "."
            return answer
            
        # Fallback to returning a clean excerpt if no keywords matched
        excerpt = clean_context.replace("\n", " ").strip()
        return f"Based on the provided documents: {excerpt[:300]}..."

    async def generate_text_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        answer = self.generate_text(prompt)
        words = answer.split(" ")
        for i, word in enumerate(words):
            suffix = " " if i < len(words) - 1 else ""
            yield word + suffix
            await asyncio.sleep(0.02)


class OpenAIProvider(BaseLLMProvider):
    """API provider querying OpenAI-compatible completions endpoints."""
    
    def generate_text(self, prompt: str) -> str:
        if not settings.LLM_API_KEY:
            raise ValueError("LLM_API_KEY is not configured in settings.")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS
        }
        
        with httpx.Client(timeout=settings.LLM_TIMEOUT) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def generate_text_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        if not settings.LLM_API_KEY:
            raise ValueError("LLM_API_KEY is not configured in settings.")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except Exception:
                            pass
