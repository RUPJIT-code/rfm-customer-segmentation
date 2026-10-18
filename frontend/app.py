from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

APP_TITLE = "Customer Signals"
DEFAULT_API_URL = "http://127.0.0.1:8000"
API_URL = os.getenv("CUSTOMER_SEGMENTATION_API_URL", DEFAULT_API_URL).rstrip("/")
HEALTH_TIMEOUT = 4
PREDICT_TIMEOUT = 12

FEATURE_HELP = {
    "Recency": "Days since the customer's most recent purchase.",
    "Frequency": "Number of distinct orders placed by the customer.",
    "Monetary": "Total historical sales value for the customer.",
    "Avg_Discount_Rate": "Enter a decimal: 0.10 means a 10% average discount.",
    "Unique_Product_Categories": "Number of distinct product departments/categories purchased.",
    "Total_Profit": "Historical total profit. Negative values are allowed.",
}

st.set_page_config(page_title=APP_TITLE, page_icon="◒", layout="wide", initial_sidebar_state="collapsed")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --paper: #f5f1e8; --panel: #fffdf8; --ink: #202b25;
          --muted: #6b756d; --line: #dedfd3; --forest: #244d3b;
          --forest2: #35674d; --clay: #c66a45; --pale: #e7ecdf;
        }
        .stApp { background: var(--paper); color: var(--ink); }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { max-width: 1440px; padding-top: 1.4rem; padding-bottom: 2rem; }
        #MainMenu, footer { visibility: hidden; }
        h1, h2, h3, p, label { color: var(--ink); }
        .masthead {
          background: var(--forest); border-radius: 22px; padding: 1.65rem 1.8rem;
          color: #fffdf8; margin-bottom: 1.2rem; position: relative; overflow: hidden;
        }
        .masthead:after { content: ""; position: absolute; right: -45px; top: -95px; width: 270px; height: 270px;
          border: 1px solid rgba(255,255,255,.16); border-radius: 50%; box-shadow: 0 0 0 28px rgba(255,255,255,.035), 0 0 0 58px rgba(255,255,255,.025); }
        .eyebrow { color: #d9e5d8; text-transform: uppercase; letter-spacing: .16em; font-size: .72rem; font-weight: 800; }
        .masthead h1 { color: #fffdf8; font-size: clamp(2rem, 4vw, 3.1rem); line-height: 1.04; margin: .55rem 0 .65rem; letter-spacing: -.04em; }
        .masthead p { color: #e3e9df; max-width: 780px; margin: 0; font-size: 1rem; }
        .masthead-foot { margin-top: 1.15rem; display:flex; gap:.55rem; flex-wrap:wrap; }
        .pill { display:inline-block; border:1px solid rgba(255,255,255,.25); border-radius:999px; padding:.32rem .68rem; color:#fffdf8; font-size:.76rem; }
        .section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin: .45rem 0 .85rem; }
        .section-kicker { color: var(--forest2); font-size:.72rem; text-transform:uppercase; letter-spacing:.14em; font-weight:850; margin-bottom:.2rem; }
        .section-title { font-size:1.3rem; font-weight:850; letter-spacing:-.025em; color:var(--ink); }
        .section-sub { color:var(--muted); font-size:.9rem; margin-top:.18rem; }
        .surface { background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:1.2rem 1.25rem; height:100%; }
        .surface-dark { background:#e8ece2; border:1px solid #d4ddcf; border-radius:18px; padding:1.2rem 1.25rem; height:100%; }
        .card-label { text-transform:uppercase; font-size:.7rem; letter-spacing:.12em; color:var(--muted); font-weight:800; }
        .big-number { font-size:1.8rem; line-height:1.15; font-weight:850; color:var(--forest); margin:.25rem 0; }
        .muted { color:var(--muted); font-size:.88rem; }
        .rule { border-top:1px solid var(--line); margin:1rem 0; }
        .result-box { background:var(--forest); color:#fffdf8; border-radius:18px; padding:1.35rem; }
        .result-box .card-label { color:#d3e1d2; }
        .result-box h2 { color:#fffdf8; font-size:1.6rem; line-height:1.15; margin:.45rem 0 .55rem; }
        .result-box p { color:#e5ece2; }
        .result-chip { display:inline-block; border-radius:999px; background:#dce8d9; color:#244d3b; font-size:.78rem; font-weight:800; padding:.32rem .65rem; }
        div[data-testid="stForm"] { background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:1.1rem 1.25rem 1.2rem; }
        /* Explicit foreground colors: some browser/Streamlit themes otherwise render
           entered numbers with a low-contrast or white text color. */
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea {
          background:#fffefa !important;
          color:#202b25 !important;
          -webkit-text-fill-color:#202b25 !important;
          caret-color:#244d3b !important;
          opacity:1 !important;
        }
        div[data-testid="stNumberInput"] button { color:#202b25 !important; }
        div[data-testid="stNumberInput"] label, div[data-testid="stTextInput"] label { font-weight:700; color:#202b25 !important; }
        .stButton > button, div[data-testid="stFormSubmitButton"] > button { background:var(--clay); color:white; border:0; border-radius:10px; font-weight:800; padding:.62rem 1rem; min-height:2.8rem; }
        .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { background:#a95434; color:white; border:0; }
        div[data-testid="stAlert"] { border-radius:12px; }
        .footer { text-align:center; color:var(--muted); font-size:.78rem; padding:1.5rem .5rem .4rem; }
        @media (max-width: 700px) { .masthead { padding:1.25rem; } .surface,.surface-dark { padding:1rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_health() -> tuple[bool, dict[str, Any] | str]:
    try:
        response = requests.get(f"{API_URL}/health", timeout=HEALTH_TIMEOUT)
        response.raise_for_status()
        body = response.json()
        ok = body.get("status") == "ok" and bool(body.get("model_loaded")) and bool(body.get("scaler_loaded"))
        return ok, body
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {API_URL}. Start the FastAPI backend first."
    except requests.exceptions.Timeout:
        return False, "The API health check timed out."
    except requests.exceptions.RequestException as exc:
        return False, f"Health check failed: {exc}"
    except ValueError:
        return False, "The backend returned invalid JSON from /health."


def request_prediction(payload: dict[str, float]) -> tuple[bool, dict[str, Any] | str]:
    try:
        response = requests.post(f"{API_URL}/predict", json=payload, timeout=PREDICT_TIMEOUT)
        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text or "The API returned an invalid response."}
        if response.status_code != 200:
            detail = body.get("detail", f"HTTP {response.status_code}") if isinstance(body, dict) else str(body)
            return False, f"API error ({response.status_code}): {detail}"
        required = {"cluster", "segment_name", "description", "recommendation"}
        if not isinstance(body, dict) or not required.issubset(body):
            return False, "The API response is missing expected fields: cluster, segment_name, description, recommendation."
        return True, body
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {API_URL}. Start the FastAPI backend first."
    except requests.exceptions.Timeout:
        return False, "The prediction request timed out. Please try again."
    except requests.exceptions.RequestException as exc:
        return False, f"Prediction request failed: {exc}"


def section_heading(kicker: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="section-head"><div><div class="section-kicker">{kicker}</div>'
        f'<div class="section-title">{title}</div><div class="section-sub">{subtitle}</div></div></div>',
        unsafe_allow_html=True,
    )


def render_header(api_ok: bool) -> None:
    status = "API CONNECTED" if api_ok else "API OFFLINE"
    st.markdown(
        f'<div class="masthead"><div class="eyebrow">Customer segmentation · RFM + behavior</div>'
        f'<h1>Know the customer.<br>Choose the next move.</h1>'
        f'<p>A single workspace to profile a customer, get a segment prediction, and translate that result into a practical business action.</p>'
        f'<div class="masthead-foot"><span class="pill">◒ &nbsp; Five customer segments</span>'
        f'<span class="pill">↗ &nbsp; FastAPI prediction service</span><span class="pill">{status}</span></div></div>',
        unsafe_allow_html=True,
    )


def render_result(result: dict[str, Any], payload: dict[str, float]) -> None:
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">Prediction returned by the API</div>', unsafe_allow_html=True)
    st.markdown(f'<h2>{result["segment_name"]}</h2>', unsafe_allow_html=True)
    st.markdown(f'<span class="result-chip">Cluster {int(result["cluster"])}</span>', unsafe_allow_html=True)
    st.markdown("<div style='height: .8rem'></div>", unsafe_allow_html=True)
    st.markdown("**Customer profile**", unsafe_allow_html=True)
    st.markdown(str(result["description"]), unsafe_allow_html=True)
    st.markdown("<div style='height: .4rem'></div>", unsafe_allow_html=True)
    st.markdown("**Recommended next action**", unsafe_allow_html=True)
    st.markdown(str(result["recommendation"]), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    with st.expander("See the six values sent to the model"):
        display = pd.DataFrame([payload]).rename(columns={
            "Avg_Discount_Rate": "Average discount (decimal)",
            "Unique_Product_Categories": "Unique product categories",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption("The segment label and recommendation are taken from the API response; the frontend does not independently assign a segment.")


def main() -> None:
    inject_css()
    api_ok, health = api_health()
    render_header(api_ok)

    # One-page layout: inputs and the live prediction occupy the same workspace.
    left, right = st.columns([1.12, 0.88], gap="large")
    with left:
        section_heading("01 · CUSTOMER PROFILE", "Enter customer signals", "Use historical customer-level values calculated with the same definitions as the training data.")
        if not api_ok:
            detail = health.get("detail") if isinstance(health, dict) else health
            st.warning(
                "The API is not reporting ready. You can still submit the form to see the exact prediction error. "
                f"Details: {detail or 'Check that FastAPI is running and its model artifacts loaded.'}"
            )
        # Use standalone widgets rather than a form so each value updates
        # immediately and repeat predictions do not depend on form submission state.
        st.markdown("**Purchase behavior**")
        a, b = st.columns(2)
        with a:
            recency = st.number_input(
                "Recency · days", min_value=0.0, value=100.0, step=1.0,
                help=FEATURE_HELP["Recency"], key="input_recency"
            )
            monetary = st.number_input(
                "Monetary · total sales", min_value=0.0, value=500.0, step=50.0,
                help=FEATURE_HELP["Monetary"], key="input_monetary"
            )
            categories = st.number_input(
                "Distinct categories", min_value=1.0, value=2.0, step=1.0,
                help=FEATURE_HELP["Unique_Product_Categories"], key="input_categories"
            )
        with b:
            frequency = st.number_input(
                "Frequency · orders", min_value=1.0, value=2.0, step=1.0,
                help=FEATURE_HELP["Frequency"], key="input_frequency"
            )
            discount = st.number_input(
                "Average discount · decimal", min_value=0.0, max_value=1.0,
                value=0.10, step=0.01, format="%.2f",
                help=FEATURE_HELP["Avg_Discount_Rate"], key="input_discount"
            )
            profit = st.number_input(
                "Total profit", value=100.0, step=25.0,
                help=FEATURE_HELP["Total_Profit"], key="input_profit"
            )
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        st.caption(
            "Discount: 0.10 = 10%. Profit can be negative. Enter values from the "
            "same customer-level definitions used during model training."
        )
        submitted = st.button(
            "Generate customer segment  →",
            use_container_width=True,
            key="predict_customer_button"
        )

        if submitted:
            st.session_state["prediction_request_count"] = (
                st.session_state.get("prediction_request_count", 0) + 1
            )
            payload = {
                "Recency": float(recency),
                "Frequency": float(frequency),
                "Monetary": float(monetary),
                "Avg_Discount_Rate": float(discount),
                "Unique_Product_Categories": float(categories),
                "Total_Profit": float(profit),
            }
            with st.spinner("Sending customer features to the prediction API…"):
                success, response = request_prediction(payload)
            if success:
                st.session_state["last_prediction"] = response
                st.session_state["last_payload"] = payload
                st.session_state.pop("last_prediction_error", None)
            else:
                st.session_state.pop("last_prediction", None)
                st.session_state["last_prediction_error"] = str(response)

    with right:
        section_heading("02 · RESULT", "Customer decision panel", "The response appears here after you submit the form.")
        if st.session_state.get("last_prediction_error"):
            st.error(st.session_state["last_prediction_error"])
        elif st.session_state.get("last_prediction"):
            render_result(st.session_state["last_prediction"], st.session_state["last_payload"])
        else:
            st.markdown(
                '<div class="surface-dark"><div class="card-label">READY FOR PREDICTION</div>'
                '<div class="big-number">One customer.<br>One clear next step.</div>'
                '<p class="muted">Complete the six fields on the left and run the prediction. The segment name, explanation, and recommended action will appear in this panel.</p>'
                '<div class="rule"></div><div class="card-label">WHAT THE MODEL USES</div>'
                '<p class="muted">Recency · Frequency · Monetary · Discount rate · Category diversity · Total profit</p></div>',
                unsafe_allow_html=True,
            )
            st.markdown(" ")
            st.markdown('<div class="surface"><div class="card-label">HOW TO READ THE RESULT</div><p><b>Segment</b> is the cluster label predicted by the backend.</p><p><b>Recommendation</b> is a suggested business action associated with that segment.</p><p class="muted">This is a historical-behavior segmentation tool, not a forecast of future customer behavior.</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)
    section_heading("03 · BUSINESS PLAYBOOK", "What each segment is designed to help with", "These are general action themes from the project report. The live recommendation is returned by the API.")
    playbook = [
        ("High-Value Profitable", "Retain valuable customers", "Prioritize loyalty and personalized experiences; avoid unnecessary discounting."),
        ("High-Revenue / Low-Profit", "Investigate margin leakage", "Review product mix, discounts, fulfilment costs, and pricing before chasing more sales."),
        ("At-Risk Valuable", "Reactivate inactive customers", "Prioritize win-back outreach to customers with strong historical value."),
        ("Recent Low-Value", "Encourage a second purchase", "Use relevant follow-ups, cross-sell suggestions, and onboarding offers."),
        ("Discount-Sensitive", "Reduce blanket discounting", "Test targeted offers and bundles rather than relying on broad discounts."),
    ]
    cols = st.columns(5, gap="small")
    for col, (name, goal, action) in zip(cols, playbook):
        with col:
            st.markdown(
                f'<div class="surface"><div class="card-label">SEGMENT</div>'
                f'<div style="font-size:1rem;font-weight:850;margin:.45rem 0 .6rem;line-height:1.2">{name}</div>'
                f'<div style="font-size:.82rem;color:#35674d;font-weight:800;margin-bottom:.45rem">{goal}</div>'
                f'<div class="muted">{action}</div></div>',
                unsafe_allow_html=True,
            )

    with st.expander("About the model and its limitations"):
        st.markdown(
            """
            - The project uses six customer-level features and K-Means to define five segments.
            - A Random Forest classifier predicts the K-Means label; its accuracy measures reproduction of those labels, not independent proof of business value.
            - Inputs should be prepared using the same feature definitions and units as the training data.
            - Confirm the deployed scaler, model artifacts, and cluster-to-name mapping all come from the same corrected training run.
            """
        )
        st.markdown(f"**API base URL:** `{API_URL}`  ")
        st.markdown("**Endpoints used:** `GET /health` and `POST /predict`.")
        if st.button("Check API connection again", use_container_width=False):
            st.rerun()

    st.markdown('<div class="footer">Customer Signals · One-page customer segmentation workspace · Streamlit + FastAPI</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
