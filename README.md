# Negative Aura — Officer Hub

One place for the guild's officer data: **Roster**, **Loot Tracking**, **Logs**, and
(later) **Recruitment**. Sibling project to
[`negative-aura-loot-tracker`](https://github.com/cbarnesedu/negative-aura-loot-tracker).

## How it works

```
wowutils / Viserio Cooldowns API ─┐
WarcraftLogs API v1 ──────────────┤→  scripts/refresh_data.py  →  docs/data/*.json
                                  │        (hourly GitHub Action)
                                  ▼
                        docs/  (static pages)  →  GitHub Pages
                                  ▼
                     embedded as tabs in a Google Sites site
                         (officer-only Google sign-in)
```

- **No build step, no framework.** `docs/` is plain HTML/CSS/JS served straight by GitHub Pages.
- **`scripts/refresh_data.py`** (stdlib only) pulls live data every hour via
  `.github/workflows/refresh.yml` and commits the small JSON files in `docs/data/` when they change.
- **Google Sites** is just the front door — each tab is an `<iframe>` embed of one page here.
  It provides the officer-only access control; the GitHub Pages URLs themselves are public
  (the data — guild roster, loot, public log links — is not sensitive).

## Pages

| Page | Source | Notes |
|------|--------|-------|
| `docs/pages/roster.html` | wowutils `/roster` | Raiders grouped by role, mains + alts, class colors |
| `docs/pages/loot.html` | Google Sheet embed + wowutils `/droptimizers` + `/wishlists` | Sheet = the loot-tracker sheet; wishlists currently disabled (wowutils API returns 500) |
| `docs/pages/logs.html` | WarcraftLogs v1 guild reports | Recent reports, links to WarcraftLogs |
| `docs/pages/recruitment.html` | — | Placeholder until the Discord integration is built |
| `docs/index.html` | `/calendar-events` | Landing page + next raid nights |

## Setup

1. **[`SETUP.md`](SETUP.md)** — GitHub secrets, enable Pages, key rotation, WCL v2 migration.
2. **[`SHEET-PUBLISH.md`](SHEET-PUBLISH.md)** — publish the loot sheet tab(s) so the embed renders.
3. **[`GOOGLE-SITES.md`](GOOGLE-SITES.md)** — build the Sites site and lock it to officers.

## Local development

```
cd docs
python -m http.server 8777
# open http://localhost:8777/
```

Regenerate the data files locally:

```
WOWUTILS_API_KEY=... WCL_V1_API_KEY=... python scripts/refresh_data.py
```

## Constants (not secret)

- wowutils group ID: `677479dbad9e549fd4ebb137` ("Negative Aura")
- WarcraftLogs guild: **Negative Aura** / **Dalaran** / **US** (guild id `738983`)
- Loot Tracker sheet: `1ZNf-uSfHsBAYue-KOxItRnPwAHpT1OAYGkTvOJyG7g0`

These live in `scripts/refresh_data.py` and the page files.
