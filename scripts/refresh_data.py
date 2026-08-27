#!/usr/bin/env python3
"""
Negative Aura - Officer Hub : data refresher
--------------------------------------------
Pulls live data from the wowutils / Viserio Cooldowns API and the WarcraftLogs
v1 API, normalizes it, and writes small JSON files into docs/data/ that the
static hub pages render. Run hourly by .github/workflows/refresh.yml.

stdlib only - no pip install.

Env:
    WOWUTILS_API_KEY   wowutils "wowutils_live_..." group key (Bearer)
    WCL_V1_API_KEY     WarcraftLogs API v1 key (32 hex chars)

Local run:
    WOWUTILS_API_KEY=... WCL_V1_API_KEY=... python scripts/refresh_data.py
"""

import csv
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# --- constants (not secret) ------------------------------------------------
WOWUTILS_BASE = "https://api.wowutils.com/v1"
WOWUTILS_GROUP_ID = "677479dbad9e549fd4ebb137"  # "Negative Aura" - real id, not the docs placeholder

WCL_V1_BASE = "https://www.warcraftlogs.com/v1"
WCL_GUILD_NAME = "Negative Aura"
WCL_GUILD_REALM = "Dalaran"
WCL_GUILD_REGION = "US"
WCL_GUILD_ID = 738983
WCL_GUILD_PAGE = f"https://www.warcraftlogs.com/guild/reports-list/{WCL_GUILD_ID}"

# Loot Tracker sheet, "Publish to web" token (Entire Document). CSV export per tab.
LOOT_PUB = ("https://docs.google.com/spreadsheets/d/e/"
            "2PACX-1vTmqucJwPzXkAxaFAaWTTki7gVEDRdQMziehVp6cWu6LwQqCKNspq6WRXxT_I8jr1MYHMcvh3by88Ly/pub")
LOOT_TABS = {"history": "1065887371", "tier": "625156953"}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "docs", "data")

USER_AGENT = "negative-aura-officer-hub/1.0 (+https://github.com/Negative-Aura-Guild/negative-aura-officer-hub)"


# --- tiny http helper ----------------------------------------------------------

def http_get_json(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def demojibake(value):
    """Best-effort repair of latin1<->utf8 double-encoding (e.g. 'DankyÃ¢' -> 'Dankyâ')."""
    if not isinstance(value, str) or "Ã" not in value:
        return value
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- wowutils fetchers -------------------------------------------------------

def wu_get(path, key, params=None):
    url = f"{WOWUTILS_BASE}/groups/{WOWUTILS_GROUP_ID}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return http_get_json(url, headers={"Authorization": f"Bearer {key}"})


def fetch_roster(key):
    raw = wu_get("/roster", key)
    members = []
    for m in raw.get("members", []):
        chars = []
        for c in sorted(m.get("characters", []), key=lambda c: c.get("order", 0)):
            chars.append({
                "name": demojibake(c.get("name", "")),
                "realm": c.get("realm"),
                "class": c.get("class", ""),
                "spec": c.get("spec", ""),
                "status": c.get("status", "alt"),
                "inactive": bool(c.get("inactive")),
            })
        main = next((c for c in chars if c["status"] == "main"), chars[0] if chars else None)
        members.append({
            "name": demojibake(m.get("displayName", "")),
            "battletag": m.get("battletag"),
            "rank": m.get("rank", "Raider"),
            "role": m.get("mainRole"),
            "main": main,
            "characters": chars,
        })
    role_order = {"tank": 0, "healer": 1, "melee": 2, "ranged": 3, None: 9}
    members.sort(key=lambda m: (role_order.get(m["role"], 9), m["name"].lower()))
    return {
        "memberCount": raw.get("memberCount", len(members)),
        "characterCount": raw.get("characterCount"),
        "members": members,
    }


def fetch_calendar(key):
    raw = wu_get("/calendar-events", key, {"upcoming": "true", "limit": 8})
    events = []
    for e in raw.get("data", []):
        counts = {}
        for s in e.get("signups", []):
            counts[s.get("status", "pending")] = counts.get(s.get("status", "pending"), 0) + 1
        events.append({
            "name": e.get("name"),
            "date": e.get("date"),
            "start": e.get("startTime"),
            "end": e.get("endTime"),
            "difficulty": e.get("difficulty"),
            "status": e.get("status"),
            "rosterSize": e.get("rosterSize"),
            "counts": counts,
        })
    return {"serverTimeZone": raw.get("serverTimeZone"), "events": events}


def fetch_droptimizers(key):
    raw = wu_get("/droptimizers", key)
    rows = []
    for d in raw.get("data", []):
        rows.append({
            "character": demojibake(d.get("characterName", "")),
            "class": d.get("characterClass", ""),
            "spec": d.get("characterSpec", ""),
            "profile": d.get("profileKey", ""),
            "dps": round(d.get("baselineDps", 0)) or None,
            "reportUrl": d.get("reportUrl"),
            "importedAt": d.get("importedAt"),
        })
    rows.sort(key=lambda r: r["importedAt"] or "", reverse=True)
    return {"data": rows}


def fetch_wishlists(key):
    """Known to 500 on the server side as of build time - caller records the status."""
    raw = wu_get("/wishlists", key)
    out = []
    for c in raw.get("data", []):
        out.append({
            "character": demojibake(c.get("characterName", "")),
            "class": c.get("characterClass", ""),
            "spec": c.get("characterSpec"),
            "selections": [
                {
                    "itemId": s.get("itemId"),
                    "slot": s.get("slot"),
                    "source": s.get("source"),
                    "priority": s.get("priority"),
                    "difficulty": s.get("difficulty"),
                    "note": s.get("note", ""),
                }
                for s in c.get("selections", [])
            ],
            "updatedAt": c.get("updatedAt"),
        })
    return {"data": out}


# --- warcraftlogs v1 fetchers ---------------------------------------------

def wcl_zone_map(key):
    try:
        zones = http_get_json(f"{WCL_V1_BASE}/zones?api_key={key}")
        return {z["id"]: z.get("name", f"Zone {z['id']}") for z in zones}
    except (urllib.error.URLError, ValueError, KeyError):
        return {}


def fetch_logs(key):
    gn = urllib.parse.quote(WCL_GUILD_NAME)
    gr = urllib.parse.quote(WCL_GUILD_REALM)
    url = f"{WCL_V1_BASE}/reports/guild/{gn}/{gr}/{WCL_GUILD_REGION}?api_key={key}"
    raw = http_get_json(url)
    zmap = wcl_zone_map(key)
    reports = []
    for r in raw:
        start, end = r.get("start", 0), r.get("end", 0)
        reports.append({
            "code": r.get("id"),
            "title": r.get("title", ""),
            "owner": r.get("owner", ""),
            "start": start,
            "end": end,
            "durationMin": round((end - start) / 60000) if end > start else None,
            "zoneId": r.get("zone"),
            "zone": zmap.get(r.get("zone"), None),
            "url": f"https://www.warcraftlogs.com/reports/{r.get('id')}",
        })
    reports.sort(key=lambda r: r["start"], reverse=True)
    return {"guildPage": WCL_GUILD_PAGE, "reports": reports[:25]}


# --- google sheet (published CSV) ------------------------------------------

def _fetch_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return [], []
    header = [h.strip() for h in rows[0]]
    width = max([len(header)] + [len(r) for r in rows[1:]] or [0])
    out = []
    for r in rows[1:]:
        if not any(cell.strip() for cell in r):
            continue
        out.append({(header[i] if i < len(header) and header[i] else f"col{i}"):
                    (r[i].strip() if i < len(r) else "") for i in range(width)})
    return header, out


def fetch_loot():
    result = {}
    for name, gid in LOOT_TABS.items():
        header, rows = _fetch_csv(f"{LOOT_PUB}?gid={gid}&single=true&output=csv")
        result[name] = rows
        result[name + "Cols"] = [h for h in header if h]
    return result


# --- write / diff --------------------------------------------------------------

def write_if_changed(name, payload):
    """Write docs/data/<name>.json only if the content differs. Returns True if written."""
    path = os.path.join(DATA_DIR, name + ".json")
    new = json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    old = None
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            old = f.read()
    if old == new:
        return False
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def main():
    wu_key = os.environ.get("WOWUTILS_API_KEY", "").strip()
    wcl_key = os.environ.get("WCL_V1_API_KEY", "").strip()
    if not wu_key:
        print("ERROR: WOWUTILS_API_KEY not set", file=sys.stderr)
    if not wcl_key:
        print("ERROR: WCL_V1_API_KEY not set", file=sys.stderr)

    jobs = [
        ("roster", lambda: fetch_roster(wu_key), bool(wu_key)),
        ("calendar", lambda: fetch_calendar(wu_key), bool(wu_key)),
        ("droptimizers", lambda: fetch_droptimizers(wu_key), bool(wu_key)),
        ("wishlists", lambda: fetch_wishlists(wu_key), bool(wu_key)),
        ("logs", lambda: fetch_logs(wcl_key), bool(wcl_key)),
        ("loot", fetch_loot, True),  # published Google Sheet CSV - no key needed
    ]

    sources = {}
    any_changed = False
    ok_count = 0
    for name, fn, enabled in jobs:
        if not enabled:
            sources[name] = "skipped:no-key"
            print(f"- {name}: skipped (no key)")
            continue
        try:
            payload = fn()
            changed = write_if_changed(name, payload)
            any_changed = any_changed or changed
            n = len(payload.get("members") or payload.get("events") or payload.get("data")
                    or payload.get("reports") or payload.get("history") or [])
            sources[name] = "ok"
            ok_count += 1
            print(f"- {name}: ok ({n} rows){' [changed]' if changed else ''}")
        except urllib.error.HTTPError as e:
            sources[name] = f"error:{e.code}"
            print(f"- {name}: HTTP {e.code} {e.reason}", file=sys.stderr)
        except (urllib.error.URLError, ValueError, TimeoutError) as e:
            sources[name] = f"error:{type(e).__name__}"
            print(f"- {name}: {e}", file=sys.stderr)

    # meta.json: only bump the timestamp when real data changed or statuses shifted
    meta_path = os.path.join(DATA_DIR, "meta.json")
    prev_sources = {}
    prev_generated = None
    if os.path.isfile(meta_path):
        try:
            prev = json.load(open(meta_path, encoding="utf-8"))
            prev_sources = prev.get("sources", {})
            prev_generated = prev.get("generatedAt")
        except (ValueError, OSError):
            pass

    if any_changed or sources != prev_sources or not prev_generated:
        meta = {"generatedAt": now_iso(), "sources": sources}
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(meta, indent=1, sort_keys=True) + "\n")
        print(f"meta.json written (generatedAt={meta['generatedAt']})")
    else:
        print("no changes; meta.json left as-is")

    if ok_count == 0 and (wu_key or wcl_key):
        print("FATAL: every source failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
