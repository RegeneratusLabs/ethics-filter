"""Audit log tests."""

from ethics_filter.engine import evaluate, read_audit_log


def test_audit_record_appended(audit_path):
    evaluate(
        action="Donate 10% of profits to a local community fund",
        context="regional business, community board",
        module_scores={
            "fairness": 90, "transparency": 85, "ethical-framework": 85,
            "conscious-leadership": 85, "compliance": 80,
        },
        constitution_name="small-business-ethical",
        audit=True,
        audit_path=audit_path,
    )
    records = read_audit_log(audit_path)
    assert len(records) == 1
    record = records[0]
    assert record["action"].startswith("Donate 10%")
    assert record["decision"] in {"green", "amber", "red"}
    assert 0 <= record["overall_score"] <= 100
    assert "timestamp" in record
    assert "module_results" in record


def test_audit_append_order(audit_path):
    for i in range(3):
        evaluate(
            action=f"Decision number {i}",
            context="",
            module_scores={
                "fairness": 80, "transparency": 80, "ethical-framework": 80 + i,
            },
            constitution_name="small-business-ethical",
            audit=True,
            audit_path=audit_path,
        )
    records = read_audit_log(audit_path)
    assert [r["action"] for r in records] == [
        "Decision number 0", "Decision number 1", "Decision number 2",
    ]


def test_audit_tail_limits(audit_path):
    for i in range(5):
        evaluate(
            action=f"Decision number {i}",
            context="",
            module_scores={
                "fairness": 80, "transparency": 80, "ethical-framework": 80,
            },
            constitution_name="small-business-ethical",
            audit=True,
            audit_path=audit_path,
        )
    records = read_audit_log(audit_path, tail=2)
    assert len(records) == 2
    assert records[-1]["action"] == "Decision number 4"


def test_no_audit_when_disabled(audit_path):
    evaluate(
        action="A quiet decision",
        context="",
        module_scores={
            "fairness": 80, "transparency": 80, "ethical-framework": 80,
        },
        constitution_name="small-business-ethical",
        audit=False,
        audit_path=audit_path,
    )
    assert read_audit_log(audit_path) == []


def test_missing_log_returns_empty(tmp_path):
    assert read_audit_log(tmp_path / "nope.jsonl") == []
