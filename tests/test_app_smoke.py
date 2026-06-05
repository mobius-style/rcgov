# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Streamlit app smoke test via the AppTest harness.

Skipped when streamlit is not installed (it is an optional ``ui`` extra). When
present, this actually executes app/streamlit_app.py in a simulated runtime and
asserts the script runs without raising — verifying imports, widget
construction, and both the idle and the run code paths.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


def test_app_boots_idle():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    # idle state shows the guidance info message
    assert any("run governance" in i.value.lower() for i in at.info)


def test_app_run_without_files_warns():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.button[0].set_value(True).run()
    assert not at.exception
    assert any("no files" in w.value.lower() for w in at.warning)
