"""LogiX-VN Lab 8 - live demo for the classroom projector.

Run from the repo root (K5-Day8-From-Workflows-to-Agents/) with the lab venv active:

    python -m pip install -r demo_ui/requirements-demo.txt
    streamlit run demo_ui/app.py --theme.base light

The demo imports lab8 from src/ and reads src/reports, src/traces (skeleton layout).
Main page is a chatbot: run config in the sidebar, each answer shows the live call log.
The other pages (compare, security, durability, benchmark) sit in the sidebar menu
in talk order. The slides live in demo_ui/slides/index.html.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="LogiX-VN Lab 8 Demo",
    layout="wide",
    initial_sidebar_state="expanded",
)

import demo_lab_runner_service  # noqa: E402,F401 - bootstraps repo path and cwd before lab8 imports
import page_benchmark_dashboard  # noqa: E402
import page_chat_console  # noqa: E402
import page_compare_shapes  # noqa: E402
import page_durability_lab  # noqa: E402
import page_security_gates  # noqa: E402
from demo_theme_styles import inject_theme  # noqa: E402
from demo_ui_components import html_block  # noqa: E402

PAGES = {
    "Chat demo": page_chat_console,
    "So sánh 4 shape": page_compare_shapes,
    "Bảo mật": page_security_gates,
    "Durability": page_durability_lab,
    "Benchmark": page_benchmark_dashboard,
}


def main() -> None:
    inject_theme()
    st.sidebar.markdown('<div class="lx-brand">LogiX-VN · Lab 8</div>', unsafe_allow_html=True)
    title = st.sidebar.radio("Trang", list(PAGES), key="nav_page", label_visibility="collapsed")
    st.sidebar.divider()
    if title != "Chat demo":
        html_block(
            '<div class="lx-hero"><h1>Kiến trúc nào đáng tin khi agent được quyền trả tiền?</h1>'
            "<p>LogiX-VN · hoàn phí ship · 14 claim công khai · 4 shape · 5 seed · MockLLM</p></div>"
        )
    try:
        PAGES[title].render()
    except Exception as exc:  # noqa: BLE001 - one broken page must not blank the demo
        st.error(f"Trang {title} gặp lỗi: {type(exc).__name__}: {exc}")


main()
