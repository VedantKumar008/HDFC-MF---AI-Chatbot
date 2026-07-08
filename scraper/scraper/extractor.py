"""Normalize Groww payloads into project scheme records."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from .models import AllocationItem, FaqItem, SchemeRecord


def build_scheme_record(
    scheme_id: str,
    groww_url: str,
    mf_data: dict[str, Any],
    html_sections: dict[str, str],
) -> SchemeRecord:
    holdings = _normalize_holdings(mf_data.get("holdings") or [])
    category_info = mf_data.get("category_info") or {}

    record: SchemeRecord = {
        "id": scheme_id,
        "scheme_name": _as_str(mf_data.get("scheme_name")) or _as_str(mf_data.get("fund_name")),
        "fund_name": _as_str(mf_data.get("fund_name")),
        "groww_url": groww_url,
        "scraped_at": datetime.now(UTC).isoformat(),
        "category": _as_str(mf_data.get("category")),
        "sub_category": _as_str(mf_data.get("sub_category")),
        "super_category": _as_str(mf_data.get("super_category")),
        "scheme_type": _as_str(mf_data.get("scheme_type")),
        "plan_type": _as_str(mf_data.get("plan_type")),
        "description": _as_str(mf_data.get("description")),
        "fund_objective": _as_str(mf_data.get("description"))
        or html_sections.get("investment_objective", ""),
        "nav": _as_float(mf_data.get("nav")),
        "nav_date": _as_str(mf_data.get("nav_date")),
        "aum": _as_float(mf_data.get("aum")),
        "expense_ratio": _as_float(mf_data.get("expense_ratio")),
        "exit_load": _as_str(mf_data.get("exit_load")),
        "risk_level": _as_str(mf_data.get("nfo_risk")),
        "fund_manager": _as_str(mf_data.get("fund_manager")),
        "fund_manager_details": _normalize_fund_managers(mf_data.get("fund_manager_details") or []),
        "holdings": holdings,
        "asset_allocation": _build_asset_allocation(holdings),
        "historical_returns": _build_historical_returns(mf_data),
        "tax_information": _build_tax_information(mf_data, html_sections),
        "faq_content": _build_faq_content(mf_data, html_sections),
        "additional_text": _build_additional_text(mf_data, html_sections),
        "investment_terms": _build_investment_terms(mf_data),
        "amc_info": mf_data.get("amc_info") or {},
        "benchmark": _as_str(mf_data.get("benchmark_name")) or _as_str(mf_data.get("benchmark")),
        "raw_sections": {
            "analysis": mf_data.get("analysis") or [],
            "category_info": category_info,
            "historic_fund_expense": _trim_list(mf_data.get("historic_fund_expense"), 24),
            "fund_news": mf_data.get("fund_news"),
            "peer_comparison": mf_data.get("peerComparison") or [],
        },
    }
    return record


def _build_asset_allocation(holdings: list[dict[str, Any]]) -> dict[str, list[AllocationItem]]:
    return {
        "by_sector": _aggregate_holdings(holdings, "sector_name"),
        "by_nature": _aggregate_holdings(holdings, "nature_name"),
        "by_instrument": _aggregate_holdings(holdings, "instrument_name"),
        "by_market_cap": _aggregate_holdings(holdings, "market_cap"),
    }


def _aggregate_holdings(holdings: list[dict[str, Any]], field: str) -> list[AllocationItem]:
    totals: dict[str, float] = defaultdict(float)
    for holding in holdings:
        label = _as_str(holding.get(field)) or "Unspecified"
        percentage = _as_float(holding.get("corpus_per"))
        if percentage is None:
            continue
        totals[label] += percentage

    items = [
        {"name": name, "percentage": round(percentage, 4)}
        for name, percentage in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]
    return items


def _build_historical_returns(mf_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "simple_return": mf_data.get("simple_return") or {},
        "sip_return": mf_data.get("sip_return") or {},
        "return_stats": mf_data.get("return_stats") or [],
        "stats": mf_data.get("stats") or [],
        "portfolio_turnover": _as_float(mf_data.get("portfolio_turnover")),
        "historic_fund_expense": _trim_list(mf_data.get("historic_fund_expense"), 12),
    }


def _build_tax_information(mf_data: dict[str, Any], html_sections: dict[str, str]) -> dict[str, Any]:
    category_info = mf_data.get("category_info") or {}
    return {
        "tax_impact": _as_str(category_info.get("tax_impact")),
        "category_description": _as_str(category_info.get("description")),
        "stamp_duty": _as_str(mf_data.get("stamp_duty")),
        "exit_load": _as_str(mf_data.get("exit_load")),
        "historic_exit_loads": mf_data.get("historic_exit_loads") or [],
        "html_tax_implication": html_sections.get("tax_implication", ""),
        "html_exit_tax_section": html_sections.get("exit_tax_section", ""),
    }


def _build_faq_content(mf_data: dict[str, Any], html_sections: dict[str, str]) -> list[FaqItem]:
    faq_items: list[FaqItem] = []

    analysis = mf_data.get("analysis") or []
    for item in analysis:
        question = _as_str(item.get("analysis_subject"))
        answer = _as_str(item.get("analysis_desc"))
        if question and answer:
            faq_items.append({"question": question, "answer": answer})

    understand_terms = html_sections.get("understand_terms", "")
    if understand_terms:
        faq_items.append(
            {
                "question": "Understand terms",
                "answer": understand_terms,
            }
        )

    return faq_items


def _build_additional_text(mf_data: dict[str, Any], html_sections: dict[str, str]) -> dict[str, Any]:
    return {
        "about": html_sections.get("about", ""),
        "investment_objective": html_sections.get("investment_objective", ""),
        "fund_house_section": html_sections.get("fund_house", ""),
        "fund_management_section": html_sections.get("fund_management", ""),
        "minimum_investments_section": html_sections.get("minimum_investments", ""),
        "returns_and_rankings_section": html_sections.get("returns_and_rankings", ""),
        "meta_description": _as_str(mf_data.get("meta_desc")),
        "category_helper_text": _as_str((mf_data.get("category_info") or {}).get("category_helper_text")),
        "blocked_reason": _as_str(mf_data.get("blocked_reason")),
        "brochure_link": _as_str(mf_data.get("brochure_link")),
        "scheme_info_link": _as_str(mf_data.get("scheme_info_link")),
        "sid_url": _as_str(mf_data.get("sid_url")),
    }


def _build_investment_terms(mf_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "min_investment_amount": _as_float(mf_data.get("min_investment_amount")),
        "min_sip_investment": _as_float(mf_data.get("min_sip_investment")),
        "max_sip_investment": _as_float(mf_data.get("max_sip_investment")),
        "min_withdrawal": _as_float(mf_data.get("min_withdrawal")),
        "sip_allowed": mf_data.get("sip_allowed"),
        "lumpsum_allowed": mf_data.get("lumpsum_allowed"),
        "lock_in": mf_data.get("lock_in") or {},
        "launch_date": _as_str(mf_data.get("launch_date")),
        "isin": _as_str(mf_data.get("isin")),
        "plan_type": _as_str(mf_data.get("plan_type")),
        "additional_details": mf_data.get("additional_details") or {},
    }


def _normalize_holdings(holdings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for holding in holdings:
        normalized.append(
            {
                "company_name": _as_str(holding.get("company_name")),
                "sector_name": _as_str(holding.get("sector_name")),
                "nature_name": _as_str(holding.get("nature_name")),
                "instrument_name": _as_str(holding.get("instrument_name")),
                "rating": _as_str(holding.get("rating")),
                "corpus_per": _as_float(holding.get("corpus_per")),
                "market_cap": _as_str(holding.get("market_cap")),
                "portfolio_date": _as_str(holding.get("portfolio_date")),
            }
        )
    return normalized


def _normalize_fund_managers(managers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for manager in managers:
        normalized.append(
            {
                "person_name": _as_str(manager.get("person_name")),
                "education": _as_str(manager.get("education")),
                "experience": _as_str(manager.get("experience")),
                "date_from": _as_str(manager.get("date_from")),
                "funds_managed": manager.get("funds_managed") or [],
            }
        )
    return normalized


def _trim_list(value: Any, max_items: int) -> list[Any]:
    if not isinstance(value, list):
        return []
    return value[:max_items]


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
