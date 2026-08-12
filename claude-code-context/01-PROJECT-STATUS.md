# BBMR Drive Times Dashboard — Project Status

## What's Built
A real-time traffic display system showing drive times from three resort bases to four freeways.
Approved by Marketing (Figma: BBMR Traffic Signage | Resort 2025).

## Source of Truth
Figma file: `https://www.figma.com/design/UQYDS6haMR3MpVcFbXwk3I/BBMR-Traffic-Signage-%7C-Resort-2025?node-id=64-2767` (fileKey `UQYDS6haMR3MpVcFbXwk3I`, node `64:2767` = the "📍 Designs 12/23" canvas with all three resort frames). Adrian has connector access; usable via the Figma MCP tools when not rate-limited.

`Guidlines.png` (project root) is the authoritative written spec — the "BBMR In Resort Digital Signage" doc. Key points:
- Three standalone signs, one per resort (Bear Mountain, Snow Valley, Snow Summit); single-screen, landscape 16:9 1080p, readable from a distance; each sign uses its own brand fonts & colors.
- **Route labels are approved and must remain unchanged**, consistent across all three resorts:
  1. CA-210 via CA-18 Running Springs to CA-330
  2. CA-210 via CA-18 Running Springs
  3. **CA-10 via CA-38**
  4. CA-15 via CA-18 Lucerne Valley
- ⚠️ The Figma PNG mockups in `BBMR Traffic Signage 12/` show route 3 as "CA-210 via CA-38", which **contradicts** the approved labels above. The guidelines doc wins — the code uses CA-10. Don't "fix" the code to match those mockups; they appear to predate label approval. Worth flagging to Marketing so the Figma file gets corrected.
- ⚠️ The guidelines doc says traffic data refreshes at **5 min intervals** and references the **Google Routes API**. We're intentionally diverging on both: TomTom is the demo data source (per Adrian, unless Google becomes necessary), and polling is every 8 min to stay inside TomTom's free tier (see quota note below). Revisit if the spec is enforced or we move to Google.

## Current State (August 12, 2026)
- ✅ HTML/CSS/JS complete (matches Figma design)
- ✅ Poller script complete (all three origins, four routes each)
- ✅ nginx config ready
- ✅ Dedicated EC2 instance provisioned: **bbmr-drivetimes-prod** (i-057931b061ec907f1, IP 44.244.49.134, us-west-2b, t3.micro) — moved off the shared bbmr-web-ftp-prod box for reliability/ops control
- ✅ **Deployed and live** — nginx serving, all three base views (bearmountain/snowsummit/snowvalley) confirmed showing real TomTom drive times, no more sample-data fallback
- ✅ Fixed a feed-mapping bug found during deployment: `index.html`'s `CONFIG.bases` had `bearmountain` and `snowsummit` pointing at a `routes.json` file the poller never writes (only `snowvalley` was wired to the right file, `routes-sv.json`). Corrected to `routes-bm.json` / `routes-ss.json` in `deploy-new/index.html` and redeployed.
- ✅ **TomTom API key rotated** (Aug 12, 2026) — the exposed key was regenerated in the TomTom developer portal (Routing API scope) and the crontab updated; poller confirmed working with the new key, no auth errors
- ✅ **Operating window applied + polling tuned for TomTom's free tier** (Aug 12, 2026) — TomTom's Routing API free tier is 20,000 requests/month (confirmed via [docs.tomtom.com/pricing](https://docs.tomtom.com/pricing); overage returns HTTP 429, no surprise billing, per the [TomTom FAQ](https://docs.tomtom.com/platform/documentation/status-and-support/faqs)). The poller makes 9 calls/cycle (3 origins × 3 open routes; CA-10/r3 is a closed override, no call). At the old 24/7 + 5-min cadence that was ~77,760 calls/month (390% of quota — would have exhausted the month's quota in ~8 days). Now running 10am–6pm Pacific (`START_HOUR=10, END_HOUR=18` in `update_all.py`) with cron at `*/8 * * * *`: ~16,200/month on a 30-day month, ranging ~80-89% of quota across month lengths, never exceeding.
- ✅ **Added an on-screen schedule note** (Aug 12, 2026) — small caption under "Last updated" reading "Updates every 8 min · 10am–6pm PT", driven by `CONFIG.scheduleNote` in `index.html`. Keep this in sync by hand if `update_all.py`'s `START_HOUR`/`END_HOUR` or the crontab interval change later — it's not computed automatically from either.
- ⚠️ **Public IP changed** (2026-08-12) — instance was restarted, and with no Elastic IP attached the address moved from 44.244.49.134 to **52.40.27.71**, exactly the failure mode this bullet warned about. Elastic IP is now the top infra priority, not a someday-item.
- ⚠️ **Alterra's corporate network blocks bare-IP URLs** (discovered 2026-08-12, trying to verify the live site from a company machine) — both a browser and a plain `curl` from an Alterra-network host got Alterra's own "Web Page Blocked... Category: unknown" page for `http://52.40.27.71/...`. This means marketing reviewers on the corporate network likely can't open the "Live URLs" below either. A real DNS hostname (in addition to an Elastic IP) is probably necessary, not just nice-to-have — domains are far more likely to pass a categorization filter than a raw IP. May also need a FreshService ticket to get the address/domain allow-listed regardless.
- ⚠️ Previous POC on bbmr-web-ftp-prod (IP 16.144.132.248) is retired in favor of the new instance

## What Needs to Happen

### 1. Confirm coordinates (when confirmed from Google Maps)
- ✅ **All three origins confirmed and deployed** (2026-08-12), each at its parking lot:
  - Bear Mountain: **34.228479,-116.860377**
  - Snow Summit: **34.236555,-116.888996**
  - Snow Valley: **34.224625,-117.036427**
  - Not yet verified against a live poll cycle since all three were deployed outside the 10am–6pm window; will self-confirm at the next in-window run, or ask and I'll check the log
- ⚠️ **Freeway endpoints audited 2026-08-12 — all four `dest` values are off. No code changed; Adrian is confirming replacements in Google Maps.**
  Method: reverse-geocoded every `waypoints`/`dest` value (OSM Nominatim) and cross-checked against real freeway exit nodes (OSM Overpass).
  - ✅ **All four `waypoints` are correct** — each lands on the intended highway (CA-330 for r1, CA-18/Rim of the World for r2, CA-38 at Angelus Oaks for r3, CA-18 at Lucerne Valley for r4). No change needed.
  - ⚠️ r1 `dest` — sits on CA-330, **0.65 km short** of the I-210 junction
  - ⚠️ r2 `dest` — sits on N. Waterman Ave, **0.41 km past** the I-210 junction
  - ⚠️ r3 `dest` — sits on Orange St, **0.98 km short** of the I-10 junction
  - The three above are each well under a minute and get absorbed by `round5()`, so guests never see a difference. Decision (Adrian, 2026-08-12): **leave as-is.** They do bias slightly — r1/r3 understate, r2 overstates.
  - 🔴 r4 `dest` (`34.416300,-117.301700`) — **lands on no road at all**, in open desert in Hesperia, **7.5–9.7 km** from any I-15 junction. This is a real error, not rounding noise: the live feed is currently reporting an 85-minute drive time measured to this empty-desert point. Two candidate endpoints were verified as actually being on I-15:
    - I-15 × Bear Valley Rd (exit 143) = `34.4231,-117.3830` — the usual Apple Valley approach, and nearest to what the current coordinate seems to have been aiming at
    - I-15 × Main St, Hesperia (exit 141) = `34.3960,-117.4047`
    - (A third option is the literal CA-18 × I-15 junction in Victorville, ~`34.536,-117.292`, which is a longer drive and would need its exact node verified.)

### 2. Fonts — code side done, waiting on the files
**The @font-face rules are already wired into `index.html`** (2026-08-12) for all six weights the design actually uses. Nothing left to code — drop the files into `/var/www/drivetimes/fonts/` under the exact names in `deploy-new/fonts/README.txt` and they take effect on reload. Any missing file falls through silently to Bitter/Montserrat, so a partial drop is safe.

Searched SharePoint, the local disk, and installed Windows fonts on 2026-08-12 — **no Gelica or Proxima Nova files exist anywhere yet**, so this is genuinely blocked on Marketing/brand supplying them. `.woff2` preferred, `.otf` also accepted (both are listed as sources).

⚠️ When the fonts land, re-check the longest route label. "via CA-18 Running Springs to CA-330" currently **wraps to two lines** because it needs 620px in a 560px slot. This is pre-existing (it wraps identically at the old 47px icon width — verified, not caused by the icon change) and is purely a fallback-font artifact: Bitter runs wider than Gelica, and the label fits on one line in the Figma design. It should self-resolve once Gelica is installed.

### 3. Logos — ✅ done properly (2026-08-12), via the Figma connector
Got real access to the Figma file (`UQYDS6haMR3MpVcFbXwk3I`, node `64:2767`) after Adrian shared the URL. Pulled true assets instead of the earlier PNG crops:
- `bear-mountain.svg`, `snow-summit.svg` — genuine vector exports (extracted the `Primary Logo` component group from Figma's flattened export, stripping the ancestor frame/canvas background rects that came along with it)
- `snow-valley.png` — Snow Valley's logo is raster *in Figma itself* (a rounded-rect with an image fill, no vector layer exists), so this is the original high-res source image (1280×823, real alpha transparency) rather than a crop — much better than the earlier crop but still raster by nature of the source.
- All three confirmed serving (HTTP 200) and rendering (not the text-fallback path) on the live site.
- `CONFIG.bases[*].logo` in both `index.html` copies updated accordingly (`.svg` for Bear Mountain/Snow Summit, `.png` for Snow Valley).

### 4. Status icons — ✅ fixed 2026-08-12 (not yet deployed)
Replaced the placeholder squiggles with the real winding-road glyph. The Figma MCP connector was **still rate-limited** (View seat, Enterprise plan — hit the cap again on this attempt), so rather than keep waiting, the icon was traced pixel-accurately from the approved mockup `BBMR Traffic Signage 12/Bear Mountain.png`, which contains all three states at 1:1.

How it was derived (so it can be re-verified or redone): the icon occupies exactly **53×47 px** at 1920×1080 (x 38–90, y 196–242). Per-row weighted centroids of the dark pixels gave the two road-edge centerlines and the three centerline dashes; stroke width measures **2.5**, and the badge is a circle at **cx 44.5, cy 8.5, r 8.5**. Correctness was confirmed by overlaying the new SVG on the mockup crop at 14× — the two align symmetrically.

Two things the old code got wrong beyond the shape:
- The stale comment claimed the badge shows "steam-lines / triangle / check". It does **not** — the badge glyph is an **exclamation mark in all three states**, including green/Normal. Only the badge *colour* changes.
- All four `ICONS` entries were the same squiggle recoloured. Since only the badge colour varies, `ICONS` is now built from a single `roadIcon(badge)` helper instead of four near-duplicate SVG strings.

Colours came out exactly matching the existing CSS variables (`#f68c42` / `#ea1609` / `#2b8028`), and the road stroke is `--ink` `#252525`.

Also widened `.status-icon` from 47px to 53px to match the icon's true aspect ratio. (Verified this did **not** cause the long-label wrap noted in §2 — that wraps at both widths.)

The separate `PILL_ICONS` (warning triangle / check circle in the "Traffic: …" pill) were already correct and are unchanged — the pill *does* use a check for Normal.

### 5. Elastic IP — ⚠️ still open, needs doing from the AWS console
Not actionable from Adrian's laptop: **no AWS CLI and no credentials are installed there** (checked 2026-08-12). Do it in the console, or from a machine with credentials:

1. EC2 → Elastic IPs → **Allocate Elastic IP address** (region **us-west-2**)
2. Associate it with instance **i-057931b061ec907f1** (`bbmr-drivetimes-prod`)

⚠️ **Associating an EIP replaces the instance's current public IP.** `44.244.49.134` stops working the moment it's attached, and all three marketing URLs change to the new address. Do this *before* the URLs are distributed widely, not after — that's the whole reason it's on the list.

Two notes:
- Cost is a wash while it's attached. AWS bills all public IPv4 the same (~$3.60/mo) since Feb 2024, so an EIP costs no more than the auto-assigned IP it replaces. An EIP left allocated but **not** attached to a running instance does get billed, so don't allocate one and leave it idle.
- `drivetimes.nginx.conf` used to pin `server_name 16.144.132.248` — the *old, retired* instance. Changed to `server_name _` (catch-all) on 2026-08-12 so the IP swap needs no nginx edit. Harmless either way given `default_server`, but it was actively misleading.

Longer term a DNS name pointed at the EIP would beat handing Marketing a bare IP at all.

## ⏳ Not yet deployed
`index.html` changes from 2026-08-12 (status icons §4, @font-face rules §2) are **local only** — the live box still serves the previous 13,488-byte copy. Both local copies are in sync with each other; upload `deploy-new/index.html` to `/var/www/drivetimes/` to publish. The nginx `server_name` change also needs its file copied and `sudo nginx -t && sudo systemctl reload nginx`.

## Live URLs (for marketing)
Live now on bbmr-drivetimes-prod:
- http://44.244.49.134/?base=bearmountain
- http://44.244.49.134/?base=snowsummit
- http://44.244.49.134/?base=snowvalley

## Files in This Folder

- `../Guidlines.png` (project root) — **the authoritative spec**; see Source of Truth above
- `../BBMR Traffic Signage 12/` (project root) — Figma mockup exports, one 1920×1080 PNG per resort; logos were cropped from these. Note the route-label discrepancy called out above.
- `preview-bearmountain.png` — The approved design rendered
- `index.html` — Display HTML/CSS/JS (kept in sync with `deploy-new/index.html`, but `deploy-new/` is the one actually deployed)
- `deploy-new/` folder:
  - `index.html` — Deployed copy; feed mapping fixed 2026-08-12 (was pointing bearmountain/snowsummit at a non-existent `routes.json`)
  - `update_all.py` — The poller script; switched from 24/7 POC mode to the 10am-6pm production window on 2026-08-12 (see quota note above)
  - `drivetimes.nginx.conf` — nginx config; `server_name` switched to the `_` catch-all 2026-08-12 (was pinned to the retired instance's IP)
  - `logos/` — the three deployed logos: `bear-mountain.svg` and `snow-summit.svg` (real vector exports from Figma), `snow-valley.png` (Figma's original raster source — no vector exists for this one)
  - `fonts/` — empty except `README.txt`, which lists the exact filenames the `@font-face` rules expect. Drop the licensed fonts here (see §2)
