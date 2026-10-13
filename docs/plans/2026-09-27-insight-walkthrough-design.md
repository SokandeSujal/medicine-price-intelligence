# Insight Walkthrough and Analytical Chart Design

## Goal

Make every visualization self-explanatory to a non-technical evaluator. A new vertical Insights walkthrough reuses live chart components and follows each visual with a one-sentence orientation, a concrete finding, and an honest caveat where needed.

## New analytical evidence

1. **Formulation complexity versus typical price:** grouped bubble scatter of ingredient count and median non-outlier price, separated by severe-interaction flag. Bubble size represents medicine count.
2. **Manufacturer market position:** bubble scatter of product count versus non-outlier average price for manufacturers with at least 15 products. Bubble size represents salt breadth; median reference lines create volume/premium quadrants.
3. **Therapeutic-category price spread:** floating range bars for the 10th–90th percentile with a median marker, restricted to leading categories so extreme outliers do not dominate.

All three are computed by named SQL in `backend/queries.py` and exposed through dedicated FastAPI routes.

## Narrative pattern

Each block contains: plain title, large chart, “What you’re looking at,” bold “Key finding,” optional caveat, and SQL provenance. Existing visuals are reused rather than recreated.

## Copy standard

Page subtitles answer “why does this page exist?” in one sentence. Terms such as salt-adjusted premium, correlation, potential, outlier, and percentile are paired with plain-language explanations.
