# Monochrome Product Overhaul

## Chosen direction

MedIntel becomes a restrained cobalt-blue healthcare intelligence product. Blue is the only decorative brand color, green means savings, red means clinical risk, and all other UI uses a warm neutral scale. A single soft 3D medicine composition anchors the overview; other pages use one oversized data point or focused tool as their hero moment.

## System

- 8pt spacing grid only: 8, 16, 24, 32, 40, 48, and 56px.
- Large 48–64px tabular figures, quiet uppercase labels, readable 14–16px body text.
- One Lucide outline icon family and one blue-tint icon badge treatment.
- Pill navigation and controls; 24px cards; custom scrollbars and custom selects.
- Framer Motion supplies shared page, card, row, KPI, and navigation transitions.
- Charts use one blue series color unless red/green has explicit semantic meaning.
- Every page promotes one hero region and demotes supporting detail.

## Page hierarchy

- Overview: narrative hero, 6,196-record count-up, transparent 3D medicine art, one dominant histogram, then compact secondary summaries.
- Finder: live search is the hero; medicine facts and alternatives appear only after selection.
- Manufacturers: company positioning and one premium percentage lead; stock signal is secondary.
- Savings: maximum saving percentage and interactive ranked comparison lead.
- Safety: 20.16% risk flag leads, with supporting distributions and subdued correlations.
- EDA: three concise findings lead into a compact preprocessing audit and heatmap.

All existing APIs and Supabase data remain unchanged.
