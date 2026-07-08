"""Typed structures for scraped mutual fund scheme records."""

from __future__ import annotations

from typing import Any, TypedDict


class AllocationItem(TypedDict):
    name: str
    percentage: float


class FaqItem(TypedDict):
    question: str
    answer: str


class SchemeRecord(TypedDict, total=False):
    id: str
    scheme_name: str
    fund_name: str
    groww_url: str
    scraped_at: str
    category: str
    sub_category: str
    super_category: str
    scheme_type: str
    plan_type: str
    description: str
    fund_objective: str
    nav: float | None
    nav_date: str | None
    aum: float | None
    expense_ratio: float | None
    exit_load: str | None
    risk_level: str | None
    fund_manager: str | None
    fund_manager_details: list[dict[str, Any]]
    holdings: list[dict[str, Any]]
    asset_allocation: dict[str, list[AllocationItem]]
    historical_returns: dict[str, Any]
    tax_information: dict[str, Any]
    faq_content: list[FaqItem]
    additional_text: dict[str, Any]
    investment_terms: dict[str, Any]
    amc_info: dict[str, Any]
    benchmark: str | None
    raw_sections: dict[str, Any]
