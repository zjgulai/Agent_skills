"""Doctor should surface global metadata drift, not only per-skill rules."""
from __future__ import annotations


def test_doctor_all_includes_state_audit_summary(monkeypatch):
    from agent.lib import doctor

    class FakeReport:
        has_drift = True
        installed_parseable_count = 2
        index_count = 1
        graph_count = 1
        invalid_frontmatter = ["broken-skill"]
        parseable_not_indexed = ["missing-index"]
        indexed_missing_or_invalid = []
        index_missing_graph = ["indexed-a"]
        graph_extra = []
        graph_domain_mismatch = []
        mirror_index_in_sync = False
        mirror_graph_in_sync = True
        mirror_png_in_sync = True
        docs_status_matches_parseable = False

    monkeypatch.setattr(doctor, "check_all", lambda: {})
    monkeypatch.setattr(doctor, "audit_state", lambda: FakeReport())

    payload = doctor.build_all_payload(include_state_audit=True)

    assert payload["state_audit"]["has_drift"] is True
    assert payload["state_audit"]["installed_parseable_count"] == 2
    assert "broken-skill" in payload["state_audit"]["invalid_frontmatter"]


def test_doctor_builds_dependency_checks_from_frontmatter(monkeypatch):
    from agent.lib import doctor

    monkeypatch.setenv("EXAMPLE_API_KEY", "set")
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/bin/{name}" if name == "node" else None)
    monkeypatch.setattr(doctor, "_python_module_available", lambda name: name == "yaml")

    deps = doctor._declared_dependency_hints({
        "requires": {
            "binaries": ["node"],
            "env": ["EXAMPLE_API_KEY"],
            "python_modules": ["yaml"],
        }
    })

    results = {name: check() for name, check in deps}

    assert results == {
        "binary:node": True,
        "env:EXAMPLE_API_KEY": True,
        "python:yaml": True,
    }
