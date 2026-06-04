# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov Streamlit MVP — UI skeleton (spec v0.4 §14).

STATUS: skeleton. Renders the controls and output panes from the spec. The
"Run governance" button calls ``rcgov.pipeline.run`` which currently raises
NotImplementedError for un-built stages — the UI surfaces that honestly rather
than faking a clean pack.

Run with:  streamlit run app/streamlit_app.py   (needs the ``ui`` extra)
"""
from __future__ import annotations


def main() -> None:
    import streamlit as st

    from rcgov.contract import OUTPUT_FILES
    from rcgov.pack import PROFILES

    st.set_page_config(page_title="RCGov", layout="wide")
    st.title("RCGov — Reflective Context Governor")
    st.caption("Clean and govern AI context before the model reads it.")

    # --- Controls (spec §14.1) --------------------------------------------
    with st.sidebar:
        st.header("Controls")
        files = st.file_uploader("Upload files", accept_multiple_files=True)
        task = st.text_area("Describe current task")
        profile = st.selectbox("Profile", PROFILES, index=PROFILES.index("Balanced"))
        temporal = st.checkbox("Enable experimental temporal ordering", value=False)
        go = st.button("Run governance", type="primary")

    # --- Output panes (spec §14.2) ----------------------------------------
    panes = st.tabs([
        "ContextReady summary",
        "Clean Context Pack",
        "Non-Injection Report",
        "Authority Review Queue",
        "Override Log",
        "Manifest",
    ])

    if not go:
        with panes[0]:
            st.info("Upload files, describe the task, then run governance.")
            st.write("Artifacts produced:", list(OUTPUT_FILES))
        return

    from rcgov.pipeline import RunConfig, run

    cfg = RunConfig(task=task or "", profile=profile, temporal_attention=temporal)
    try:
        result = run([f.name for f in (files or [])], cfg)
        with panes[0]:
            st.success(result.summary or "Run complete.")
    except NotImplementedError as exc:
        with panes[0]:
            st.warning(
                "RCGov is a pre-alpha scaffold. The governance pipeline stage "
                f"below is not implemented yet:\n\n```\n{exc}\n```"
            )


if __name__ == "__main__":
    main()
