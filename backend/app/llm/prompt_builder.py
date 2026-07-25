"""
PromptBuilder — Enterprise RAG prompt construction.

Phase 8 upgrade:
  - Requires the LLM to use inline [Source N] citation markers in its answers.
  - Instructs the LLM to use exact statistics and never modify quoted values.
  - Instructs the LLM to state explicitly when information is unavailable.
  - Provides section/heading context per source block for richer answers.
  - Structured answer format: direct answer → cited evidence → confidence note.
"""


class PromptBuilder:
    """Assembles system directives, summaries, active history, context, and questions into prompts."""
    
    @staticmethod
    def build_prompt(
        context: str,
        question: str,
        summary: str | None = None,
        history_context: str | None = None
    ) -> str:
        """Constructs grounded enterprise RAG query prompt."""
        
        system_instructions = """\
You are an enterprise intelligence assistant built on a Retrieval-Augmented Generation (RAG) system.

STRICT RULES — YOU MUST FOLLOW THESE WITHOUT EXCEPTION:
1. Answer ONLY using information from the CONTEXT section below.
2. NEVER invent facts, statistics, names, dates, or figures not present in the context.
3. When the context contains relevant information, cite the source inline using [Source N] markers.
   Example: "The security policy requires AES-256 encryption [Source 1]."
4. Use EXACT statistics, figures, and quoted values from the context — do NOT round or paraphrase numbers.
5. If the answer to the question is NOT in the context, state clearly:
   "This information is not available in the provided documents."
6. Do NOT answer from prior training knowledge — only the provided context counts.
7. If multiple sources support the answer, cite all relevant ones.
8. Keep your answer structured: lead with the direct answer, then supporting evidence with citations.
9. If the question involves a policy, procedure, or guideline — quote the exact rule.
10. Never fabricate citations or source references.\
"""
        
        parts = [
            f"SYSTEM\n{system_instructions}",
            "================================"
        ]
        
        if summary:
            parts.append(f"CONVERSATION SUMMARY\n{summary}")
            parts.append("================================")
            
        if history_context:
            parts.append(f"RECENT CONVERSATION HISTORY\n{history_context}")
            parts.append("================================")
            
        parts.append(f"CONTEXT\n{context if context else 'No context available — no relevant documents found in the knowledge base.'}")
        parts.append("================================")
        parts.append(f"QUESTION\n{question}")
        parts.append("================================")
        parts.append(
            "ANSWER (use [Source N] inline citations, exact statistics, no fabrication):"
        )
        
        return "\n".join(parts)
    
    @staticmethod
    def build_rewrite_prompt(conversation_history: str, follow_up: str) -> str:
        """Constructs standalone question rewrite prompt for multi-turn conversations."""
        return (
            f"Given the following conversation history and a follow-up question, "
            f"rewrite the follow-up question as a standalone question that fully captures "
            f"the user's intent without needing any prior context.\n\n"
            f"CONVERSATION HISTORY\n{conversation_history}\n"
            f"--------------------------------\n"
            f"FOLLOW-UP QUESTION\n{follow_up}\n"
            f"--------------------------------\n"
            f"STANDALONE QUESTION:"
        )
