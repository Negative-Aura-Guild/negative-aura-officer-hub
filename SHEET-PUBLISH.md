# Publishing the loot sheet tab(s)

The **Loot Tracking** page embeds the loot-tracker Google Sheet in an `<iframe>`. For that
to render for everyone (instead of "This document is not published"), the tab has to be
**Published to web**.

## Steps

1. Open **Negative Aura – Loot Tracker**
   (`https://docs.google.com/spreadsheets/d/1ZNf-uSfHsBAYue-KOxItRnPwAHpT1OAYGkTvOJyG7g0/edit`).
2. **File → Share → Publish to web**.
3. In the dialog:
   - Left dropdown: pick the specific tab (e.g. **Loot History**, or **Tier Tracker**) — not
     "Entire document".
   - Right dropdown: **Web page**.
   - **Publish** → confirm.
4. Repeat step 2–3 for the second tab if you want both.

## What this exposes

A published tab is viewable by **anyone with the link** (it does not expose the rest of the
spreadsheet, and it's read-only). You approved this. To undo later: same dialog → **Stop
publishing**.

## Wiring it into the page

Open `docs/pages/loot.html` and edit the `TABS` array near the top of the `<script>`:

```js
var TABS = [
  { label: "Loot History", gid: "625156953", height: 620 },
  { label: "Tier Tracker", gid: "PUT_THE_OTHER_GID_HERE", height: 520 }
];
```

The **gid** is the number after `gid=` in the tab's URL when you click that tab in the
sheet. `625156953` is the one from the link you sent — confirm it's the tab you actually
want by opening
`https://docs.google.com/spreadsheets/d/1ZNf-uSfHsBAYue-KOxItRnPwAHpT1OAYGkTvOJyG7g0/edit#gid=625156953`.

Commit the change; GitHub Pages redeploys automatically.
