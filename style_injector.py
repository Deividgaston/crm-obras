import streamlit as st


def inject_apple_style():
    """
    Estilo Salesforce Lightning Design System (SLDS) REAL.
    Basado en los tokens oficiales de Salesforce:
    https://www.lightningdesignsystem.com/
    """

    if st.session_state.get("crm_style_injected"):
        return
    st.session_state["crm_style_injected"] = True

    style = """
    <style>

    /* ===========================================================
       🔵 BASE GLOBAL — SLDS Tokens
       =========================================================== */
    html, body, .stApp, [class*="css"] {
        --slds-color-brand: #0170D2;
        --slds-color-brand-dark: #014486;
        --slds-color-brand-light: #E8F3FF;

        --slds-color-text-default: #032D60;
        --slds-color-text-weak: #5A6872;
        --slds-color-text-inverse: #FFFFFF;

        --slds-color-background: #F3F6FB;
        --slds-color-background-card: #FFFFFF;
        --slds-color-border: #D8E6FF;

        --slds-radius-small: 4px;
        --slds-radius-medium: 6px;

        --slds-shadow-card: 0 1px 2px rgba(3, 45, 96, 0.12);

        background-color: var(--slds-color-background) !important;
        color: var(--slds-color-text-default) !important;

        font-family: "Salesforce Sans", "Segoe UI", sans-serif !important;
        font-size: 14px !important;
    }

    /* CENTER CONTENT */
    .block-container {
        max-width: 1250px !important;
        margin: 0 auto !important;
        padding-top: 0.5rem !important;
    }

    /* ===========================================================
       🔵 TOP BAR — Lightning Header
       =========================================================== */
    .crm-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;

        padding: 10px 6px;
        background: var(--slds-color-background-card);
        border-bottom: 1px solid var(--slds-color-border);

        box-shadow: 0 1px 2px rgba(3, 45, 96, 0.04);
    }

    .crm-topbar-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--slds-color-brand);
    }

    .crm-topbar-subtitle {
        font-size: 12.5px;
        color: var(--slds-color-text-weak);
    }

    /* ===========================================================
       🔵 NAV PILLS — Lightning Tabs Feel
       =========================================================== */
    .crm-nav-pill {
        padding: 6px 14px;
        border-radius: var(--slds-radius-small);
        background: var(--slds-color-brand-light);
        color: var(--slds-color-brand-dark);
        border: 1px solid var(--slds-color-border);
        cursor: pointer;
        font-size: 13px;
    }

    .crm-nav-pill-active {
        background: var(--slds-color-brand);
        color: var(--slds-color-text-inverse);
        border-color: var(--slds-color-brand-dark);
    }

    .crm-nav-pill:hover {
        filter: brightness(0.95);
    }

    /* ===========================================================
       🔵 CARDS — SLDS Card
       =========================================================== */
    .apple-card,
    .apple-card-light {
        background: var(--slds-color-background-card);
        border-radius: var(--slds-radius-medium);
        padding: 14px 16px;
        border: 1px solid var(--slds-color-border);
        box-shadow: var(--slds-shadow-card);
        margin-bottom: 14px;
    }

    .badge {
        background: var(--slds-color-brand-light);
        color: var(--slds-color-brand-dark);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 11px;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .apple-card h1, .apple-card h2, .apple-card h3 {
        font-weight: 600;
        margin: 4px 0 6px 0;
        color: var(--slds-color-text-default);
    }

    /* ===========================================================
       🔵 BUTTONS — SLDS Buttons
       =========================================================== */
    button, .stButton>button {
        border-radius: var(--slds-radius-small) !important;
        padding: 7px 16px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border: none !important;
        background: var(--slds-color-brand) !important;
        color: white !important;
        box-shadow: 0 1px 2px rgba(1, 112, 210, 0.2);
    }

    button:hover {
        background: var(--slds-color-brand-dark) !important;
    }

    /* Secondary */
    .sf-btn-secondary {
        background: var(--slds-color-background) !important;
        border: 1px solid var(--slds-color-border) !important;
        color: var(--slds-color-brand-dark) !important;
    }

    /* ===========================================================
       🔵 TABLES — SLDS Datatable
       =========================================================== */
    .stDataFrame table {
        border-collapse: separate !important;
        border-spacing: 0 !important;
        background: var(--slds-color-background-card) !important;
    }

    .stDataFrame th {
        background: var(--slds-color-brand-light) !important;
        color: var(--slds-color-brand-dark) !important;
        font-size: 13px !important;
        padding: 6px !important;
        border-bottom: 1px solid var(--slds-color-border) !important;
    }

    .stDataFrame td {
        font-size: 13px !important;
        padding: 6px !important;
        border-bottom: 1px solid #E4ECF7 !important;
        color: var(--slds-color-text-default) !important;
    }

    .stDataFrame tr:nth-child(even) {
        background: #F8FAFF !important;
    }

    /* ===========================================================
       🔵 METRICS — Lightning Summary Numbers
       =========================================================== */
    .metric-card {
        background: var(--slds-color-background-card);
        border: 1px solid var(--slds-color-border);
        border-radius: var(--slds-radius-medium);
        padding: 10px 12px;
        box-shadow: var(--slds-shadow-card);
        min-width: 130px;
    }

    .metric-title {
        font-size: 11px;
        color: var(--slds-color-text-weak);
        text-transform: uppercase;
        margin-bottom: 2px;
    }

    .metric-value {
        font-size: 19px;
        color: var(--slds-color-text-default);
        font-weight: 600;
    }

    /* ===========================================================
       🔵 LIST ITEMS — Lightning List Item
       =========================================================== */
    .next-item {
        background: var(--slds-color-background-card);
        border: 1px solid var(--slds-color-border);
        border-radius: var(--slds-radius-small);
        padding: 10px 12px;
        margin-bottom: 6px;
        box-shadow: var(--slds-shadow-card);
    }

    .next-item strong {
        color: var(--slds-color-text-default);
    }

    .next-item small {
        font-size: 12px;
        color: var(--slds-color-text-weak);
    }

    /* ===========================================================
       🔥 OCULTAR ELEMENTOS DE STREAMLIT
       =========================================================== */
    #MainMenu, header, footer, .stDeployButton, .stStatusWidget {
        visibility: hidden !important;
        height: 0 !important;
    }

    </style>
    """

    st.markdown(style, unsafe_allow_html=True)
