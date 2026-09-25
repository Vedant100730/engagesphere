# Design.md — EngageSphere

Visual design guidelines for the frontend dashboard.

## Theme
- Dark mode primary theme (consistent with the modern SaaS-dashboard look used in TrustTrail)
- Clean, minimal, data-forward — the dashboard's job is to make cross-platform feedback scannable at a glance

## Color Palette
- **Background:** near-black / deep charcoal (`#0B0E14` – `#0F1420` range)
- **Surface/cards:** slightly lighter dark panels (`#151A24` range) with soft borders
- **Primary accent:** blue-purple gradient (matching "EngageSphere" branding — sphere/connectivity concept), e.g. `#6366F1` to `#8B5CF6`
- **Sentiment colors:**
  - Positive: green (`#22C55E`)
  - Negative: red/rose (`#EF4444`)
  - Neutral: amber/yellow (`#F59E0B`)
- **Platform accent tags** (small identifying color per platform badge):
  - Google Maps: blue/red/yellow (Google brand-adjacent, muted)
  - Facebook: blue (`#1877F2` muted)
  - Instagram: gradient pink-orange (muted, used sparingly as an accent only)
  - Twitter/X: light blue/white-gray (muted)

## Typography
- Sans-serif throughout — Inter or similar system-UI font for readability
- Headings: semi-bold, slightly larger tracking for dashboard section titles
- Body/card text: regular weight, comfortable line-height for reading review/comment text
- Numbers/metrics (counts, percentages): bold, slightly larger, to draw attention in summary cards

## Layout Principles
- Top bar: logo + business name + key summary metrics (total feedback, avg sentiment, pending replies) — same pattern as TrustTrail's header
- Filter tabs directly below header: All / Google Maps / Facebook / Instagram / Twitter, plus sentiment filter (All/Positive/Negative/Neutral)
- Feedback feed: card-based grid, each card showing platform badge, author, original text (not truncated), sentiment tag, and the AI-generated reply with Approve/Edit actions
- Suggestions panel: separate section, clearly distinguished from the feed (e.g., highlighted background), each suggestion showing supporting quote(s) and cited best-practice source
- Charts: donut/pie for overall sentiment split, bar chart for per-platform feedback volume

## Interaction Notes
- Reply cards must show full original text — no silent truncation (a lesson carried over from TrustTrail's review-card bug)
- Approve/Edit/Reject actions should be immediately visible on each reply card, not hidden behind a menu
- Loading states for the ingestion pipeline should show per-platform progress (matches the multi-step loading pattern used in TrustTrail: Fetching → Classifying → Generating Replies → Suggestions)
- Mobile responsive: cards stack to single column, filter tabs become horizontally scrollable
