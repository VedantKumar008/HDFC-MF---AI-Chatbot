"""Prompt templates and canned responses for the RAG pipeline."""

from __future__ import annotations

import re

NOT_FOUND_MESSAGE = (
    "I could not find that information within my supported HDFC Mutual Fund dataset."
)

SYSTEM_PROMPT = """You are the HDFC Mutual Fund AI Assistant.

Your role is to provide factual information about supported HDFC Mutual Fund schemes using ONLY the context supplied below.

Rules:
- Answer only from the provided context. Do not use outside knowledge.
- If the context does not contain enough information, respond exactly with:
  "I could not find that information within my supported HDFC Mutual Fund dataset."
- Do not provide investment advice, buy/sell recommendations, SIP suggestions, portfolio guidance, or suitability assessments.
- For comparisons, state factual differences only. Do not declare a winner or recommend one fund over another.
- Use clear markdown formatting when helpful (lists, bold labels, short paragraphs).
- Do not add source citations or footnotes in the response.
- Be concise, accurate, and neutral.
- When the user uses pronouns (it, its, this, that, etc.), resolve them to the most recently mentioned HDFC Mutual Fund scheme from the conversation history.
- Maintain context across conversation turns to provide coherent multi-turn responses.
"""


# List of HDFC Mutual Fund scheme names for extraction (matching actual data)
SCHEME_NAMES = [
    "HDFC Banking and PSU Debt Fund",
    "HDFC BSE Sensex Index Fund",
    "HDFC Defence Fund",
    "HDFC Dividend Yield Fund",
    "HDFC ELSS Tax Saver Fund",
    "HDFC Equity Fund",
    "HDFC Gold ETF Fund of Fund",
    "HDFC Large and Mid Cap Fund",
    "HDFC Large Cap Fund",
    "HDFC Long Duration Debt Fund",
    "HDFC Medium Term Debt Fund",
    "HDFC Mid Cap Fund",
    "HDFC Monthly Income Plan Long Term Plan",
    "HDFC Multi Cap Fund",
    "HDFC Nifty 50 Index Fund",
    "HDFC Nifty LargeMidCap 250 Index Fund",
    "HDFC Nifty Midcap 150 Index Fund",
    "HDFC Nifty Smallcap 250 Index Fund",
    "HDFC Retirement Savings Fund Equity Plan",
    "HDFC Short Term Opportunities Fund",
    "HDFC Silver ETF FOF",
]


def extract_scheme_name(text: str) -> str | None:
    """Extract HDFC Mutual Fund scheme name from text."""
    import logging
    logger = logging.getLogger(__name__)
    
    for scheme in SCHEME_NAMES:
        if scheme.lower() in text.lower():
            logger.info(f"Extracted scheme name: {scheme} from text: {text}")
            return scheme
    logger.info(f"No scheme name found in text: {text}")
    return None


def enhance_query_with_context(
    query: str, history: list[dict[str, str]] | None = None
) -> str:
    """Enhance query with context from conversation history for pronoun resolution."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Enhancing query: {query}")
    logger.info(f"History length: {len(history) if history else 0}")
    
    if not history:
        logger.info("No history provided, returning original query")
        return query

    # Pronouns and ambiguous references to detect
    ambiguous_patterns = [
        r"\bits\b",
        r"\bits\b",
        r"\bthis\b",
        r"\bthat\b",
        r"\bthis fund\b",
        r"\bthat fund\b",
        r"\bthis scheme\b",
        r"\bthat scheme\b",
        r"\bthe fund\b",
        r"\bthe scheme\b",
    ]

    # Check if query contains ambiguous references
    has_ambiguous = any(re.search(pattern, query, re.IGNORECASE) for pattern in ambiguous_patterns)
    logger.info(f"Has ambiguous references: {has_ambiguous}")

    if not has_ambiguous:
        logger.info("No ambiguous references, returning original query")
        return query

    # Look for most recently mentioned scheme in conversation history
    logger.info("Searching conversation history for scheme names...")
    for i, msg in enumerate(reversed(history)):
        logger.info(f"History message {i}: role={msg['role']}, content={msg['content'][:100]}")
        if msg["role"] == "user":
            scheme = extract_scheme_name(msg["content"])
            if scheme:
                # Prepend scheme name to query for better retrieval
                enhanced = f"{scheme} {query}"
                logger.info(f"Enhanced query: {enhanced}")
                return enhanced

    logger.info("No scheme found in history, returning original query")
    return query


def build_user_prompt(query: str, context: str) -> str:
    return f"""Use the context below to answer the user's question.

Context:
{context}

User question:
{query}
"""
