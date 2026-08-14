"""CLI tests (invoke main() directly, no subprocess)."""

import json

from ethics_filter.cli import main


def test_version(capsys):
    assert main(["version"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("ethics-filter ")


def test_evaluate_brief(capsys):
    rc = main(["evaluate", "Publish salary bands", "--context", "50-person company"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Enabled modules" in out
    assert "fairness" in out
    assert "EVALUATION PROMPT" in out


def test_evaluate_brief_json(capsys):
    rc = main([
        "evaluate", "Publish salary bands", "--context", "50-person company", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["enabled_modules"] == ["fairness", "transparency", "ethical-framework"]
    assert "prompt" in data


def test_evaluate_with_scores(capsys, tmp_path, monkeypatch):
    audit_file = tmp_path / "audit.jsonl"
    rc = main([
        "evaluate", "Publish salary bands",
        "--context", "50-person company",
        "--scores", '{"fairness": 90, "transparency": 85, "ethical-framework": 88}',
        "--audit-path", str(audit_file),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Decision: GREEN" in out
    assert "Overall score: 87.7" in out
    assert audit_file.exists()


def test_evaluate_with_scores_json(capsys, tmp_path, monkeypatch):
    rc = main([
        "evaluate", "Fix prices with competitors",
        "--context", "illegal collusion",
        "--scores", '{"fairness": 5, "transparency": 10, "ethical-framework": 5, "compliance": 5}',
        "--json", "--no-audit",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["decision"] == "red"
    assert data["requires_human"] is True


def test_evaluate_missing_scores_error(capsys):
    rc = main([
        "evaluate", "Restructure the team",
        "--context", "affects 20 employees",
        "--scores", '{"fairness": 90}',
        "--no-audit",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "Missing scores" in err


def test_evaluate_invalid_json_scores(capsys):
    rc = main(["evaluate", "Anything", "--scores", "not-json", "--no-audit"])
    assert rc == 2


def test_evaluate_unknown_constitution(capsys):
    rc = main(["evaluate", "Anything", "--constitution", "nope", "--no-audit"])
    assert rc == 2
    assert "Unknown constitution" in capsys.readouterr().err


def test_audit_empty(capsys, tmp_path):
    rc = main(["audit", "--audit-path", str(tmp_path / "empty.jsonl")])
    assert rc == 0
    assert "No audit records" in capsys.readouterr().out


def test_audit_lists_records(capsys, tmp_path):
    audit_file = tmp_path / "audit.jsonl"
    main([
        "evaluate", "Donate to charity",
        "--scores", '{"fairness": 90, "transparency": 85, "ethical-framework": 85}',
        "--audit-path", str(audit_file),
    ])
    rc = main(["audit", "--audit-path", str(audit_file)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Donate to charity" in out
    assert "GREEN" in out


def test_modules(capsys):
    rc = main(["modules"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ethical-framework" in out
    assert "compliance" in out


def test_constitutions(capsys):
    rc = main(["constitutions"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "small-business-ethical" in out
    assert "maximalist" in out


def test_no_command_is_error():
    import pytest as _pytest

    with _pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 2
