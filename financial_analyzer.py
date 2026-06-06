import pdfplumber
from google import genai
import json
import yfinance as yf
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image

class FinancialAnalyzer:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API Key is required")
        self.client = genai.Client(api_key=api_key)
        
        self.used_ocr = False

    def extract_text_from_pdf(self, pdf_file):
        self.used_ocr = False
        """Extracts text from a PDF file."""
        text = ""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            return None, f"Error extracting text: {str(e)}"
        if not text.strip():
            return None, "Could not extract any text from the PDF. It might be a scanned image."
        if not text.strip():
            try:
                self.used_ocr = True

                pdf_file.seek(0)

                text = self.extract_text_with_ocr(pdf_file)
                
                if text.strip():
                    return text, None
            except Exception as e:
                print(f"OCR Error: {e}")
                pass
            return None, "Unable to extract text from PDF even with OCR."

        
        return text, None

    def extract_text_with_ocr(self, pdf_file):
        images = convert_from_bytes(pdf_file.read())
        text = ""
        
        for image in images:
            text += pytesseract.image_to_string(image)
            
        pdf_file.seek(0)
        
        return text
    
    def analyze_financials(self, text):
        """Sends the text to Gemini to extract key financial metrics."""
        prompt = """You are an expert financial analyst. Your task is to carefully read through this financial statement and extract the key financial metrics for the MOST RECENT fiscal year.

IMPORTANT RULES:
1. Return ONLY raw JSON. No markdown, no code fences, no explanation text before or after.
2. ALL number values MUST be actual numbers (integers or floats), NOT strings and NOT null.
3. Convert all values to their full numeric form:
   - "394.3 billion" = 394300000000
   - "93,736 (in millions)" = 93736000000
   - If the table says "in millions", multiply every number by 1000000
   - If the table says "in thousands", multiply every number by 1000
4. Search the ENTIRE document for: Income Statements, Balance Sheets, Cash Flow Statements.
5. For EPS: find "Earnings per share" (basic or diluted).
6. For Free Cash Flow: "Cash from operations" minus "Capital expenditures".
7. For Growth Rate: compute (current_revenue - prior_revenue) / prior_revenue.
8. NEVER return null for numeric fields. If truly not found, use 0.
9. Extract the stock ticker symbol (e.g. AAPL for Apple, MSFT for Microsoft, RELIANCE.NS for Reliance Industries).

JSON format (use real numbers, these are just format examples):
{
  "Company Name": "Apple Inc.",
  "Ticker": "AAPL",
  "Fiscal Year": "2025",
  "Revenue": 394328000000,
  "Net Income": 93736000000,
  "EPS": 6.08,
  "Free Cash Flow": 108807000000,
  "Total Assets": 364980000000,
  "Total Liabilities": 308030000000,
  "Outstanding Shares": 15408095000,
  "Growth Rate": 0.05,
  "Currency": "USD",
  "Risk Factors": ["risk one", "risk two", "risk three"],
  "Notes": "Values extracted from consolidated statements"
}

DOCUMENT TEXT:
""" + text[:30000]

        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.5-pro",
        ]

        last_error = None
        for model_name in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                data = response.text.strip()
                # Strip markdown fences if present
                if data.startswith("```json"):
                    data = data[7:]
                elif data.startswith("```"):
                    data = data[3:]
                if data.endswith("```"):
                    data = data[:-3]
                parsed = json.loads(data.strip())
                # Validate we got actual numbers
                if parsed.get("Revenue") is not None and parsed.get("Revenue") != 0:
                    return parsed
                # If revenue is null/0, the model didn't extract well, but return anyway
                return parsed
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error from {model_name}: {str(e)[:100]}"
                print(f"{last_error}")
                continue
            except Exception as e:
                last_error = str(e)
                print(f"Model {model_name} failed: {e}")
                continue

        return {"error": f"All models failed. Last error: {last_error}"}

    def calculate_intrinsic_value(self, metrics):
        """Calculates intrinsic value using DCF and Graham Number."""
        if "error" in metrics:
            return metrics

        try:
            fcf = float(metrics.get("Free Cash Flow") or 0)
            eps = float(metrics.get("EPS") or 0)
            growth_rate = float(metrics.get("Growth Rate") or 0.05)
            shares = float(metrics.get("Outstanding Shares") or 1)
            assets = float(metrics.get("Total Assets") or 0)
            liabilities = float(metrics.get("Total Liabilities") or 0)

            # 1. Simplified DCF
            discount_rate = 0.10
            terminal_growth = 0.02
            years = 5

            future_fcf = []
            current_fcf = fcf
            for _ in range(years):
                current_fcf *= (1 + growth_rate)
                future_fcf.append(current_fcf)

            if future_fcf and future_fcf[-1] != 0:
                terminal_value = (future_fcf[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            else:
                terminal_value = 0

            dcf_value = sum(val / ((1 + discount_rate) ** (i + 1)) for i, val in enumerate(future_fcf))
            dcf_value += terminal_value / ((1 + discount_rate) ** years)
            intrinsic_dcf = dcf_value / shares if shares else 0

            # 2. Graham Number
            book_value = assets - liabilities
            bvps = book_value / shares if shares else 0

            if eps > 0 and bvps > 0:
                graham_number = (22.5 * eps * bvps) ** 0.5
            else:
                graham_number = 0

            return {
                "DCF Value": round(intrinsic_dcf, 2),
                "Graham Number": round(graham_number, 2),
                "Book Value Per Share": round(bvps, 2),
                "Assumptions": {
                    "Discount Rate": "10%",
                    "Growth Rate": f"{growth_rate:.1%}",
                    "Terminal Growth": "2%",
                    "Projection Years": "5"
                }
            }
        except Exception as e:
            return {"error": f"Calculation error: {str(e)}"}

    def get_current_price(self, ticker):
        """Fetches the current stock price using yfinance."""
        if not ticker:
            return None
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if hist.empty:
                return None
            return round(float(hist['Close'].iloc[-1]), 2)
        except Exception as e:
            print(f"Could not fetch price for {ticker}: {e}")
            return None

    def get_recent_news(self, ticker, max_items=3):
        """Fetches recent news articles for a ticker using yfinance."""
        if not ticker:
            return []
        try:
            import time
            stock = yf.Ticker(ticker)
            raw_news = stock.news or []
            articles = []
            for item in raw_news[:max_items]:
                content = item.get("content", {})
                title = content.get("title") or item.get("title", "No title")
                link = (content.get("canonicalUrl", {}) or {}).get("url") or \
                       (content.get("clickThroughUrl", {}) or {}).get("url") or \
                       item.get("link", "#")
                publisher = (content.get("provider", {}) or {}).get("displayName") or \
                            item.get("publisher", "Unknown")
                pub_time = content.get("pubDate") or ""
                if not pub_time:
                    raw_ts = item.get("providerPublishTime", 0)
                    if raw_ts:
                        pub_time = time.strftime("%b %d, %Y", time.gmtime(raw_ts))
                articles.append({
                    "title": title,
                    "link": link,
                    "publisher": publisher,
                    "published": pub_time,
                })
            return articles
        except Exception as e:
            print(f"Could not fetch news for {ticker}: {e}")
            return []

    def analyze_quarterly_comparison(self, pdf_files_with_labels):
        """Analyze multiple quarterly PDFs and compute growth trends + pros/cons.

        Args:
            pdf_files_with_labels: list of (pdf_file, label) tuples, e.g. [("file", "Q1 2025")]

        Returns:
            dict with keys: quarters, growth, pros_cons, company_name
        """
        quarters = []
        errors = []

        for pdf_file, label in pdf_files_with_labels:
            text, err = self.extract_text_from_pdf(pdf_file)
            if err:
                errors.append(f"{label}: {err}")
                continue
            metrics = self.analyze_financials(text)
            if "error" in metrics:
                errors.append(f"{label}: {metrics['error']}")
                continue
            metrics["Quarter Label"] = label
            quarters.append(metrics)

        if len(quarters) < 2:
            return {"error": f"Need at least 2 valid reports. Errors: {'; '.join(errors)}"}

        # Compute QoQ growth
        growth = []
        metric_keys = ["Revenue", "Net Income", "EPS", "Free Cash Flow"]
        for i in range(1, len(quarters)):
            prev = quarters[i - 1]
            curr = quarters[i]
            g = {"Quarter": curr.get("Quarter Label", f"Q{i+1}")}
            for key in metric_keys:
                prev_val = float(prev.get(key) or 0)
                curr_val = float(curr.get(key) or 0)
                if prev_val != 0:
                    g[key] = round(((curr_val - prev_val) / abs(prev_val)) * 100, 2)
                else:
                    g[key] = 0.0
            growth.append(g)

        # Generate pros/cons via Gemini
        pros_cons = self.generate_pros_cons(quarters)

        company_name = quarters[0].get("Company Name", "Unknown Company")

        return {
            "quarters": quarters,
            "growth": growth,
            "pros_cons": pros_cons,
            "company_name": company_name,
            "errors": errors
        }

    def generate_pros_cons(self, quarters):
        """Use Gemini to generate pros, cons, and trajectory from quarterly data."""
        # Build a summary of all quarters for the prompt
        summary_lines = []
        for q in quarters:
            label = q.get("Quarter Label", "Unknown")
            summary_lines.append(
                f"{label}: Revenue={q.get('Revenue',0)}, "
                f"Net Income={q.get('Net Income',0)}, "
                f"EPS={q.get('EPS',0)}, "
                f"FCF={q.get('Free Cash Flow',0)}, "
                f"Total Assets={q.get('Total Assets',0)}, "
                f"Total Liabilities={q.get('Total Liabilities',0)}"
            )
        quarter_data = "\n".join(summary_lines)

        prompt = f"""You are a senior financial analyst. Below are the key financial metrics extracted from multiple quarterly reports of the same company, in chronological order.

QUARTERLY DATA:
{quarter_data}

Based on this data, provide:
1. PROS: 4-6 bullet points highlighting strengths, positive trends, and growth areas
2. CONS: 4-6 bullet points highlighting weaknesses, concerns, declining metrics, and risks
3. TRAJECTORY: A 2-3 sentence overall assessment of the company's direction

IMPORTANT: Return ONLY raw JSON. No markdown, no code fences.
JSON format:
{{
  "pros": ["point 1", "point 2", "point 3", "point 4"],
  "cons": ["point 1", "point 2", "point 3", "point 4"],
  "trajectory": "Overall assessment text here."
}}"""

        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.5-pro",
        ]

        for model_name in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                data = response.text.strip()
                if data.startswith("```json"):
                    data = data[7:]
                elif data.startswith("```"):
                    data = data[3:]
                if data.endswith("```"):
                    data = data[:-3]
                return json.loads(data.strip())
            except Exception as e:
                print(f"Pros/Cons model {model_name} failed: {e}")
                continue

        return {
            "pros": ["Could not generate analysis"],
            "cons": ["Could not generate analysis"],
            "trajectory": "AI analysis unavailable."
        }

    def fetch_stock_data(self, ticker):
        """Fetches live financial data for a ticker using yfinance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or info.get("trailingPE") is None and info.get("marketCap") is None:
                return None, "Could not find financial data for this ticker."

            # Pull financials
            revenue = info.get("totalRevenue", 0) or 0
            net_income = info.get("netIncomeToCommon", 0) or 0
            eps = info.get("trailingEps", 0) or 0
            total_assets = info.get("totalAssets", 0) or 0
            total_liabilities = info.get("totalDebt", 0) or 0
            shares = info.get("sharesOutstanding", 0) or 0
            fcf = info.get("freeCashflow", 0) or 0
            growth = info.get("revenueGrowth", 0.05) or 0.05
            currency = info.get("currency", "USD")
            name = info.get("longName") or info.get("shortName") or ticker
            sector = info.get("sector", "N/A")
            market_cap = info.get("marketCap", 0) or 0

            # Try to get total assets/liabilities from balance sheet if missing
            if total_assets == 0:
                try:
                    bs = stock.balance_sheet
                    if bs is not None and not bs.empty:
                        if "Total Assets" in bs.index:
                            total_assets = float(bs.loc["Total Assets"].iloc[0]) or 0
                        if "Total Liabilities Net Minority Interest" in bs.index:
                            total_liabilities = float(bs.loc["Total Liabilities Net Minority Interest"].iloc[0]) or 0
                except Exception:
                    pass

            metrics = {
                "Company Name": name,
                "Ticker": ticker.upper(),
                "Fiscal Year": "TTM",
                "Revenue": revenue,
                "Net Income": net_income,
                "EPS": round(eps, 2),
                "Free Cash Flow": fcf,
                "Total Assets": total_assets,
                "Total Liabilities": total_liabilities,
                "Outstanding Shares": shares,
                "Growth Rate": growth,
                "Currency": currency,
                "Sector": sector,
                "Market Cap": market_cap,
                "Risk Factors": [
                    f"Sector: {sector}",
                    f"Market Cap: ${market_cap/1e9:.1f}B" if market_cap > 0 else "Market Cap: N/A",
                    f"Revenue Growth: {growth:.1%}" if growth else "Growth data unavailable"
                ],
                "Notes": f"Data sourced from Yahoo Finance (trailing twelve months). Ticker: {ticker.upper()}"
            }
            return metrics, None
        except Exception as e:
            return None, f"Error fetching data for {ticker}: {str(e)}"


