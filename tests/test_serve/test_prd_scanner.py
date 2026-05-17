"""Smoke tests for serve.prd_scanner.

The PRD scanner walks <vault_root>/prd/ and builds an index of PRD files
with cross-links back to research notes. These tests exercise:

- empty vault (no prd/ directory): returns []
- single PRD with frontmatter + matching request file: full record built
- multiple PRDs sorted newest-first by mtime
- prds_for_research lookup by research_note_id
- feature_groups produces one group per PRD
- find_prd lookup by tag
- read_prd_body strips frontmatter
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from hyperresearch.serve.prd_scanner import (
    feature_groups,
    find_prd,
    prds_for_research,
    read_prd_body,
    scan_prds,
)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    return tmp_path


def test_scan_returns_empty_when_no_prd_dir(vault_root: Path):
    assert scan_prds(vault_root) == []


def test_scan_returns_empty_when_prd_dir_has_no_finals(vault_root: Path):
    (vault_root / "prd").mkdir()
    (vault_root / "prd" / "scaffold.md").write_text("# scaffold", encoding="utf-8")
    assert scan_prds(vault_root) == []


def test_scan_builds_full_record(vault_root: Path):
    _write(
        vault_root / "prd" / "notes" / "final_prd_chat-feature.md",
        (
            "---\n"
            "title: Real-Time Chat\n"
            "research_final_report_path: research/notes/final_report_chat-123.md\n"
            "response_format: full_prd\n"
            "pipeline_tier: full\n"
            "---\n"
            "# Real-Time Chat PRD\n\n"
            "This is the body.\n"
        ),
    )
    _write(
        vault_root / "prd" / "request-chat-feature.md",
        "---\nprd_tag: chat-feature\n---\nUser-supplied request: build chat.\n",
    )
    _write(
        vault_root / "prd" / "prd-decomposition.json",
        json.dumps({"pipeline_tier": "full", "response_format": "full_prd"}),
    )

    records = scan_prds(vault_root)
    assert len(records) == 1
    record = records[0]
    assert record.prd_tag == "chat-feature"
    assert record.title == "Real-Time Chat"
    assert record.research_path == "research/notes/final_report_chat-123.md"
    assert record.research_note_id == "final_report_chat-123"
    assert record.research_tag == "chat-123"
    assert record.modality == "full_prd"
    assert record.tier == "full"
    assert record.feature_request is not None
    assert "User-supplied request" in record.feature_request
    assert record.feature_request_path is not None
    assert record.word_count > 0


def test_scan_falls_back_to_h1_when_no_title_frontmatter(vault_root: Path):
    _write(
        vault_root / "prd" / "notes" / "final_prd_x.md",
        "---\nresponse_format: one_pager\n---\n# Title From H1\n",
    )
    records = scan_prds(vault_root)
    assert records[0].title == "Title From H1"
    assert records[0].modality == "one_pager"


def test_scan_falls_back_to_tag_when_no_h1_or_title(vault_root: Path):
    _write(vault_root / "prd" / "notes" / "final_prd_naked.md", "no frontmatter here\n")
    records = scan_prds(vault_root)
    assert records[0].title == "PRD: naked"


def test_scan_sorts_by_mtime_descending(vault_root: Path):
    old = _write(vault_root / "prd" / "notes" / "final_prd_old.md", "# Old\n")
    time.sleep(0.05)
    new = _write(vault_root / "prd" / "notes" / "final_prd_new.md", "# New\n")
    # Force a 1s mtime gap so the test is robust on filesystems with coarse
    # mtime granularity (HFS, FAT32, some NFS).
    old_time = time.time() - 100
    os.utime(old, (old_time, old_time))
    os.utime(new, None)

    records = scan_prds(vault_root)
    assert [r.prd_tag for r in records] == ["new", "old"]


def test_scan_falls_back_to_decomposition_for_tier(vault_root: Path):
    _write(
        vault_root / "prd" / "notes" / "final_prd_minimal.md",
        "# Minimal PRD\n",
    )
    _write(
        vault_root / "prd" / "prd-decomposition.json",
        json.dumps({"pipeline_tier": "light", "response_format": "one_pager"}),
    )
    record = scan_prds(vault_root)[0]
    assert record.tier == "light"
    assert record.modality == "one_pager"


def test_prds_for_research_matches_by_note_id(vault_root: Path):
    _write(
        vault_root / "prd" / "notes" / "final_prd_a.md",
        "---\nresearch_final_report_path: research/notes/final_report_alpha.md\n---\n# A\n",
    )
    _write(
        vault_root / "prd" / "notes" / "final_prd_b.md",
        "---\nresearch_final_report_path: research/notes/final_report_beta.md\n---\n# B\n",
    )
    records = scan_prds(vault_root)
    matched = prds_for_research(records, "final_report_alpha")
    assert [r.prd_tag for r in matched] == ["a"]


def test_prds_for_research_returns_empty_when_no_match(vault_root: Path):
    _write(
        vault_root / "prd" / "notes" / "final_prd_a.md",
        "---\nresearch_final_report_path: research/notes/final_report_alpha.md\n---\n# A\n",
    )
    records = scan_prds(vault_root)
    assert prds_for_research(records, "final_report_other") == []


def test_feature_groups_one_per_prd(vault_root: Path):
    _write(vault_root / "prd" / "notes" / "final_prd_a.md", "# A\n")
    _write(vault_root / "prd" / "notes" / "final_prd_b.md", "# B\n")
    records = scan_prds(vault_root)
    groups = feature_groups(records)
    assert {g.tag for g in groups} == {"a", "b"}
    assert all(g.prd is not None for g in groups)


def test_feature_groups_snippet_truncates_long_request(vault_root: Path):
    long_request = "x" * 1000
    _write(
        vault_root / "prd" / "notes" / "final_prd_long.md",
        "# Long\n",
    )
    _write(vault_root / "prd" / "request-long.md", long_request)
    records = scan_prds(vault_root)
    snippet = feature_groups(records)[0].feature_request_snippet
    assert snippet is not None
    assert len(snippet) <= 280
    assert snippet.endswith("...")


def test_find_prd_by_tag(vault_root: Path):
    _write(vault_root / "prd" / "notes" / "final_prd_lookup.md", "# Lookup\n")
    records = scan_prds(vault_root)
    assert find_prd(records, "lookup") is not None
    assert find_prd(records, "missing") is None


def test_read_prd_body_strips_frontmatter(vault_root: Path):
    _write(
        vault_root / "prd" / "notes" / "final_prd_strip.md",
        "---\ntitle: Strip Me\n---\n# Body Heading\n\nbody text\n",
    )
    record = scan_prds(vault_root)[0]
    body = read_prd_body(record)
    assert body.startswith("# Body Heading")
    assert "title: Strip Me" not in body
