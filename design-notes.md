# Design notes — THE WORLD DAILY, Friday 20 November 2026

## Approach

Everything is procedural. `main.py` (Python 3.13, stdlib only: `math`, `os`,
`struct`, `zlib`) allocates a 1024×1024 RGB framebuffer, draws into it with a
handful of primitives, and encodes it as a PNG with its own chunk writer
(signature → IHDR (8-bit truecolor) → IDAT (`zlib` of filter-0 scanlines) →
IEND, each with a CRC-32). No fonts are loaded: the page is typeset with an
embedded 5×7 bitmap glyph table (A–Z, 0–9, and `: , . ' " - & + % : ; ! ? / ( ) * $`)
scaled ×1–×7 at draw time. No random, no clock: two runs produce byte-identical
files.

## Palette (fixed)

| role | hex | use |
|---|---|---|
| paper | `#f4eeda` | full-bleed newsprint ground, ticker text |
| ink | `#1c1a16` | masthead, headlines, card borders, pictogram bodies |
| crimson | `#b32b2b` | date line, kickers, lead kicker, arrows, accents |
| blue | `#2f4a6b` | card deks, lead summary line, ticker tags |

Four flat colors keep the file tiny (well under 1 MiB after zlib) and give the
crisp "pixel-editorial" look — everything sits on a strict integer-pixel grid.

## Layout (top → bottom)

1. **Masthead band** — hairline rule; folio row ("VOL. LXXXII - NO. 324",
   "( PRICE: ONE IMAGE )"); "THE WORLD DAILY" at 7× scale centered; the date
   "FRIDAY, 20 NOVEMBER 2026" in crimson at 3× (the page names its day twice —
   also in the bottom folio); thick-over-thin newspaper rules.
2. **Lead story** — crimson kicker (summit fall-out), two 3× headline lines
   (oil plunge on the pact's oil clause; EU calls a Sunday summit), two 2× dek
   lines (Brent sinks $4 to $58.10; Kyiv's "map for Russia" jibe), a blue 1×
   summary strip, and a column rule separating text from the pictogram: an oil
   barrel with a crimson falling arrow.
3. **Story grid (3×3)** — bordered 320×140 cards: crimson kicker with underline,
   44px pictogram, 2× headline (≤3 lines, ≤19 chars/line), 1× blue dek
   (≤2 lines, ≤47 chars/line). Order: CONGRESS (case folder with crimson seal —
   Epstein files subpoenas), BERLIN (euro sign with coins — €3bn Ukraine aid),
   GAZA (aid truck with cross — Cairo talks), MIDEAST (top-view fighter jet —
   Saudi strikes on Houthi sites), ASIA-PACIFIC (torii gate — Japan tightens
   Russia sanctions), CLIMATE (globe with crimson equator — COP31 in Turkey),
   SPORT (tennis ball — Sinner reaches Turin semis), SPACE (flaring sun — X6
   solar eruption), TECH (speech bubble — OpenAI delays GPT-6).
4. **Bottom band** — a tenth, full-height card on the left: OPINION (quill pen
   with crimson ink drop — an essay against co-signing the Shenzhen pact,
   tagged "ESSAY P.11"). On the right, a **BY THE NUMBERS** panel: crimson
   header over five 118×92 boxed figures, each with a hand-plotted mini chart —
   BRENT CRUDE $58.10 (descending sparkline), NIKKEI 225 51,204 (ascending
   sparkline), GAZA AID 120 (bar chart, final bar crimson), PERTH HEAT 41.2C
   (thermometer pegged high beside a sun), EU GAS STORES 88% (donut gauge,
   crimson sweep from 12 o'clock) — with blue source lines beneath. Below the
   OPINION card, bottom-aligned with the panel, sits a **WEATHER micro-panel**:
   a new sun-behind-cloud pictogram (crimson sun peeking from a puffy ink
   cloud) beside a crimson WEATHER tag and one 1× line of Friday readings —
   ROME 18C * LONDON 7C * SYDNEY 41C (Sydney echoes the Perth heat story).
5. **Ticker strip** — solid ink band with a paper-colored hippo silhouette
   (the paper's mascot) and four 1× bulletin items separated by asterisks
   (Anthropic day-two, Dhaka curfew, the Booker Prize, the Pete Rose
   Hall-of-Fame review).
6. **Folio** — "PAGE 01 - THE WORLD DAILY - FRIDAY, 20 NOVEMBER 2026"
   over closing rules.

## Editorial rationale

Every story is a *follow-on*, not a repeat of the 19 Nov front page: the
Shenzhen trilateral (day-after market and diplomatic fall-out), the Riyadh
drone strike (Saudi retaliation), the Gaza "yellow line" breach (Cairo talks to
rescue the ceasefire), Takaichi–Putin (Tokyo tightens sanctions), Anthropic's
debut (day two) and the Pete Rose pardon (Hall of Fame review). Fresh beats
cover Friday's natural news cycle: the Epstein-files subpoenas, Bundestag aid
vote, COP31's final 48 hours, ATP Finals round-robin climax in Turin, a solar
flare, and an AI-race launch slip. Copy is straight wire style: specific
places, numbers and names, no hype.

## Constraints check

- ≤ 1024×1024 px, ≤ 1 MiB PNG (truecolor + flat colors compress hard).
- Deterministic output, runs in well under a second, ~30 MB RAM.
- All copy is written as plausible reported news of the 20 Nov 2026 wire;
  continuing storylines of the 19 Nov front page, no repeated headlines.
