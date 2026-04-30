import streamlit as st


def setup_page():
    """Sets up the Streamlit page configuration and clean light theme CSS."""
    st.set_page_config(
        page_title="FinAI — Financial Analyzer",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

        /* === GLOBAL === */
        .stApp {
            background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 40%, #e8eef5 100%);
            color: #1a1a2e;
            font-family: 'DM Sans', sans-serif;
        }

        h1, h2, h3, h4 {
            font-family: 'DM Sans', sans-serif !important;
            font-weight: 700 !important;
            color: #1a1a2e !important;
        }

        /* === HERO === */
        .hero-title {
            font-size: 3rem;
            font-weight: 700;
            text-align: center;
            color: #1a1a2e;
            margin-bottom: 4px;
        }
        .hero-title .accent {
            color: #2563eb;
        }
        .hero-sub {
            text-align: center;
            color: #64748b;
            font-size: 1.05rem;
            font-weight: 400;
            margin-bottom: 2rem;
        }

        /* === SIDEBAR === */
        section[data-testid="stSidebar"] {
            background-color: #f8fafc;
            border-right: 1px solid #e2e8f0;
        }
        section[data-testid="stSidebar"] h2 {
            color: #2563eb !important;
        }
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stMarkdown li {
            color: #475569;
        }

        /* === METRIC CARDS === */
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
            transition: all 0.25s ease;
        }
        .metric-card:hover {
            border-color: #2563eb;
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.10);
            transform: translateY(-2px);
        }
        .metric-label {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #94a3b8;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1e293b;
            font-family: 'JetBrains Mono', monospace;
        }
        .metric-delta {
            font-size: 0.78rem;
            color: #64748b;
            margin-top: 4px;
        }

        /* === VALUATION CARDS === */
        .val-card {
            background: linear-gradient(145deg, #eff6ff 0%, #f0f4ff 100%);
            border: 1px solid #bfdbfe;
            border-radius: 16px;
            padding: 32px 28px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.06);
            transition: all 0.3s ease;
        }
        .val-card:hover {
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.12);
            border-color: #2563eb;
            transform: translateY(-2px);
        }
        .val-label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: #64748b;
        }
        .val-amount {
            font-size: 2.3rem;
            font-weight: 700;
            color: #1e293b;
            font-family: 'JetBrains Mono', monospace;
            margin: 10px 0 6px;
        }
        .val-desc {
            font-size: 0.8rem;
            color: #94a3b8;
            line-height: 1.4;
        }

        /* === INFO CARDS === */
        .info-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 24px;
            min-height: 180px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .info-card-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
        }
        .info-card-body {
            color: #64748b;
            font-size: 0.88rem;
            line-height: 1.8;
        }

        /* === COMPANY HEADER === */
        .company-bar {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 16px 0;
        }
        .company-name {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1e293b;
        }
        .fy-badge {
            background-color: #2563eb;
            color: #ffffff;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        /* === SECTION HEADERS === */
        .section-head {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1e293b;
            margin: 36px 0 18px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* === SUPPORTED DOCS === */
        .supported-docs {
            text-align: center;
            padding: 10px 0 4px;
            color: #94a3b8;
            font-size: 0.8rem;
        }
        .supported-docs span {
            display: inline-block;
            background-color: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 3px 10px;
            margin: 0 3px;
            font-size: 0.75rem;
            font-weight: 500;
            color: #64748b;
        }

        /* === TRUST FOOTER === */
        .trust-footer {
            text-align: center;
            padding: 40px 0 20px;
            margin-top: 48px;
            border-top: 1px solid #e2e8f0;
        }
        .trust-footer .trust-badges {
            display: flex;
            justify-content: center;
            gap: 32px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .trust-footer .trust-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #64748b;
            font-size: 0.82rem;
            font-weight: 500;
        }
        .trust-footer .trust-badge .badge-icon {
            font-size: 1.1rem;
        }
        .trust-footer .trust-legal {
            color: #94a3b8;
            font-size: 0.72rem;
            margin-top: 12px;
            line-height: 1.5;
        }

        /* === BUTTONS === */
        .stButton > button {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.5rem;
            font-family: 'DM Sans', sans-serif;
            font-weight: 600;
            font-size: 0.95rem;
            transition: background-color 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #1d4ed8;
        }

        /* === INPUTS === */
        .stTextInput > div > div > input {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            color: #1e293b;
        }
        .stTextInput > div > div > input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
        }

        /* === FILE UPLOADER === */
        .stFileUploader {
            border: 2px dashed #cbd5e1;
            border-radius: 14px;
            padding: 20px;
            background-color: #ffffff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            transition: border-color 0.2s ease;
        }
        .stFileUploader:hover {
            border-color: #93c5fd;
        }

        /* === DIVIDERS === */
        hr {
            border-color: #e2e8f0 !important;
        }

        /* === VERDICT CARD === */
        .verdict-card {
            border-radius: 14px;
            padding: 28px;
            text-align: center;
            margin-top: 16px;
        }
        .verdict-buy {
            background-color: #f0fdf4;
            border: 2px solid #22c55e;
        }
        .verdict-sell {
            background-color: #fef2f2;
            border: 2px solid #ef4444;
        }
        .verdict-hold {
            background-color: #fffbeb;
            border: 2px solid #f59e0b;
        }
        .verdict-signal {
            font-size: 2rem;
            font-weight: 800;
            margin: 8px 0;
        }
        .verdict-signal.buy { color: #16a34a; }
        .verdict-signal.sell { color: #dc2626; }
        .verdict-signal.hold { color: #d97706; }
        .verdict-price {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.3rem;
            font-weight: 600;
            color: #1e293b;
            margin: 6px 0;
        }
        .verdict-explain {
            font-size: 0.88rem;
            color: #64748b;
            line-height: 1.6;
            margin-top: 10px;
        }

        /* === NEWS CARDS === */
        .news-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #2563eb;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
            transition: all 0.25s ease;
        }
        .news-card:hover {
            border-left-color: #7c3aed;
            box-shadow: 0 6px 20px rgba(37,99,235,0.10);
            transform: translateY(-2px);
        }
        .news-title a {
            font-size: 0.93rem;
            font-weight: 600;
            color: #1e293b;
            text-decoration: none;
            line-height: 1.45;
        }
        .news-title a:hover {
            color: #2563eb;
        }
        .news-meta {
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 6px;
        }
        .news-meta span {
            margin-right: 10px;
        }

        /* === QUARTERLY ANALYSIS CARDS === */
        .pros-card {
            background: linear-gradient(145deg, #f0fdf4 0%, #ecfdf5 100%);
            border: 1px solid #86efac;
            border-radius: 16px;
            padding: 28px 24px;
            box-shadow: 0 2px 8px rgba(34, 197, 94, 0.08);
            transition: all 0.3s ease;
        }
        .pros-card:hover {
            box-shadow: 0 8px 24px rgba(34, 197, 94, 0.14);
            transform: translateY(-2px);
        }
        .cons-card {
            background: linear-gradient(145deg, #fef2f2 0%, #fff1f2 100%);
            border: 1px solid #fca5a5;
            border-radius: 16px;
            padding: 28px 24px;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.08);
            transition: all 0.3s ease;
        }
        .cons-card:hover {
            box-shadow: 0 8px 24px rgba(239, 68, 68, 0.14);
            transform: translateY(-2px);
        }
        .trajectory-card {
            background: linear-gradient(145deg, #eff6ff 0%, #eef2ff 100%);
            border: 1px solid #93c5fd;
            border-radius: 16px;
            padding: 28px 24px;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.08);
            transition: all 0.3s ease;
        }
        .trajectory-card:hover {
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.14);
            transform: translateY(-2px);
        }
        .pc-card-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0,0,0,0.06);
        }
        .pc-card-title.pros { color: #16a34a; }
        .pc-card-title.cons { color: #dc2626; }
        .pc-card-title.trajectory { color: #2563eb; }
        .pc-bullet {
            font-size: 0.88rem;
            color: #475569;
            line-height: 1.9;
        }
        .quarter-badge {
            display: inline-block;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            color: #ffffff;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 0 4px 6px 0;
        }
        .growth-positive {
            color: #16a34a;
            font-weight: 600;
        }
        .growth-negative {
            color: #dc2626;
            font-weight: 600;
        }

        /* === TOOLTIP === */
        .info-tooltip {
            display: inline-block;
            position: relative;
            cursor: pointer;
            color: #94a3b8;
            font-size: 0.85rem;
            margin-left: 4px;
            vertical-align: middle;
        }
        .info-tooltip .info-tooltip-text {
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 130%;
            left: 50%;
            transform: translateX(-50%);
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 400;
            line-height: 1.5;
            width: 260px;
            text-align: left;
            text-transform: none;
            letter-spacing: normal;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: opacity 0.2s ease;
            z-index: 100;
        }
        .info-tooltip .info-tooltip-text::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #1e293b transparent transparent transparent;
        }
        .info-tooltip:hover .info-tooltip-text {
            visibility: visible;
            opacity: 1;
        }

        /* Hide defaults */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


def format_number(num):
    """Formats large numbers into readable strings."""
    if num is None:
        return "N/A"
    try:
        num = float(num)
    except (ValueError, TypeError):
        return str(num)
    if abs(num) >= 1e12:
        return f"${num / 1e12:.2f}T"
    if abs(num) >= 1e9:
        return f"${num / 1e9:.2f}B"
    if abs(num) >= 1e6:
        return f"${num / 1e6:.2f}M"
    if abs(num) >= 1e3:
        return f"${num / 1e3:.1f}K"
    return f"${num:.2f}"


def create_metric_card(label, value, delta=None):
    """Creates a clean light-themed metric card."""
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def create_valuation_card(label, amount, description, tooltip=None):
    """Creates a valuation card with blue accent and optional info tooltip."""
    tooltip_html = ""
    if tooltip:
        tooltip_html = f'''
        <span class="info-tooltip">ⓘ
            <span class="info-tooltip-text">{tooltip}</span>
        </span>'''
    st.markdown(f"""
    <div class="val-card">
        <div class="val-label">{label} {tooltip_html}</div>
        <div class="val-amount">{amount}</div>
        <div class="val-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def create_info_card(title, content, icon="📊"):
    """Creates an info card for risks/notes."""
    st.markdown(f"""
    <div class="info-card">
        <div class="info-card-title">{icon} {title}</div>
        <div class="info-card-body">{content}</div>
    </div>
    """, unsafe_allow_html=True)
