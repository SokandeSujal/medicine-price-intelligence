from backend import queries


def test_all_analytical_queries_are_documented_and_nontrivial():
    assert len(queries.ANALYTICAL_QUERIES) >= 8
    for name, query in queries.ANALYTICAL_QUERIES.items():
        assert query.name == name
        assert query.section and len(query.purpose) > 40
        assert "SELECT" in query.sql.upper()


def test_required_database_concepts_are_visible():
    sql = "\n".join(q.sql.upper() for q in queries.ANALYTICAL_QUERIES.values())
    for concept in ("JOIN", "GROUP BY", "HAVING", "OVER ("):
        assert concept in sql


def test_no_inline_sql_in_routes():
    source = (Path(__file__).parents[1] / "main.py").read_text(encoding="utf-8")
    assert "SELECT " not in source.upper()


from pathlib import Path
