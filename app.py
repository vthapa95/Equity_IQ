import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from financial_analyzer import FinancialAnalyzer
from utils import (
    setup_page, format_number,
    create_metric_card, create_valuation_card, create_info_card
)

load_dotenv()


def safe_num(val, default=0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def display_results(metrics, valuation, analyzer):
    """Shared results dashboard for PDF and Ticker modes."""
    st.markdown("---")

    company = metrics.get("Company Name", "Unknown")
    fy = metrics.get("Fiscal Year", "N/A")
    currency = metrics.get("Currency", "USD")
    st.markdown(f"""
    <div class="company-header">
        <span class="company-name">🏢 {company}</span>
        <span class="fy-badge">FY {fy} · {currency}</span>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics
    st.markdown('<div class="section-head">📊 Key Financials</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        create_metric_card("Revenue", format_number(metrics.get("Revenue")))
    with c2:
        create_metric_card("Net Income", format_number(metrics.get("Net Income")))
    with c3:
        eps_val = metrics.get("EPS")
        create_metric_card("EPS", f"${eps_val}" if eps_val is not None else "N/A")
    with c4:
        create_metric_card("Free Cash Flow", format_number(metrics.get("Free Cash Flow")))

    # Valuation
    st.markdown('<div class="section-head">💎 Intrinsic Valuation</div>', unsafe_allow_html=True)
    v1, v2 = st.columns(2)
    with v1:
        dcf = valuation.get("DCF Value", 0)
        growth = valuation.get("Assumptions", {}).get("Growth Rate", "5.0%")
        create_valuation_card(
            "DCF Model", f"${dcf:,.2f}",
            f"5-year projection · {growth} growth · 10% discount",
            tooltip="Discounted Cash Flow (DCF) estimates a company's value by projecting its future cash flows and discounting them back to today's value using a required rate of return."
        )
    with v2:
        graham = valuation.get("Graham Number", 0)
        bvps = valuation.get("Book Value Per Share", 0)
        create_valuation_card(
            "Graham Number", f"${graham:,.2f}",
            f"BVPS: ${bvps:,.2f} · Conservative estimate",
            tooltip="The Graham Number, developed by Benjamin Graham, calculates the maximum fair price for a stock using its EPS and book value per share. Formula: √(22.5 × EPS × BVPS)"
        )

    # Chart
    st.markdown('<div class="section-head">📈 Financial Snapshot</div>', unsafe_allow_html=True)
    chart_keys = ["Revenue", "Net Income", "Free Cash Flow", "Total Assets", "Total Liabilities"]
    labels = ["Revenue", "Net Income", "FCF", "Assets", "Liabilities"]
    values = [safe_num(metrics.get(k)) for k in chart_keys]
    colors = ['#2563eb', '#0891b2', '#7c3aed', '#059669', '#dc2626']

    fig = go.Figure(data=[go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, line=dict(color='rgba(255,255,255,0.1)', width=1)),
        hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'
    )])
    fig.update_layout(
        template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="DM Sans", size=13, color="#475569"),
        xaxis=dict(gridcolor='#f1f5f9'), yaxis=dict(gridcolor='#f1f5f9'),
        margin=dict(l=20, r=20, t=20, b=40), height=350, hovermode="x unified"
    )
    st.plotly_chart(fig, width="stretch")

    # Risk & Notes
    st.markdown('<div class="section-head">📋 Analysis Details</div>', unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    with r1:
        risks = metrics.get("Risk Factors", [])
        risk_html = "<br>".join([f"• {r}" for r in risks]) if risks else "No risks identified"
        create_info_card("Risk Factors", risk_html, "⚠️")
    with r2:
        notes = metrics.get("Notes", "No additional notes.")
        create_info_card("AI Analyst Notes", notes, "📝")

    # News
    ticker = metrics.get("Ticker", "")
    if ticker:
        news_articles = analyzer.get_recent_news(ticker, max_items=3)
        if news_articles:
            st.markdown('<div class="section-head">📰 Latest News</div>', unsafe_allow_html=True)
            for article in news_articles:
                pub = article.get("published", "")
                pub_str = f'<span>🕒 {pub}</span>' if pub else ""
                st.markdown(f"""
                <div class="news-card">
                    <div class="news-title"><a href="{article['link']}" target="_blank">{article['title']}</a></div>
                    <div class="news-meta">
                        <span>📰 {article['publisher']}</span>{pub_str}
                        <span><a href="{article['link']}" target="_blank" style="color:#2563eb;font-size:0.73rem;">Read more →</a></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Verdict
    if ticker:
        st.markdown('<div class="section-head">🎯 Investment Verdict</div>', unsafe_allow_html=True)
        current_price = analyzer.get_current_price(ticker)
        if current_price is not None:
            dcf_val = safe_num(valuation.get("DCF Value"))
            graham_val = safe_num(valuation.get("Graham Number"))
            avg_intrinsic = 0
            count = 0
            if dcf_val > 0:
                avg_intrinsic += dcf_val
                count += 1
            if graham_val > 0:
                avg_intrinsic += graham_val
                count += 1
            avg_intrinsic = avg_intrinsic / count if count > 0 else 0

            if avg_intrinsic > 0:
                margin = ((avg_intrinsic - current_price) / current_price) * 100
                if margin > 15:
                    signal, signal_class, card_class, emoji = "BUY", "buy", "verdict-buy", "🟢"
                    explanation = f"The stock appears <b>undervalued</b>. Fair value (${avg_intrinsic:,.2f}) is <b>{margin:.1f}% above</b> market price."
                elif margin < -15:
                    signal, signal_class, card_class, emoji = "SELL / AVOID", "sell", "verdict-sell", "🔴"
                    explanation = f"The stock appears <b>overvalued</b>. Price is <b>{abs(margin):.1f}% above</b> fair value (${avg_intrinsic:,.2f})."
                else:
                    signal, signal_class, card_class, emoji = "HOLD", "hold", "verdict-hold", "🟡"
                    explanation = f"Trading <b>near fair value</b> (${avg_intrinsic:,.2f}). No strong signal."

                st.markdown(f"""
                <div class="verdict-card {card_class}">
                    <div style="font-size:0.8rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;">{ticker} · Current Market Price</div>
                    <div class="verdict-price">${current_price:,.2f}</div>
                    <div class="verdict-signal {signal_class}">{emoji} {signal}</div>
                    <div class="verdict-explain">{explanation}</div>
                    <div style="margin-top:14px;font-size:0.75rem;color:#94a3b8;">⚠️ Not financial advice. Always do your own research.</div>
                </div>
                """, unsafe_allow_html=True)

    # Trust Footer
    st.markdown("""
    <div class="trust-footer">
        <div class="trust-badges">
            <div class="trust-badge"><span class="badge-icon">🔒</span> Data never stored</div>
            <div class="trust-badge"><span class="badge-icon">⚡</span> Powered by Gemini AI</div>
            <div class="trust-badge"><span class="badge-icon">📊</span> DCF & Graham Models</div>
            <div class="trust-badge"><span class="badge-icon">🌐</span> Real-time pricing</div>
        </div>
        <div class="trust-legal">
            FinAI Pro is for educational and informational purposes only. Not financial advice.<br>
            Always consult a qualified financial advisor before making investment decisions.
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    setup_page()

    # --- Sidebar ---
    with st.sidebar:
        st.markdown("## 💎 FinAI Pro")
        st.caption("AI-Powered Financial Intelligence")
        st.markdown("---")

        env_key = os.getenv("GEMINI_API_KEY")
        if env_key and len(env_key) > 10:
            api_key = env_key
            st.success("✅ API Key loaded")
        else:
            api_key = st.text_input("Gemini API Key", type="password", help="Get free key at aistudio.google.com")
            if not api_key:
                st.markdown("[🔑 Get Free API Key →](https://aistudio.google.com/app/apikey)")

        st.markdown("---")
        st.markdown("#### 🧭 Navigate")
        mode = st.radio(
            "Choose a feature",
            ["📄 Upload PDF", "🔍 Ticker Lookup", "⚖️ Compare Stocks", "📊 Quarterly Analysis"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("#### How It Works")
        st.markdown("""
        1. 📄 Upload report, enter ticker, or compare
        2. 🤖 AI / Yahoo Finance extracts data
        3. 📊 View valuation, verdict & quarterly trends
        """)

    # --- Hero ---
    st.markdown('<div class="hero-title">Fin<span class="accent">AI</span> Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Upload a report, look up a ticker, compare stocks, or analyze quarterly trends.</div>', unsafe_allow_html=True)

    # --- Three Tabs (synced with sidebar) ---
    tab_list = ["📄 Upload PDF", "🔍 Ticker Lookup", "⚖️ Compare Stocks", "📊 Quarterly Analysis"]
    default_idx = tab_list.index(mode)
    tabs = st.tabs(tab_list)

    # =====================
    # TAB 1: PDF Upload
    # =====================
    with tabs[0]:
        uploaded_file = st.file_uploader("Upload Financial Report (PDF)", type="pdf")
        st.markdown("""
        <div class="supported-docs">
            Supported: <span>10-K Annual Reports</span> <span>10-Q Quarterly</span> <span>Annual Reports</span> <span>Investor Presentations</span>
        </div>
        """, unsafe_allow_html=True)

        if uploaded_file and api_key:
            analyzer = FinancialAnalyzer(api_key)
            if st.button("🚀 Analyze Report", key="pdf_btn"):
                progress = st.progress(0)
                status = st.empty()

                status.info("📄 Extracting text from PDF...")
                progress.progress(15)
                text, error = analyzer.extract_text_from_pdf(uploaded_file)
                if error:
                    st.error(error)
                    progress.empty()
                    status.empty()
                    return

                progress.progress(35)
                status.info("🧠 AI is analyzing financials...")
                metrics = analyzer.analyze_financials(text)
                progress.progress(75)
                if "error" in metrics:
                    st.error(f"Analysis Error: {metrics['error']}")
                    progress.empty()
                    status.empty()
                    return

                status.info("💎 Computing intrinsic value...")
                valuation = analyzer.calculate_intrinsic_value(metrics)
                progress.progress(100)
                status.empty()
                progress.empty()
                display_results(metrics, valuation, analyzer)

        elif not api_key:
            st.info("👈 Enter your Gemini API Key in the sidebar to get started.")

    # =====================
    # TAB 2: Ticker Lookup
    # =====================
    with tabs[1]:
        st.markdown('<div style="text-align:center;color:#64748b;font-size:0.92rem;margin-bottom:8px;">Enter any stock ticker to pull <b>live financial data</b> from Yahoo Finance.</div>', unsafe_allow_html=True)

        col_input, col_btn = st.columns([3, 1])
        with col_input:
            ticker_input = st.text_input("Stock Ticker", placeholder="e.g.  AAPL,  TSLA,  RELIANCE.NS", label_visibility="collapsed")
        with col_btn:
            ticker_go = st.button("🔍 Analyze", key="ticker_btn")

        st.markdown("""
        <div class="supported-docs">
            Examples: <span>AAPL</span> <span>TSLA</span> <span>GOOGL</span> <span>MSFT</span> <span>RELIANCE.NS</span> <span>TCS.NS</span> <span>INFY.NS</span>
        </div>
        """, unsafe_allow_html=True)

        if ticker_go and ticker_input:
            ticker_clean = ticker_input.strip().upper()
            dummy_key = api_key if api_key else "ticker-mode"
            try:
                analyzer = FinancialAnalyzer(dummy_key)
            except ValueError:
                analyzer = None

            progress = st.progress(0)
            status = st.empty()
            status.info(f"🌐 Fetching live data for **{ticker_clean}**...")
            progress.progress(30)

            metrics, error = analyzer.fetch_stock_data(ticker_clean) if analyzer else (None, "Internal error")
            if error:
                st.error(f"❌ {error}")
                progress.empty()
                status.empty()
            else:
                progress.progress(70)
                status.info("💎 Computing valuation...")
                valuation = analyzer.calculate_intrinsic_value(metrics)
                progress.progress(100)
                status.empty()
                progress.empty()
                display_results(metrics, valuation, analyzer)

        elif ticker_go and not ticker_input:
            st.warning("Please enter a stock ticker symbol.")

    # =====================
    # TAB 3: Compare Stocks
    # =====================
    with tabs[2]:
        st.markdown('<div style="text-align:center;color:#64748b;font-size:0.92rem;margin-bottom:12px;">Add stock tickers and compare them side-by-side.</div>', unsafe_allow_html=True)

        # Dynamic ticker count via session state
        if "compare_count" not in st.session_state:
            st.session_state.compare_count = 2

        # Render ticker inputs
        input_cols = st.columns(list([3] * st.session_state.compare_count) + [1])
        ticker_values = []
        for i in range(st.session_state.compare_count):
            with input_cols[i]:
                val = st.text_input(f"Stock {i+1}", placeholder=f"e.g. {'AAPL' if i==0 else 'MSFT' if i==1 else 'GOOGL'}", key=f"cmp_{i}")
                ticker_values.append(val)
        with input_cols[-1]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)  # spacer to align with inputs
            if st.button("➕", key="add_ticker", help="Add another stock"):
                st.session_state.compare_count += 1
                st.rerun()

        # Compare + Remove buttons row
        btn_cols = st.columns([2, 1])
        with btn_cols[0]:
            compare_go = st.button("⚖️ Compare", key="compare_btn")
        with btn_cols[1]:
            if st.session_state.compare_count > 2:
                if st.button("➖ Remove last", key="remove_ticker"):
                    st.session_state.compare_count -= 1
                    st.rerun()

        st.markdown("""
        <div class="supported-docs">
            US: <span>AAPL</span> <span>MSFT</span> <span>TSLA</span>
            India: <span>RELIANCE.NS</span> <span>TCS.NS</span> <span>INFY.NS</span>
        </div>
        """, unsafe_allow_html=True)

        if compare_go:
            tickers = [t.strip().upper() for t in ticker_values if t and t.strip()]
            if len(tickers) < 2:
                st.warning("Please enter at least 2 tickers to compare.")
            else:
                dummy_key = api_key if api_key else "ticker-mode"
                try:
                    analyzer = FinancialAnalyzer(dummy_key)
                except ValueError:
                    st.error("Could not initialize analyzer.")
                    analyzer = None

                if analyzer:
                    progress = st.progress(0)
                    status = st.empty()
                    all_data = []

                    for i, tk in enumerate(tickers):
                        status.info(f"🌐 Fetching data for **{tk}**... ({i+1}/{len(tickers)})")
                        progress.progress(int((i + 1) / (len(tickers) + 1) * 80))
                        m, err = analyzer.fetch_stock_data(tk)
                        if err:
                            st.warning(f"⚠️ Could not fetch {tk}: {err}")
                        else:
                            val = analyzer.calculate_intrinsic_value(m)
                            price = analyzer.get_current_price(tk)
                            all_data.append({"ticker": tk, "metrics": m, "valuation": val, "price": price})

                    progress.progress(100)
                    status.empty()
                    progress.empty()

                    if len(all_data) < 2:
                        st.error("Need data for at least 2 stocks to compare.")
                    else:
                        st.markdown("---")
                        st.markdown('<div class="section-head">⚖️ Comparison Table</div>', unsafe_allow_html=True)

                        # --- Build comparison table ---
                        rows = []
                        for d in all_data:
                            m, v, p = d["metrics"], d["valuation"], d["price"]
                            dcf_v = safe_num(v.get("DCF Value"))
                            graham_v = safe_num(v.get("Graham Number"))
                            avg_fair = 0
                            cnt = 0
                            if dcf_v > 0:
                                avg_fair += dcf_v
                                cnt += 1
                            if graham_v > 0:
                                avg_fair += graham_v
                                cnt += 1
                            avg_fair = avg_fair / cnt if cnt > 0 else 0

                            if p and avg_fair > 0:
                                upside = ((avg_fair - p) / p) * 100
                                verdict = "🟢 BUY" if upside > 15 else ("🔴 SELL" if upside < -15 else "🟡 HOLD")
                            else:
                                upside, verdict = 0, "⚪ N/A"

                            rows.append({
                                "Ticker": d["ticker"],
                                "Company": m.get("Company Name", "—"),
                                "Price": f"${p:,.2f}" if p else "N/A",
                                "Revenue": format_number(m.get("Revenue")),
                                "Net Income": format_number(m.get("Net Income")),
                                "EPS": f"${safe_num(m.get('EPS')):.2f}",
                                "DCF Value": f"${dcf_v:,.2f}",
                                "Graham #": f"${graham_v:,.2f}",
                                "Upside": f"{upside:+.1f}%",
                                "Verdict": verdict
                            })

                        df = pd.DataFrame(rows)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # --- Grouped Bar Chart ---
                        st.markdown('<div class="section-head">📊 Visual Comparison</div>', unsafe_allow_html=True)
                        compare_keys = ["Revenue", "Net Income", "Free Cash Flow", "Total Assets"]
                        bar_colors = ['#2563eb', '#0891b2', '#7c3aed', '#059669']

                        fig = go.Figure()
                        for i, d in enumerate(all_data):
                            m = d["metrics"]
                            vals = [safe_num(m.get(k)) for k in compare_keys]
                            fig.add_trace(go.Bar(
                                name=d["ticker"],
                                x=["Revenue", "Net Income", "FCF", "Assets"],
                                y=vals,
                                marker_color=bar_colors[i % len(bar_colors)],
                                hovertemplate='%{x}<br>$%{y:,.0f}<extra>' + d["ticker"] + '</extra>'
                            ))

                        fig.update_layout(
                            barmode='group', template="plotly_white",
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(family="DM Sans", size=13, color="#475569"),
                            xaxis=dict(gridcolor='#f1f5f9'), yaxis=dict(gridcolor='#f1f5f9'),
                            margin=dict(l=20, r=20, t=20, b=40), height=400,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig, width="stretch")

                        # --- Verdict Cards ---
                        st.markdown('<div class="section-head">🎯 Verdict</div>', unsafe_allow_html=True)
                        verdict_cols = st.columns(len(all_data))
                        for i, d in enumerate(all_data):
                            with verdict_cols[i]:
                                v, p = d["valuation"], d["price"]
                                dcf_v = safe_num(v.get("DCF Value"))
                                graham_v = safe_num(v.get("Graham Number"))
                                avg_fair = 0
                                cnt = 0
                                if dcf_v > 0:
                                    avg_fair += dcf_v
                                    cnt += 1
                                if graham_v > 0:
                                    avg_fair += graham_v
                                    cnt += 1
                                avg_fair = avg_fair / cnt if cnt > 0 else 0

                                if p and avg_fair > 0:
                                    margin = ((avg_fair - p) / p) * 100
                                    if margin > 15:
                                        card_cls, sig = "verdict-buy", "🟢 BUY"
                                    elif margin < -15:
                                        card_cls, sig = "verdict-sell", "🔴 SELL"
                                    else:
                                        card_cls, sig = "verdict-hold", "🟡 HOLD"
                                    price_str = f"${p:,.2f}"
                                    fair_str = f"Fair Value: ${avg_fair:,.2f}"
                                else:
                                    card_cls, sig = "verdict-hold", "⚪ N/A"
                                    price_str, fair_str = "N/A", "Insufficient data"

                                st.markdown(f"""
                                <div class="verdict-card {card_cls}" style="padding:20px;">
                                    <div style="font-size:1.1rem;font-weight:700;color:#1e293b;">{d['ticker']}</div>
                                    <div class="verdict-price">{price_str}</div>
                                    <div class="verdict-signal" style="font-size:1.5rem;">{sig}</div>
                                    <div style="font-size:0.82rem;color:#64748b;">{fair_str}</div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Trust Footer
                        st.markdown("""
                        <div class="trust-footer">
                            <div class="trust-badges">
                                <div class="trust-badge"><span class="badge-icon">🔒</span> Data never stored</div>
                                <div class="trust-badge"><span class="badge-icon">⚡</span> Powered by Gemini AI</div>
                                <div class="trust-badge"><span class="badge-icon">📊</span> DCF & Graham Models</div>
                                <div class="trust-badge"><span class="badge-icon">🌐</span> Real-time pricing</div>
                            </div>
                            <div class="trust-legal">
                                FinAI Pro is for educational and informational purposes only. Not financial advice.<br>
                                Always consult a qualified financial advisor before making investment decisions.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # =============================
    # TAB 4: Quarterly Analysis
    # =============================
    with tabs[3]:
        st.markdown('<div style="text-align:center;color:#64748b;font-size:0.92rem;margin-bottom:8px;">Upload <b>2–8 quarterly reports</b> (PDFs) to track growth and get AI pros & cons.</div>', unsafe_allow_html=True)

        q_files = st.file_uploader(
            "Upload Quarterly Reports (PDF)", type="pdf",
            accept_multiple_files=True, key="quarterly_uploader"
        )
        st.markdown("""
        <div class="supported-docs">
            Upload in order: <span>Q1</span> <span>Q2</span> <span>Q3</span> <span>Q4</span>
            &nbsp;·&nbsp; Supported: <span>10-Q</span> <span>Quarterly Reports</span> <span>Investor Updates</span>
        </div>
        """, unsafe_allow_html=True)

        if q_files and api_key:
            # Show uploaded file badges
            badge_html = "".join([f'<span class="quarter-badge">📄 {f.name}</span>' for f in q_files])
            st.markdown(f'<div style="margin:10px 0;">{badge_html}</div>', unsafe_allow_html=True)

            if st.button("🚀 Analyze Quarters", key="quarterly_btn"):
                if len(q_files) < 2:
                    st.warning("⚠️ Please upload at least 2 quarterly reports to compare.")
                else:
                    analyzer = FinancialAnalyzer(api_key)
                    progress = st.progress(0)
                    status = st.empty()

                    # Prepare labels
                    pdf_pairs = []
                    for i, f in enumerate(q_files):
                        label = f"Q{i+1}"
                        # Try to extract quarter from filename
                        fname = f.name.upper()
                        for q_tag in ["Q1", "Q2", "Q3", "Q4"]:
                            if q_tag in fname:
                                label = q_tag
                                break
                        pdf_pairs.append((f, label))

                    status.info(f"📄 Analyzing {len(q_files)} quarterly reports...")
                    progress.progress(10)

                    result = analyzer.analyze_quarterly_comparison(pdf_pairs)
                    progress.progress(90)

                    if "error" in result:
                        st.error(f"❌ {result['error']}")
                        progress.empty()
                        status.empty()
                    else:
                        progress.progress(100)
                        status.empty()
                        progress.empty()

                        quarters_data = result["quarters"]
                        growth_data = result["growth"]
                        pros_cons = result["pros_cons"]
                        company_name = result["company_name"]

                        # Show errors for any failed PDFs
                        if result.get("errors"):
                            for e in result["errors"]:
                                st.warning(f"⚠️ {e}")

                        st.markdown("---")

                        # Company header
                        quarter_labels = " · ".join([q.get("Quarter Label", "?") for q in quarters_data])
                        st.markdown(f"""
                        <div class="company-header">
                            <span class="company-name">🏢 {company_name}</span>
                            <span class="fy-badge">{quarter_labels}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # --- Quarterly Metrics Table ---
                        st.markdown('<div class="section-head">📋 Quarterly Metrics</div>', unsafe_allow_html=True)
                        table_rows = []
                        for q in quarters_data:
                            table_rows.append({
                                "Quarter": q.get("Quarter Label", "—"),
                                "Revenue": format_number(q.get("Revenue")),
                                "Net Income": format_number(q.get("Net Income")),
                                "EPS": f"${safe_num(q.get('EPS')):.2f}",
                                "Free Cash Flow": format_number(q.get("Free Cash Flow")),
                                "Total Assets": format_number(q.get("Total Assets")),
                                "Total Liabilities": format_number(q.get("Total Liabilities")),
                            })
                        df_q = pd.DataFrame(table_rows)
                        st.dataframe(df_q, use_container_width=True, hide_index=True)

                        # --- Growth Trend Line Chart ---
                        st.markdown('<div class="section-head">📈 Quarterly Growth Trends</div>', unsafe_allow_html=True)
                        q_labels = [q.get("Quarter Label", f"Q{i+1}") for i, q in enumerate(quarters_data)]
                        trend_keys = ["Revenue", "Net Income", "EPS", "Free Cash Flow"]
                        trend_colors = ['#2563eb', '#0891b2', '#7c3aed', '#059669']

                        fig_trend = go.Figure()
                        for idx, key in enumerate(trend_keys):
                            values = [safe_num(q.get(key)) for q in quarters_data]
                            display_label = "FCF" if key == "Free Cash Flow" else key
                            fig_trend.add_trace(go.Scatter(
                                x=q_labels, y=values,
                                mode='lines+markers',
                                name=display_label,
                                line=dict(color=trend_colors[idx], width=3),
                                marker=dict(size=8),
                                hovertemplate=f'{display_label}<br>%{{x}}: $%{{y:,.0f}}<extra></extra>'
                            ))
                        fig_trend.update_layout(
                            template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(family="DM Sans", size=13, color="#475569"),
                            xaxis=dict(gridcolor='#f1f5f9', title="Quarter"),
                            yaxis=dict(gridcolor='#f1f5f9', title="Value ($)"),
                            margin=dict(l=20, r=20, t=20, b=40), height=400,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)

                        # --- QoQ Growth % Bar Chart ---
                        if growth_data:
                            st.markdown('<div class="section-head">📊 Quarter-over-Quarter Growth (%)</div>', unsafe_allow_html=True)
                            growth_labels = [g["Quarter"] for g in growth_data]
                            growth_keys = ["Revenue", "Net Income", "EPS", "Free Cash Flow"]
                            growth_colors = ['#2563eb', '#0891b2', '#7c3aed', '#059669']

                            fig_growth = go.Figure()
                            for idx, key in enumerate(growth_keys):
                                values = [g.get(key, 0) for g in growth_data]
                                display_label = "FCF" if key == "Free Cash Flow" else key
                                fig_growth.add_trace(go.Bar(
                                    name=display_label,
                                    x=growth_labels, y=values,
                                    marker_color=growth_colors[idx],
                                    hovertemplate=f'{display_label}<br>%{{x}}: %{{y:+.1f}}%<extra></extra>'
                                ))
                            fig_growth.update_layout(
                                barmode='group', template="plotly_white",
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(family="DM Sans", size=13, color="#475569"),
                                xaxis=dict(gridcolor='#f1f5f9', title="Quarter"),
                                yaxis=dict(gridcolor='#f1f5f9', title="Growth %", zeroline=True, zerolinecolor='#94a3b8'),
                                margin=dict(l=20, r=20, t=20, b=40), height=380,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                                hovermode="x unified"
                            )
                            st.plotly_chart(fig_growth, use_container_width=True)

                        # --- Pros & Cons ---
                        st.markdown('<div class="section-head">✅ Pros & ❌ Cons</div>', unsafe_allow_html=True)
                        pc1, pc2 = st.columns(2)
                        with pc1:
                            pros_list = pros_cons.get("pros", [])
                            pros_html = "<br>".join([f"✅ {p}" for p in pros_list])
                            st.markdown(f"""
                            <div class="pros-card">
                                <div class="pc-card-title pros">💪 Strengths & Positives</div>
                                <div class="pc-bullet">{pros_html}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        with pc2:
                            cons_list = pros_cons.get("cons", [])
                            cons_html = "<br>".join([f"⚠️ {c}" for c in cons_list])
                            st.markdown(f"""
                            <div class="cons-card">
                                <div class="pc-card-title cons">⚠️ Weaknesses & Risks</div>
                                <div class="pc-bullet">{cons_html}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # --- Trajectory ---
                        trajectory = pros_cons.get("trajectory", "No trajectory analysis available.")
                        st.markdown(f"""
                        <div class="trajectory-card" style="margin-top:20px;">
                            <div class="pc-card-title trajectory">🧭 Overall Trajectory</div>
                            <div class="pc-bullet">{trajectory}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Trust Footer
                        st.markdown("""
                        <div class="trust-footer">
                            <div class="trust-badges">
                                <div class="trust-badge"><span class="badge-icon">🔒</span> Data never stored</div>
                                <div class="trust-badge"><span class="badge-icon">⚡</span> Powered by Gemini AI</div>
                                <div class="trust-badge"><span class="badge-icon">📊</span> Quarterly Trend Analysis</div>
                                <div class="trust-badge"><span class="badge-icon">📈</span> QoQ Growth Tracking</div>
                            </div>
                            <div class="trust-legal">
                                FinAI Pro is for educational and informational purposes only. Not financial advice.<br>
                                Always consult a qualified financial advisor before making investment decisions.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

        elif q_files and not api_key:
            st.info("👈 Enter your Gemini API Key in the sidebar to analyze quarterly reports.")
        elif not q_files:
            st.markdown("""
            <div style="text-align:center; padding:40px 0; color:#94a3b8;">
                <div style="font-size:3rem; margin-bottom:10px;">📊</div>
                <div style="font-size:1rem; font-weight:500;">Upload quarterly report PDFs above to get started</div>
                <div style="font-size:0.85rem; margin-top:6px;">Drag & drop or click to browse · Min 2, Max 8 reports</div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
