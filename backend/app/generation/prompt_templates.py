"""Prompt templates for the GroundedAI generation pipeline."""

GROUNDED_PROMPT = """You are GroundedAI, a precise enterprise document assistant.
Your ONLY job is to answer questions using the provided context.

STRICT RULES:
1. Answer ONLY from the context. Never use prior knowledge.
2. Cite every claim using [filename, p.N] inline format.
3. If context is insufficient, say so explicitly. Never guess.
4. Be concise. No filler. No preamble.

CONTEXT:
{context}

QUESTION: {query}

ANSWER (cite sources inline as [filename, p.N]):"""


REFUSAL_RESPONSE = (
    "I don't have sufficient information in the provided documents "
    "to answer this question confidently. Please upload relevant "
    "documents first."
)


def format_context(chunks: list) -> str:
    """Format retrieved chunks into a context string with source labels."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        filename = getattr(chunk, "source_filename", "") or "unknown"
        page = getattr(chunk, "page_number", 1)
        text = getattr(chunk, "text", "")
        parts.append(f"[Source {i}: {filename}, p.{page}]\n{text}")
    return "\n\n---\n\n".join(parts)


def build_grounded_prompt(query: str, chunks: list) -> str:
    """Build the full grounded prompt with context and query."""
    context = format_context(chunks)
    return GROUNDED_PROMPT.format(context=context, query=query)
