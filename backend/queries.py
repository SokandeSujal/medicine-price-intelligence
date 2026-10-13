"""Single source of truth for every SQL statement used by the application.

This module is intentionally presentation-friendly: each named query explains the
dashboard section it powers and the database concept it demonstrates.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Query:
    """A documented, named SQL statement exposed to routes and the debug page."""

    name: str
    section: str
    purpose: str
    sql: str


CREATE_SCHEMA = Query(
    "create_schema",
    "Data loader",
    "Creates the normalized relational schema and performance indexes. Foreign keys connect medicines to manufacturers and normalized side effects to medicines.",
    """
    CREATE TABLE IF NOT EXISTS manufacturers (
      id SERIAL PRIMARY KEY,
      name TEXT UNIQUE NOT NULL,
      product_count INT NOT NULL DEFAULT 0,
      avg_price NUMERIC(12,2),
      median_price NUMERIC(12,2)
    );
    CREATE TABLE IF NOT EXISTS medicines (
      id SERIAL PRIMARY KEY,
      product_name TEXT NOT NULL,
      sub_category TEXT,
      salt_composition TEXT,
      primary_salt TEXT,
      num_ingredients INT,
      price NUMERIC(12,2),
      is_price_outlier BOOLEAN NOT NULL DEFAULT FALSE,
      manufacturer_id INT REFERENCES manufacturers(id),
      medicine_desc TEXT,
      num_side_effects INT,
      num_interactions INT,
      has_life_threatening_interaction BOOLEAN NOT NULL DEFAULT FALSE
    );
    CREATE TABLE IF NOT EXISTS side_effects (
      id BIGSERIAL PRIMARY KEY,
      medicine_id INT NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
      side_effect_name TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_medicines_product_name ON medicines USING gin (to_tsvector('simple', product_name));
    CREATE INDEX IF NOT EXISTS idx_medicines_product_name_lower ON medicines (lower(product_name) text_pattern_ops);
    CREATE INDEX IF NOT EXISTS idx_medicines_primary_salt ON medicines (primary_salt);
    CREATE INDEX IF NOT EXISTS idx_medicines_manufacturer ON medicines (manufacturer_id);
    CREATE INDEX IF NOT EXISTS idx_medicines_price ON medicines (price);
    CREATE INDEX IF NOT EXISTS idx_side_effects_medicine ON side_effects (medicine_id);
    CREATE INDEX IF NOT EXISTS idx_side_effects_name ON side_effects (side_effect_name);
    """,
)

TRUNCATE_ALL = Query(
    "truncate_all", "Data loader", "Clears all three related tables in dependency-safe order for an explicit --replace reload.",
    "TRUNCATE TABLE side_effects, medicines, manufacturers RESTART IDENTITY CASCADE;",
)
COUNT_MEDICINES = Query(
    "count_medicines", "Data loader", "Prevents accidental duplicate loads by checking whether the target table already contains rows.",
    "SELECT COUNT(*) AS count FROM medicines;",
)
INSERT_MANUFACTURER = Query(
    "insert_manufacturer", "Data loader", "Upserts manufacturer-level aggregates computed from the cleaned source before medicine foreign keys are resolved.",
    """INSERT INTO manufacturers (name, product_count, avg_price, median_price)
       VALUES (%s, %s, %s, %s)
       ON CONFLICT (name) DO UPDATE SET product_count=EXCLUDED.product_count,
       avg_price=EXCLUDED.avg_price, median_price=EXCLUDED.median_price;""",
)
GET_MANUFACTURER_IDS = Query(
    "get_manufacturer_ids", "Data loader", "Maps natural manufacturer names to surrogate keys used by the medicines foreign key.",
    "SELECT id, name FROM manufacturers;",
)
INSERT_MEDICINE = Query(
    "insert_medicine", "Data loader", "Bulk-inserts cleaned medicine facts while preserving the normalized manufacturer relationship.",
    """INSERT INTO medicines (id, product_name, sub_category, salt_composition, primary_salt,
       num_ingredients, price, is_price_outlier, manufacturer_id, medicine_desc,
       num_side_effects, num_interactions, has_life_threatening_interaction)
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
)
SET_MEDICINE_SEQUENCE = Query(
    "set_medicine_sequence", "Data loader", "Advances the medicines identity sequence after deterministic bulk IDs are assigned, preserving safe future inserts.",
    "SELECT setval(pg_get_serial_sequence('medicines', 'id'), COALESCE(MAX(id), 1), true) FROM medicines;",
)
INSERT_SIDE_EFFECT = Query(
    "insert_side_effect", "Data loader", "Populates the one-to-many normalized side-effect rows linked to their inserted medicine.",
    "INSERT INTO side_effects (medicine_id, side_effect_name) VALUES (%s, %s);",
)

OVERVIEW_KPIS = Query(
    "overview_kpis",
    "Overview · KPI cards",
    "Uses scalar aggregate subqueries and DISTINCT counts to summarize medicine, manufacturer, salt, category, price, and severe-interaction coverage in one database round trip.",
    """
    SELECT COUNT(*)::int AS total_medicines,
      COUNT(DISTINCT manufacturer_id)::int AS total_manufacturers,
      COUNT(DISTINCT primary_salt)::int AS total_salts,
      COUNT(DISTINCT sub_category)::int AS total_categories,
      ROUND(AVG(price), 2)::float AS avg_price,
      PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::float AS median_price,
      ROUND(100.0 * COUNT(*) FILTER (WHERE has_life_threatening_interaction) / NULLIF(COUNT(*), 0), 2)::float AS life_threatening_pct
    FROM medicines;
    """,
)

PRICE_HISTOGRAM = Query(
    "price_histogram",
    "Overview · Price distribution",
    "Generates equal-width price buckets after excluding flagged outliers so the skewed price distribution remains interpretable; GROUP BY supplies counts per bucket.",
    """
    WITH bounds AS (SELECT MIN(price) lo, MAX(price) hi FROM medicines WHERE NOT is_price_outlier),
    bucketed AS (
      SELECT width_bucket(m.price, b.lo, b.hi + 0.01, 20) bucket, m.price
      FROM medicines m CROSS JOIN bounds b WHERE NOT m.is_price_outlier
    )
    SELECT bucket, ROUND(MIN(price), 2)::float AS range_start,
      ROUND(MAX(price), 2)::float AS range_end, COUNT(*)::int AS count
    FROM bucketed GROUP BY bucket ORDER BY bucket;
    """,
)

TOP_MANUFACTURERS = Query(
    "top_manufacturers",
    "Overview · Manufacturer volume",
    "JOINs medicines to manufacturers and GROUPs the facts by company to rank suppliers by observed product count.",
    """
    SELECT mf.id, mf.name, COUNT(m.id)::int AS product_count,
      ROUND(AVG(m.price), 2)::float AS avg_price
    FROM manufacturers mf JOIN medicines m ON m.manufacturer_id = mf.id
    GROUP BY mf.id, mf.name ORDER BY product_count DESC, mf.name LIMIT %s;
    """,
)

MANUFACTURER_PRICE_RANKING = Query(
    "manufacturer_price_ranking",
    "Overview · Price positioning",
    "JOINs and GROUPs medicine prices by manufacturer, uses HAVING to enforce a statistically meaningful minimum catalog size, then ranks either extreme.",
    """
    SELECT mf.id, mf.name, COUNT(m.id)::int AS product_count,
      ROUND(AVG(m.price), 2)::float AS avg_price,
      PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.price)::float AS median_price
    FROM manufacturers mf JOIN medicines m ON m.manufacturer_id = mf.id
    GROUP BY mf.id, mf.name HAVING COUNT(m.id) >= %s
    ORDER BY CASE WHEN %s = 'desc' THEN AVG(m.price) END DESC,
             CASE WHEN %s = 'asc' THEN AVG(m.price) END ASC
    LIMIT %s;
    """,
)

TOP_SUBCATEGORIES = Query(
    "top_subcategories",
    "Overview · Therapeutic categories",
    "GROUPs medicine rows into therapeutic sub-categories and calculates both volume and median price for richer comparison.",
    """
    SELECT sub_category, COUNT(*)::int AS product_count,
      PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::float AS median_price
    FROM medicines WHERE sub_category IS NOT NULL
    GROUP BY sub_category ORDER BY product_count DESC, sub_category LIMIT %s;
    """,
)

SEARCH_MEDICINES = Query(
    "search_medicines",
    "Medicine Search · Autocomplete",
    "JOINs manufacturer names into product suggestions and performs a case-insensitive prefix/substring search, ranked with prefix matches first.",
    """
    SELECT m.id, m.product_name, m.primary_salt, m.price::float, mf.name AS manufacturer
    FROM medicines m JOIN manufacturers mf ON mf.id = m.manufacturer_id
    WHERE m.product_name ILIKE %s
    ORDER BY CASE WHEN m.product_name ILIKE %s THEN 0 ELSE 1 END, m.product_name
    LIMIT %s;
    """,
)

MEDICINE_DETAIL = Query(
    "medicine_detail",
    "Medicine Search · Detail",
    "JOINs the manufacturer and normalized side_effects table, aggregating one-to-many effects into a JSON-friendly ordered array for a single medicine.",
    """
    SELECT m.id, m.product_name, m.sub_category, m.salt_composition, m.primary_salt,
      m.num_ingredients, m.price::float, m.is_price_outlier, mf.name AS manufacturer,
      m.medicine_desc, m.num_side_effects, m.num_interactions,
      m.has_life_threatening_interaction,
      COALESCE(array_agg(DISTINCT se.side_effect_name) FILTER (WHERE se.id IS NOT NULL), '{}') AS side_effects
    FROM medicines m JOIN manufacturers mf ON mf.id = m.manufacturer_id
    LEFT JOIN side_effects se ON se.medicine_id = m.id
    WHERE m.id = %s GROUP BY m.id, mf.name;
    """,
)

CHEAPER_ALTERNATIVES = Query(
    "cheaper_alternatives",
    "Medicine Search · Alternative finder",
    "Uses a target-medicine CTE as a self-comparison, then JOINs medicines and manufacturers on the same primary salt to calculate genuine savings versus the selected product.",
    """
    WITH target AS (SELECT id, primary_salt, price FROM medicines WHERE id = %s)
    SELECT m.id, m.product_name, mf.name AS manufacturer, m.price::float,
      t.price::float AS reference_price,
      ROUND(100.0 * (t.price - m.price) / NULLIF(t.price, 0), 1)::float AS savings_pct
    FROM target t JOIN medicines m ON m.primary_salt = t.primary_salt AND m.id <> t.id
    JOIN manufacturers mf ON mf.id = m.manufacturer_id
    WHERE m.price < t.price ORDER BY m.price ASC LIMIT %s;
    """,
)

LIST_MANUFACTURERS = Query(
    "list_manufacturers",
    "Manufacturer Insights · Selector",
    "Returns the dimension table sorted by catalog size; precomputed aggregates avoid repeatedly scanning medicines for dropdown metadata.",
    "SELECT id, name, product_count, avg_price::float, median_price::float FROM manufacturers ORDER BY product_count DESC, name;",
)

MANUFACTURER_INSIGHT = Query(
    "manufacturer_insight",
    "Manufacturer Insights · Market comparison",
    "Uses multiple CTEs and JOINs to compare a manufacturer's price for each salt against competing products with the same salt; aggregation yields an apples-to-apples average premium rather than a misleading global comparison.",
    """
    WITH selected AS (
      SELECT m.*, mf.name manufacturer FROM medicines m
      JOIN manufacturers mf ON mf.id=m.manufacturer_id WHERE mf.id=%s
    ), salt_market AS (
      SELECT primary_salt, AVG(price) market_price FROM medicines
      WHERE primary_salt IN (SELECT DISTINCT primary_salt FROM selected)
      GROUP BY primary_salt
    ), positioned AS (
      SELECT s.*, sm.market_price,
        100.0 * (s.price-sm.market_price)/NULLIF(sm.market_price,0) premium_pct
      FROM selected s JOIN salt_market sm USING (primary_salt)
    )
    SELECT %s::int id, MAX(manufacturer) name, COUNT(*)::int product_count,
      ROUND(AVG(price),2)::float avg_price,
      PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::float median_price,
      ROUND(AVG(market_price),2)::float comparable_market_avg,
      ROUND(AVG(premium_pct),2)::float avg_price_premium_pct,
      COUNT(DISTINCT primary_salt)::int salt_count
    FROM positioned;
    """,
)

PRICE_GAPS = Query(
    "price_gaps",
    "Savings Explorer · Largest gaps",
    "GROUPs non-outlier brands by primary salt with HAVING to require real choice, then derives min/max/median values and maximum savings; a window function ranks gaps without losing raw measures.",
    """
    WITH gaps AS (
      SELECT primary_salt, COUNT(*)::int brand_count, MIN(price)::float min_price,
        MAX(price)::float max_price, AVG(price)::float avg_price,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::float median_price,
        ROUND(100.0 * (MAX(price)-MIN(price))/NULLIF(MAX(price),0),1)::float max_savings_pct
      FROM medicines WHERE primary_salt IS NOT NULL AND NOT is_price_outlier
      GROUP BY primary_salt HAVING COUNT(*) >= %s
    )
    SELECT ROW_NUMBER() OVER (ORDER BY max_savings_pct DESC, max_price DESC)::int rank, *
    FROM gaps ORDER BY rank LIMIT %s;
    """,
)

SALT_PRICE_RANGE = Query(
    "salt_price_range",
    "Savings Explorer · Brand range",
    "JOINs non-outlier medicines to manufacturers for one salt and uses percent_rank windowing to show each brand's relative position across the EDA-consistent price range.",
    """
    SELECT m.id, m.product_name, mf.name manufacturer, m.price::float,
      ROUND((100.0 * PERCENT_RANK() OVER (ORDER BY m.price))::numeric,1)::float percentile
    FROM medicines m JOIN manufacturers mf ON mf.id=m.manufacturer_id
    WHERE m.primary_salt=%s AND NOT m.is_price_outlier ORDER BY m.price;
    """,
)

SAFETY_OVERVIEW = Query(
    "safety_overview",
    "Safety · Risk and distributions",
    "Combines aggregate FILTER clauses with grouped JSON subqueries to return risk share and complete side-effect/interaction count distributions in one query.",
    """
    SELECT COUNT(*)::int total,
      COUNT(*) FILTER (WHERE has_life_threatening_interaction)::int flagged,
      COUNT(*) FILTER (WHERE NOT has_life_threatening_interaction)::int not_flagged,
      ROUND(100.0*COUNT(*) FILTER (WHERE has_life_threatening_interaction)/NULLIF(COUNT(*),0),2)::float flagged_pct,
      (SELECT json_agg(x ORDER BY x.num_side_effects) FROM (
        SELECT num_side_effects, COUNT(*)::int count FROM medicines GROUP BY num_side_effects
      ) x) side_effect_distribution,
      (SELECT json_agg(x ORDER BY x.num_interactions) FROM (
        SELECT num_interactions, COUNT(*)::int count FROM medicines GROUP BY num_interactions
      ) x) interaction_distribution
    FROM medicines;
    """,
)

TOP_SIDE_EFFECTS = Query(
    "top_side_effects",
    "Safety · Normalized side effects",
    "Demonstrates the normalized one-to-many JOIN by counting distinct affected medicines per side effect and filtering noisy one-off values with HAVING.",
    """
    SELECT se.side_effect_name, COUNT(DISTINCT se.medicine_id)::int medicine_count
    FROM side_effects se JOIN medicines m ON m.id=se.medicine_id
    GROUP BY se.side_effect_name HAVING COUNT(DISTINCT se.medicine_id) >= 2
    ORDER BY medicine_count DESC, se.side_effect_name LIMIT %s;
    """,
)

INGREDIENT_PRICE_COMPLEXITY = Query(
    "ingredient_price_complexity",
    "Overview and Insights · Formulation complexity",
    "GROUPs non-outlier medicines by ingredient count and severe-interaction flag, using median price and bubble counts to test whether more complex formulations are typically more expensive or riskier.",
    """
    SELECT num_ingredients AS ingredient_count,
      has_life_threatening_interaction AS risk_flag,
      COUNT(*)::int AS medicine_count,
      ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::numeric, 2)::float AS median_price,
      ROUND(AVG(price), 2)::float AS avg_price,
      ROUND(AVG(num_interactions), 2)::float AS avg_interactions,
      ROUND(AVG(num_side_effects), 2)::float AS avg_side_effects
    FROM medicines
    WHERE NOT is_price_outlier AND num_ingredients IS NOT NULL
    GROUP BY num_ingredients, has_life_threatening_interaction
    HAVING COUNT(*) >= 3
    ORDER BY ingredient_count, risk_flag;
    """,
)

MANUFACTURER_POSITIONING = Query(
    "manufacturer_positioning",
    "Overview and Insights · Manufacturer positioning",
    "JOINs manufacturers to medicines and GROUPs each portfolio into volume, typical price, salt breadth, and safety share, enabling a two-axis comparison of scale versus price positioning.",
    """
    SELECT mf.id, mf.name,
      COUNT(m.id)::int AS product_count,
      ROUND(AVG(m.price) FILTER (WHERE NOT m.is_price_outlier), 2)::float AS avg_price,
      ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.price)
        FILTER (WHERE NOT m.is_price_outlier))::numeric, 2)::float AS median_price,
      COUNT(DISTINCT m.primary_salt)::int AS salt_count,
      ROUND(100.0 * COUNT(*) FILTER (WHERE m.has_life_threatening_interaction)
        / NULLIF(COUNT(*), 0), 1)::float AS risk_pct
    FROM manufacturers mf JOIN medicines m ON m.manufacturer_id = mf.id
    GROUP BY mf.id, mf.name HAVING COUNT(m.id) >= %s
    ORDER BY product_count DESC;
    """,
)

CATEGORY_PRICE_SPREAD = Query(
    "category_price_spread",
    "Overview and Insights · Therapeutic category price spread",
    "Uses a top-category CTE plus percentile aggregation to compare the middle 80 percent of prices within each category, revealing variation without allowing extreme outliers to control the chart.",
    """
    WITH top_categories AS (
      SELECT sub_category FROM medicines WHERE sub_category IS NOT NULL
      GROUP BY sub_category ORDER BY COUNT(*) DESC, sub_category LIMIT %s
    )
    SELECT m.sub_category,
      COUNT(*)::int AS product_count,
      ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY m.price)::numeric, 2)::float AS p10,
      ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY m.price)::numeric, 2)::float AS q1,
      ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY m.price)::numeric, 2)::float AS median,
      ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY m.price)::numeric, 2)::float AS q3,
      ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY m.price)::numeric, 2)::float AS p90
    FROM medicines m JOIN top_categories tc USING (sub_category)
    WHERE NOT m.is_price_outlier
    GROUP BY m.sub_category ORDER BY (PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY m.price)
      - PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY m.price)) DESC;
    """,
)

ANALYTICAL_QUERIES = {
    q.name: q for q in (
        OVERVIEW_KPIS, PRICE_HISTOGRAM, TOP_MANUFACTURERS, MANUFACTURER_PRICE_RANKING,
        TOP_SUBCATEGORIES, SEARCH_MEDICINES, MEDICINE_DETAIL, CHEAPER_ALTERNATIVES,
        LIST_MANUFACTURERS, MANUFACTURER_INSIGHT, PRICE_GAPS, SALT_PRICE_RANGE,
        SAFETY_OVERVIEW, TOP_SIDE_EFFECTS, INGREDIENT_PRICE_COMPLEXITY,
        MANUFACTURER_POSITIONING, CATEGORY_PRICE_SPREAD,
    )
}

ALL_QUERIES = {
    q.name: q for q in (
        CREATE_SCHEMA, TRUNCATE_ALL, COUNT_MEDICINES, INSERT_MANUFACTURER,
        GET_MANUFACTURER_IDS, INSERT_MEDICINE, SET_MEDICINE_SEQUENCE,
        INSERT_SIDE_EFFECT, *ANALYTICAL_QUERIES.values()
    )
}
