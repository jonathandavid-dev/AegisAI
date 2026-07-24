class PromptBuilder:
    """Assembles system directives, summaries, active history, context, and questions into prompts."""
    
    @staticmethod
    def build_prompt(
        context: str,
        question: str,
        summary: str | None = None,
        history_context: str | None = None
    ) -> str:
        """Constructs grounded query prompt incorporating layered conversation memory."""
        system_instructions = (
            "You are an enterprise knowledge assistant.\n"
            "Answer ONLY using the supplied context.\n"
            "If the answer is not contained in the context, clearly state that the information is unavailable.\n"
            "Never invent facts.\n"
            "Do not rely on prior knowledge."
        )
        
        parts = [
            f"SYSTEM\n{system_instructions}",
            "--------------------------------"
        ]
        
        if summary:
            parts.append(f"CONVERSATION SUMMARY\n{summary}")
            parts.append("--------------------------------")
            
        if history_context:
            parts.append(f"RECENT CONVERSATION HISTORY\n{history_context}")
            parts.append("--------------------------------")
            
        parts.append(f"CONTEXT\n{context if context else 'No context available.'}")
        parts.append("--------------------------------")
        
        parts.append(f"QUESTION\n{question}")
        
        return "\n".join(parts)
