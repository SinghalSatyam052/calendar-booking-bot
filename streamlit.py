from __future__ import annotations

import streamlit as st, uuid, requests

import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/chat")

st.set_page_config(page_title="Calendar‑Bot", page_icon="📅")

st.header("📅 Book with my calendar")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ── helper ────────────────────────────────────────────────────────────────────

def backend_chat(msg: str) -> dict:
    resp = requests.post(
        BACKEND_URL,
        json={"session_id": st.session_state.session_id, "message": msg},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()

# ── chat history ─────────────────────────────────────────────────────────────
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Tell me when you’d like to meet…")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = backend_chat(prompt)
        st.session_state.messages.append({"role": "assistant", "content": reply["answer"]})
        st.markdown(reply["answer"])

        # render suggestion buttons if present
        if reply.get("suggestions"):
            st.markdown("### Suggested slots:")
            for s in reply["suggestions"]:
                label = f"{s['start'][11:16]}–{s['end'][11:16]}"  # HH:MM‑HH:MM
                if st.button(f"✅ Book {label}"):
                    confirm = backend_chat(f"Book {label}")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": confirm["answer"]}
                    )
                    st.experimental_rerun()