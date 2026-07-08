"""Convert scraped scheme JSON files into retrieval chunks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ChunkRecord

HOLDINGS_BATCH_SIZE = 12
MAX_TEXT_CHARS = 1800


def load_scheme_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def chunk_scheme_record(record: dict[str, Any], start_id: int) -> list[ChunkRecord]:
    scheme_id = str(record["id"])
    scheme_name = str(record.get("scheme_name") or record.get("fund_name") or scheme_id)
    scheme_url = str(record["groww_url"])
    scraped_at = str(record.get("scraped_at") or "")

    base = {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "scheme_url": scheme_url,
        "scraped_at": scraped_at,
    }

    chunks: list[ChunkRecord] = []
    next_id = start_id

    def add_chunk(section: str, text: str) -> None:
        nonlocal next_id
        cleaned = _clean_text(text)
        if not cleaned:
            return
        header = f"[{scheme_name} | {section}]"
        for part in _split_long_text(cleaned, MAX_TEXT_CHARS):
            chunks.append(
                ChunkRecord(
                    chunk_id=next_id,
                    section=section,
                    text=f"{header}\n{part}",
                    **base,
                )
            )
            next_id += 1

    add_chunk("overview", _build_overview_text(record, scheme_name))
    add_chunk("fund_objective", _build_objective_text(record))
    add_chunk("fund_manager", _build_fund_manager_text(record, scheme_name))
    add_chunk("holdings", _build_holdings_text(record, scheme_name))
    add_chunk("asset_allocation", _build_asset_allocation_text(record, scheme_name))
    add_chunk("historical_returns", _build_returns_text(record, scheme_name))
    add_chunk("tax_information", _build_tax_text(record, scheme_name))
    add_chunk("investment_terms", _build_investment_terms_text(record, scheme_name))

    for faq in record.get("faq_content") or []:
        question = _as_str(faq.get("question"))
        answer = _as_str(faq.get("answer"))
        if question and answer:
            add_chunk("faq", f"Question: {question}\nAnswer: {answer}")

    additional_text = record.get("additional_text") or {}
    for section_name, content in additional_text.items():
        text = _as_str(content)
        if text:
            add_chunk(f"additional_{section_name}", f"{scheme_name} - {section_name}:\n{text}")

    return chunks


def chunk_scheme_files(scheme_files: list[Path]) -> list[ChunkRecord]:
    all_chunks: list[ChunkRecord] = []
    next_id = 0
    for path in sorted(scheme_files):
        record = load_scheme_json(path)
        scheme_chunks = chunk_scheme_record(record, next_id)
        all_chunks.extend(scheme_chunks)
        next_id = len(all_chunks)
    return all_chunks


def _build_overview_text(record: dict[str, Any], scheme_name: str) -> str:
    lines = [
        f"Scheme: {scheme_name}",
        f"Fund name: {_as_str(record.get('fund_name'))}",
        f"Category: {_as_str(record.get('category'))}",
        f"Sub-category: {_as_str(record.get('sub_category'))}",
        f"Plan type: {_as_str(record.get('plan_type'))}",
        f"Scheme type: {_as_str(record.get('scheme_type'))}",
        f"Benchmark: {_as_str(record.get('benchmark'))}",
        f"NAV: {_as_str(record.get('nav'))} (as of {_as_str(record.get('nav_date'))})",
        f"AUM: {_as_str(record.get('aum'))} Cr",
        f"Expense ratio: {_as_str(record.get('expense_ratio'))}%",
        f"Exit load: {_as_str(record.get('exit_load'))}",
        f"Risk level: {_as_str(record.get('risk_level'))}",
        f"Primary fund manager: {_as_str(record.get('fund_manager'))}",
    ]
    return "\n".join(line for line in lines if not line.endswith(": None") and not line.endswith(": "))


def _build_objective_text(record: dict[str, Any]) -> str:
    objective = _as_str(record.get("fund_objective")) or _as_str(record.get("description"))
    if not objective:
        return ""
    return f"Investment objective:\n{objective}"


def _build_fund_manager_text(record: dict[str, Any], scheme_name: str) -> str:
    managers = record.get("fund_manager_details") or []
    if not managers:
        manager = _as_str(record.get("fund_manager"))
        return f"Fund manager for {scheme_name}: {manager}" if manager else ""

    lines = [f"Fund managers for {scheme_name}:"]
    for manager in managers:
        name = _as_str(manager.get("person_name"))
        education = _as_str(manager.get("education"))
        experience = _as_str(manager.get("experience"))
        date_from = _as_str(manager.get("date_from"))
        if not name:
            continue
        lines.append(f"- {name} (since {date_from or 'N/A'})")
        if education:
            lines.append(f"  Education: {education}")
        if experience:
            lines.append(f"  Experience: {experience}")
    return "\n".join(lines)


def _build_holdings_text(record: dict[str, Any], scheme_name: str) -> str:
    holdings = record.get("holdings") or []
    if not holdings:
        return ""

    chunks: list[str] = []
    for batch_start in range(0, len(holdings), HOLDINGS_BATCH_SIZE):
        batch = holdings[batch_start : batch_start + HOLDINGS_BATCH_SIZE]
        lines = [f"Holdings for {scheme_name} (part {batch_start // HOLDINGS_BATCH_SIZE + 1}):"]
        for holding in batch:
            company = _as_str(holding.get("company_name"))
            sector = _as_str(holding.get("sector_name"))
            instrument = _as_str(holding.get("instrument_name"))
            corpus = holding.get("corpus_per")
            if not company:
                continue
            detail = f"- {company}"
            if corpus is not None:
                detail += f": {corpus}% of corpus"
            if sector:
                detail += f" | Sector: {sector}"
            if instrument:
                detail += f" | Instrument: {instrument}"
            lines.append(detail)
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks)


def _build_asset_allocation_text(record: dict[str, Any], scheme_name: str) -> str:
    allocation = record.get("asset_allocation") or {}
    if not allocation:
        return ""

    lines = [f"Asset allocation for {scheme_name}:"]
    for bucket_name, items in allocation.items():
        if not items:
            continue
        label = bucket_name.replace("_", " ").title()
        lines.append(f"{label}:")
        for item in items[:15]:
            name = _as_str(item.get("name"))
            percentage = item.get("percentage")
            if name is not None and percentage is not None:
                lines.append(f"- {name}: {percentage}%")
    return "\n".join(lines)


def _build_returns_text(record: dict[str, Any], scheme_name: str) -> str:
    returns = record.get("historical_returns") or {}
    lines = [f"Historical returns for {scheme_name}:"]

    simple = returns.get("simple_return") or {}
    return_labels = [
        ("return1d", "1 day"),
        ("return1w", "1 week"),
        ("return1m", "1 month"),
        ("return3m", "3 months"),
        ("return6m", "6 months"),
        ("return1y", "1 year"),
        ("return3y", "3 years"),
        ("return5y", "5 years"),
    ]
    lines.append("Simple returns:")
    for key, label in return_labels:
        value = simple.get(key)
        if value is not None:
            lines.append(f"- {label}: {round(float(value), 2)}%")

    sip = returns.get("sip_return") or {}
    if sip:
        lines.append("SIP returns:")
        for key, label in return_labels:
            value = sip.get(key)
            if value is not None:
                lines.append(f"- {label}: {round(float(value), 2)}%")

    for stat in returns.get("stats") or []:
        title = _as_str(stat.get("title"))
        if not title:
            continue
        lines.append(
            f"{title}: 1Y={stat.get('stat_1y')}, 3Y={stat.get('stat_3y')}, 5Y={stat.get('stat_5y')}"
        )

    turnover = returns.get("portfolio_turnover")
    if turnover is not None:
        lines.append(f"Portfolio turnover: {turnover}")

    return "\n".join(lines)


def _build_tax_text(record: dict[str, Any], scheme_name: str) -> str:
    tax = record.get("tax_information") or {}
    lines = [f"Tax and exit load information for {scheme_name}:"]
    mapping = [
        ("tax_impact", "Tax impact"),
        ("category_description", "Category tax description"),
        ("stamp_duty", "Stamp duty"),
        ("exit_load", "Exit load"),
        ("html_tax_implication", "Tax implication"),
        ("html_exit_tax_section", "Exit load and tax details"),
    ]
    for key, label in mapping:
        value = _as_str(tax.get(key))
        if value:
            lines.append(f"{label}: {value}")

    for item in tax.get("historic_exit_loads") or []:
        note = _as_str(item.get("note"))
        if note:
            lines.append(f"Historic exit load: {note}")

    return "\n".join(lines)


def _build_investment_terms_text(record: dict[str, Any], scheme_name: str) -> str:
    terms = record.get("investment_terms") or {}
    lines = [f"Investment terms for {scheme_name}:"]
    mapping = [
        ("min_investment_amount", "Minimum investment"),
        ("min_sip_investment", "Minimum SIP"),
        ("max_sip_investment", "Maximum SIP"),
        ("min_withdrawal", "Minimum withdrawal"),
        ("launch_date", "Launch date"),
        ("isin", "ISIN"),
        ("sip_allowed", "SIP allowed"),
        ("lumpsum_allowed", "Lumpsum allowed"),
    ]
    for key, label in mapping:
        value = terms.get(key)
        if value is not None and value != "":
            lines.append(f"{label}: {value}")

    lock_in = terms.get("lock_in") or {}
    if lock_in:
        lines.append(
            f"Lock-in: {lock_in.get('years', 0)} years, {lock_in.get('months', 0)} months, {lock_in.get('days', 0)} days"
        )

    return "\n".join(lines)


def _split_long_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    paragraphs = text.split("\n\n")
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            parts.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            for line in paragraph.split("\n"):
                line_candidate = f"{current}\n{line}".strip() if current else line
                if len(line_candidate) <= max_chars:
                    current = line_candidate
                else:
                    if current:
                        parts.append(current)
                    current = line
    if current:
        parts.append(current)
    return parts


def _clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.strip().splitlines() if line.strip())


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
