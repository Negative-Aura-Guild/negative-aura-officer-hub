# Building the Google Sites site

Google Sites is the officer-only front door. Each tab is just an embed of one GitHub Pages
page from this repo. ~20 minutes.

Prereq: [`SETUP.md`](SETUP.md) done, so the pages are live at
`https://cbarnesedu.github.io/negative-aura-officer-hub/`.

## 1. Create the site

1. Go to **https://sites.google.com** → **Blank** (＋).
2. Name it (top-left): `Negative Aura — Officers`. Set the header title too.
3. Optional: **Themes** (right panel) → pick a dark theme so it matches the embeds.

## 2. Add the pages

Right panel → **Pages** tab → hover the ＋ → **New page** for each:

- `Roster`
- `Loot Tracking`
- `Logs`
- `Recruitment`

(You can delete the default "Home" or point it at Roster.)

## 3. Embed a hub page on each Sites page

On each page, delete any placeholder text box, then:

1. Right panel → **Insert** → **Embed**.
2. Choose **Embed code** (not "By URL").
3. Paste, swapping `<name>` for `roster` / `loot` / `logs` / `recruitment`:

   ```html
   <iframe
     src="https://cbarnesedu.github.io/negative-aura-officer-hub/pages/<name>.html"
     width="100%" height="1400" style="border:0"
     loading="lazy"></iframe>
   ```

4. **Next** → **Insert**.
5. Drag the embed box to full width, and drag its bottom edge tall enough that the inner
   page doesn't scroll (Roster/Logs ≈ 1600; Recruitment ≈ 700). Adjust after publishing if
   there's a scrollbar or dead space.

| Sites page      | `<name>`      | suggested height |
|-----------------|---------------|------------------|
| Roster          | `roster`      | 1700 |
| Loot Tracking   | `loot`        | 1900 |
| Logs            | `logs`        | 1600 |
| Recruitment     | `recruitment` | 700  |

## 4. Lock it to officers

1. Top right → **Share** (person icon).
2. Under "Draft" and "Published", set access to **Specific people** and add each officer's
   Google account. (Or add a Google Group for officers and share with that.)
3. Do **not** set it to "Anyone with the link".

## 5. Publish

Top right → **Publish**. Pick a web address (e.g. `negative-aura-officers`). Confirm the
published-site audience matches step 4. Re-publish whenever you change the layout — the
embeds themselves update on their own whenever the data or pages change in this repo.

## Notes

- The GitHub Pages URLs are public. The access control is the Sites sharing + the fact the
  URLs aren't advertised. The data (roster, loot, public log links) isn't sensitive. If that
  changes later, we'd move to a private-repo Pages setup or a real auth proxy.
- If an embed shows a Google sign-in prompt instead of the loot sheet, the sheet tab isn't
  published yet — see [`SHEET-PUBLISH.md`](SHEET-PUBLISH.md).
