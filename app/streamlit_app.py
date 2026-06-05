# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov Streamlit MVP (spec v0.4 §14).

A thin view over ``rcgov.service.govern_bytes`` — all logic lives in the
streamlit-free service layer so it stays unit testable. Uploaded files are
materialized to a scratch workdir, governed, and the real artifacts are rendered
in the output panes.

Run with:  PYTHONPATH=src streamlit run app/streamlit_app.py   (needs ``ui`` extra)
"""
from __future__ import annotations


def main() -> None:
    import streamlit as st

    from rcgov.pack import PROFILES
    from rcgov.service import govern_bytes

    st.set_page_config(page_title="RCGov", layout="wide")
    st.title("RCGov — Reflective Context Governor")
    st.caption("Clean and govern AI context before the model reads it.")

    # --- Controls (spec §14.1) --------------------------------------------
    with st.sidebar:
        st.header("Controls")
        files = st.file_uploader("Upload files", accept_multiple_files=True)
        task = st.text_area("Describe current task", value="")
        profile = st.selectbox("Profile", PROFILES, index=PROFILES.index("Balanced"))
        temporal = st.checkbox("Enable experimental temporal ordering", value=False)
        commit_file = st.file_uploader("Commitment manifest (optional)", type=["yaml", "yml"])
        go = st.button("Run governance", type="primary")

    panes = st.tabs([
        "ContextReady summary",
        "Clean Context Pack",
        "Non-Injection Report",
        "Conflict Map",
        "Authority Review Queue",
        "Manifest",
    ])

    if not go:
        with panes[0]:
            st.info("Upload files, describe the task, then run governance.")
        return

    if not files:
        with panes[0]:
            st.warning("No files uploaded.")
        return

    inputs = [(f.name, f.getvalue()) for f in files]
    commitments = commit_file.getvalue() if commit_file is not None else None
    result = govern_bytes(inputs, task, profile=profile,
                          temporal_attention=temporal, commitments=commitments)

    counts = result.manifest.get("counts", {})
    stab = result.manifest.get("authority_stabilization", {})

    with panes[0]:
        st.success(result.summary)
        cols = st.columns(5)
        for col, key in zip(cols, ("segments", "injectable", "committed",
                                   "quarantined", "disagreements")):
            col.metric(key, counts.get(key, 0))
        if stab.get("recommended"):
            st.warning("**Authority Stabilization recommended.** " + (stab.get("message") or ""))

    def show(pane, name: str, *, code: bool = False) -> None:
        with pane:
            text = result.artifacts.get(name, "_(not produced)_")
            st.code(text) if code else st.markdown(text)
            st.download_button(f"Download {name}", text, file_name=name)

    show(panes[1], "CLEAN_CONTEXT_PACK.md")
    show(panes[2], "NON_INJECTION_REPORT.md")
    show(panes[3], "CONFLICT_MAP.md")
    show(panes[4], "AUTHORITY_REVIEW_QUEUE.jsonl", code=True)
    show(panes[5], "CONTEXT_MANIFEST.json", code=True)


if __name__ == "__main__":
    main()
