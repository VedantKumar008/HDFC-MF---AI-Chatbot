"""Compliance detector for Phase 5 - blocks investment advice and out-of-scope queries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ComplianceAction(Enum):
    """Action to take based on compliance check."""
    ALLOW = "allow"
    BLOCK_ADVICE = "block_advice"
    BLOCK_SCOPE = "block_scope"
    BLOCK_HALLUCINATION = "block_hallucination"


@dataclass
class ComplianceResult:
    """Result of compliance check."""
    action: ComplianceAction
    message: str | None = None
    reason: str | None = None


class ComplianceDetector:
    """Detects and blocks investment advice and out-of-scope queries."""
    
    # Investment advice patterns
    ADVICE_PATTERNS = [
        r"should i (invest|buy|sell|purchase)",
        r"recommend (a fund|which fund|best fund)",
        r"is (this|it) a good (investment|choice|option)",
        r"should i (start|stop|continue) (sip|investment)",
        r"(portfolio|retirement|financial) advice",
        r"which (fund|scheme) is (better|best|recommended)",
        r"tell me which to (invest|buy|choose)",
        r"is it (safe|risky) to invest",
        r"will this (grow|perform) well",
        r"(good|bad) time to (invest|buy|sell)",
    ]
    
    # Out-of-scope fund patterns (non-HDFC funds)
    SCOPE_PATTERNS = [
        r"\b(sbi|icici|axis|kotak|uti|tata|aditya birla|franklin|dsp|reliance|nippon|idfc|bandhan|motilal|quant)\s+(mutual fund|fund)\b",
        r"\b(sbi|icici|axis|kotak|uti|tata|aditya birla|franklin|dsp|reliance|nippon|idfc|bandhan|motilal|quant)\s+(small|mid|large|flexi|balanced|debt|equity)\b",
    ]
    
    # Standard refusal messages
    ADVICE_MESSAGE = "I cannot provide investment advice or recommendations. I can only share factual information about HDFC Mutual Fund schemes from my knowledge base."
    SCOPE_MESSAGE = "I can only provide information about the 21 approved HDFC Mutual Fund schemes in my knowledge base. I don't have data about other fund houses or schemes."
    HALLUCINATION_MESSAGE = "I could not find that information within my supported HDFC Mutual Fund dataset."
    
    def __init__(self):
        """Compile regex patterns for efficiency."""
        self.advice_regex = re.compile(
            "|".join(self.ADVICE_PATTERNS), 
            re.IGNORECASE
        )
        self.scope_regex = re.compile(
            "|".join(self.SCOPE_PATTERNS), 
            re.IGNORECASE
        )
    
    def check_query(self, query: str) -> ComplianceResult:
        """
        Check if query complies with safety rules.
        
        Args:
            query: User's query text
            
        Returns:
            ComplianceResult with action and optional message
        """
        query_lower = query.lower().strip()
        
        # Check for investment advice patterns
        if self.advice_regex.search(query):
            return ComplianceResult(
                action=ComplianceAction.BLOCK_ADVICE,
                message=self.ADVICE_MESSAGE,
                reason="Investment advice detected"
            )
        
        # Check for out-of-scope fund patterns
        if self.scope_regex.search(query):
            return ComplianceResult(
                action=ComplianceAction.BLOCK_SCOPE,
                message=self.SCOPE_MESSAGE,
                reason="Out-of-scope fund house detected"
            )
        
        # Query is allowed to proceed to RAG
        return ComplianceResult(
            action=ComplianceAction.ALLOW,
            reason="Query passes compliance checks"
        )
    
    def check_retrieval(self, has_context: bool, chunk_count: int = 0) -> ComplianceResult:
        """
        Check if retrieval results are sufficient for generation.
        
        Args:
            has_context: Whether relevant chunks were found
            chunk_count: Number of chunks retrieved
            
        Returns:
            ComplianceResult with action and optional message
        """
        if not has_context or chunk_count == 0:
            return ComplianceResult(
                action=ComplianceAction.BLOCK_HALLUCINATION,
                message=self.HALLUCINATION_MESSAGE,
                reason="No relevant chunks found in retrieval"
            )
        
        return ComplianceResult(
            action=ComplianceAction.ALLOW,
            reason="Sufficient context retrieved"
        )
