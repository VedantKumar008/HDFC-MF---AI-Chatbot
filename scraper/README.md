# Scraper (Phase 1)

Extracts structured JSON for all approved HDFC Mutual Fund schemes from Groww scheme pages.

## How it works

1. Fetch each approved Groww URL with `httpx`
2. Parse embedded Next.js `__NEXT_DATA__` (`mfServerSideData`)
3. Extract supplementary HTML sections (tax, objective, fund house, etc.)
4. Derive asset allocation aggregates from holdings
5. Validate and write `data/schemes/<scheme-id>.json`

## Run

From project root:

```powershell
.\scripts\run-scraper.ps1
```

Scrape a single scheme:

```powershell
.\scripts\run-scraper.ps1 --scheme-id hdfc-defence-fund-direct-growth
```

Verify Phase 1 output:

```powershell
.\scripts\verify-phase1.ps1
```

## Output schema (high level)

Each JSON file includes:

- Scheme metadata (name, category, NAV, AUM, expense ratio, risk, exit load)
- Fund manager details and holdings
- Asset allocation (sector, nature, instrument, market cap)
- Historical returns and tax information
- FAQ / analysis content and additional page text
- Original `groww_url` and `scraped_at` timestamp

## Design notes

- Polite delay between requests (default 1.5s)
- Failed schemes do not overwrite existing JSON
- Successful writes use atomic temp-file replacement
- Required fields are validated before persistence
