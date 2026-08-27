# Setup — Officer Hub

One-time. ~15 minutes.

## 1. GitHub repo secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**. Add two:

| Name | Value |
|------|-------|
| `WOWUTILS_API_KEY` | your wowutils group key, starts with `wowutils_live_…` |
| `WCL_V1_API_KEY`   | your WarcraftLogs **API v1** key (32 hex characters) |

### Where those keys come from

**wowutils / Viserio Cooldowns** — in the group's **Settings → API Access** tab:
turn API sharing **on** (off by default), create a key (describe it, e.g. "Negative Aura
officer hub"), copy it immediately — it's shown once. The hub only ever does GET requests.

**WarcraftLogs** — the current key is a **v1** key. v1 still works but is deprecated
(see step 4). Get/regenerate it from your WarcraftLogs account settings.

## 2. Enable GitHub Pages

Repo → **Settings → Pages**:
- **Source:** Deploy from a branch
- **Branch:** `main`, folder **`/docs`** → Save

After a minute the site is at
`https://cbarnesedu.github.io/negative-aura-officer-hub/`.

## 3. Run the data refresh once

Repo → **Actions → "Refresh hub data" → Run workflow**. It fetches the APIs, writes
`docs/data/*.json`, and commits them. Confirm the run is green and open
`…/negative-aura-officer-hub/pages/roster.html` — you should see the live roster.

The workflow then re-runs hourly on its own.

## 4. Rotate the keys (do this after step 3)

Both keys were shared in plain text during setup. Regenerate them and update the two
secrets from step 1:

- **wowutils:** Group Settings → API Access → **Regenerate** (breaks the old key immediately).
  This key can *write* to the roster, so treat a leak as serious.
- **WarcraftLogs:** regenerate the v1 key in account settings.

## 5. (Later) Move WarcraftLogs to API v2

v1 is deprecated and will eventually be shut down. v2 uses OAuth2 client credentials:

1. warcraftlogs.com → your profile → **API Clients → Create Client**
   (name it, redirect URL `https://localhost` — unused).
2. You get a **Client ID** and **Client Secret**.
3. Add secrets `WCL_CLIENT_ID` and `WCL_CLIENT_SECRET`.
4. `scripts/refresh_data.py` → `fetch_logs()` gets a `_fetch_logs_v2()` path:
   `POST https://www.warcraftlogs.com/oauth/token` (HTTP Basic `id:secret`,
   `grant_type=client_credentials`) → `POST https://www.warcraftlogs.com/api/v2/client`
   with the GraphQL query
   `{ reportData { reports(guildID: 738983, limit: 25) { data { code title startTime endTime zone { name } owner { name } } } } }`.
   Prefer v2 when its secrets are present, fall back to v1.
