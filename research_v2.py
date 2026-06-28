#!/usr/bin/env python3
"""
Stock Research Engine v2 - Futu + Finviz Dual Source
Combines Futu news data with Finviz financial metrics.
Outputs structured analysis in TSEM-style five-part framework.

Usage:
    python research_v2.py <TICKER> [--source futu|finviz|both] [--lang zh|en]
"""

import argparse, json, re, sys
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

FINVIZ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
FUTU_NEWS_API = "https://ai-news-search.futunn.com"
FUTU_UA = "stock-research-v2/1.0"
LANG_MAP = {"zh": "zh-CN", "en": "en"}


@dataclass
class QuoteData:
    ticker: str = ""
    company_name: str = ""
    price: float = 0.0
    prev_close: float = 0.0
    change_pct: float = 0.0
    volume: float = 0.0
    avg_volume: float = 0.0
    market_cap: float = 0.0
    pe: float = 0.0
    forward_pe: float = 0.0
    eps: float = 0.0
    revenue_ttm: float = 0.0
    gross_margin: float = 0.0
    oper_margin: float = 0.0
    profit_margin: float = 0.0
    roe: float = 0.0
    roa: float = 0.0
    roic: float = 0.0
    dividend_yield: float = 0.0
    w52_high: float = 0.0
    w52_low: float = 0.0
    beta: float = 0.0
    target_price: float = 0.0
    recommendation: float = 0.0
    industry: str = ""
    sector: str = ""
    country: str = ""
    short_float: float = 0.0
    inst_own: float = 0.0
    debt_equity: float = 0.0
    current_ratio: float = 0.0
    pb: float = 0.0
    ps: float = 0.0
    ev_ebitda: float = 0.0
    peg_ratio: float = 0.0
    rsi_14: float = 0.0
    sma20_pct: float = 0.0
    sma50_pct: float = 0.0
    sma200_pct: float = 0.0
    perf_ytd: float = 0.0
    perf_1y: float = 0.0
    sales_qq: float = 0.0
    sales_yy: float = 0.0
    eps_qq: float = 0.0
    eps_yy: float = 0.0
    eps_surprise: float = 0.0
    sales_surprise: float = 0.0
    insiders: float = 0.0
    inst_trans: float = 0.0
    short_ratio: float = 0.0
    employees: int = 0
    ipo_date: str = ""
    index: str = ""
    rel_volume: float = 0.0
    enterprise_value: float = 0.0
    book_value: float = 0.0
    cash_per_share: float = 0.0
    price_to_free_cf: float = 0.0
    quick_ratio: float = 0.0
    lt_debt_equity: float = 0.0
    dividend_ttm: float = 0.0
    payout_ratio: float = 0.0
    eps_next_y: float = 0.0
    eps_this_y: float = 0.0
    eps_next_5y: float = 0.0
    volatility_week: float = 0.0
    volatility_month: float = 0.0
    atr_14: float = 0.0
    perf_week: float = 0.0
    perf_month: float = 0.0
    perf_quarter: float = 0.0
    perf_half_y: float = 0.0
    perf_year: float = 0.0
    perf_3y: float = 0.0
    perf_5y: float = 0.0
    shares_outstanding: float = 0.0
    shares_float: float = 0.0


@dataclass
class NewsItem:
    title: str = ""
    publish_time: str = ""
    url: str = ""


@dataclass
class ResearchResult:
    ticker: str = ""
    fetched_at: str = ""
    quote: QuoteData = field(default_factory=QuoteData)
    news: List[NewsItem] = field(default_factory=list)
    news_summary: str = ""
    data_sources: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "ticker": self.ticker,
            "fetched_at": self.fetched_at,
            "data_sources": self.data_sources,
            "errors": self.errors,
            "quote": {k: v for k, v in asdict(self.quote).items() if v not in (0.0, 0, "")},
            "news": [asdict(n) for n in self.news],
            "news_summary": self.news_summary,
        }


def _num(v):
    if not v or v == "N/A":
        return 0.0
    v = v.replace(",", "").strip()
    if "%" in v:
        try:
            return float(v.replace("%", ""))
        except ValueError:
            return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0


def _num_pct(v):
    return _num(v)


def _billion(v):
    if not v or v == "N/A":
        return 0.0
    v = v.replace(",", "").strip()
    m = re.match(r"([\d.]+)([BMK]?)", v, re.IGNORECASE)
    if m:
        n = float(m.group(1))
        s = m.group(2).upper()
        return n * {"B": 1, "M": 1e-3, "K": 1e-6}.get(s, 1e-9)
    return 0.0


def _shares(v):
    if not v or v == "N/A":
        return 0.0
    v = v.replace(",", "").strip()
    m = re.match(r"([\d.]+)([BMK]?)", v, re.IGNORECASE)
    if m:
        n = float(m.group(1))
        s = m.group(2).upper()
        return n * {"B": 1e9, "M": 1e6, "K": 1e3}.get(s, 1)
    return 0.0


def _int_val(v):
    if not v or v == "N/A":
        return 0
    try:
        return int(float(v.replace(",", "").strip()))
    except ValueError:
        return 0


def fetch_finviz(ticker):
    url = "https://finviz.com/quote.ashx?t=" + ticker.upper()
    try:
        r = requests.get(url, headers=FINVIZ_HEADERS, timeout=15)
        r.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    q = QuoteData(ticker=ticker.upper())
    h2 = soup.find("h2")
    if h2:
        q.company_name = h2.get_text(strip=True)

    # NEW: Parse the quote table (alternating label/value cells)
    tables = soup.find_all("table")
    for t in tables:
        rows = t.find_all("tr")
        if len(rows) < 5:
            continue
        # Check if this table has quote data
        sample = " ".join(
            c.get_text(strip=True) for row in rows[:3] for c in row.find_all(["td", "th"])
        )
        if "P/E" not in sample and "Market Cap" not in sample:
            continue
        # Parse all rows as label/value pairs
        for row in rows:
            cells = row.find_all(["td", "th"])
            for j in range(0, len(cells) - 1, 2):
                label = cells[j].get_text(strip=True)
                value = cells[j + 1].get_text(strip=True)
                if not label or not value:
                    continue
                label = label.strip()
                value = value.strip()
                # Skip non-metric labels
                if label in ("Peers:", "Held by:", "Scroll to Statements", "Date", "Action", "Analyst", "Rating Change", "Price Target Change"):
                    continue
                if label == "Price":
                    q.price = _num(value)
                elif label == "Prev Close":
                    q.prev_close = _num(value)
                elif label == "Change":
                    q.change_pct = _num_pct(value)
                elif label == "Volume":
                    q.volume = _num(value)
                elif label == "Avg Volume":
                    q.avg_volume = _num(value)
                elif label == "Market Cap":
                    q.market_cap = _billion(value)
                elif label == "Enterprise Value":
                    q.enterprise_value = _billion(value)
                elif label == "Beta":
                    q.beta = _num(value)
                elif label == "P/E":
                    q.pe = _num(value)
                elif label == "Forward P/E":
                    q.forward_pe = _num(value)
                elif label == "EPS (ttm)":
                    q.eps = _num(value)
                elif label == "Dividend TTM":
                    q.dividend_ttm = value
                    m = re.search(r"\((\d+\.?\d*)%?\)", value)
                    if m:
                        q.dividend_yield = float(m.group(1))
                elif label == "Dividend Yield":
                    q.dividend_yield = _num_pct(value)
                elif label == "Dividend Est.":
                    m = re.search(r"\((\d+\.?\d*)%?\)", value)
                    if m:
                        q.dividend_yield = float(m.group(1))
                    q.payout_ratio = _num(value.split()[0] if value.split() else "0")
                elif label == "Book/sh":
                    q.book_value = _num(value)
                elif label == "Cash/sh":
                    q.cash_per_share = _num(value)
                elif label == "P/B":
                    q.pb = _num(value)
                elif label == "P/S":
                    q.ps = _num(value)
                elif label == "P/FCF":
                    q.price_to_free_cf = _num(value)
                elif label == "EV/EBITDA":
                    q.ev_ebitda = _num(value)
                elif label == "Income":
                    q.revenue_ttm = _billion(value)
                elif label == "Gross Margin":
                    q.gross_margin = _num_pct(value)
                elif label == "Oper. Margin":
                    q.oper_margin = _num_pct(value)
                elif label == "Profit Margin":
                    q.profit_margin = _num_pct(value)
                elif label == "ROE":
                    q.roe = _num_pct(value)
                elif label == "ROA":
                    q.roa = _num_pct(value)
                elif label == "ROIC":
                    q.roic = _num_pct(value)
                elif label == "Sales Q/Q":
                    q.sales_qq = _num_pct(value)
                elif label == "Sales Y/Y TTM":
                    q.sales_yy = _num_pct(value)
                elif label == "EPS Q/Q":
                    q.eps_qq = _num_pct(value)
                elif label == "EPS Y/Y TTM":
                    q.eps_yy = _num_pct(value)
                elif label == "EPS/Sales Surpr.":
                    parts = value.split()
                    if parts:
                        q.eps_surprise = _num_pct(parts[0])
                    if len(parts) > 1:
                        q.sales_surprise = _num_pct(parts[1])
                elif label == "Shs Outstand":
                    q.shares_outstanding = _shares(value)
                elif label == "Shs Float":
                    q.shares_float = _shares(value)
                elif label == "Insider Own":
                    q.insiders = _num_pct(value)
                elif label == "Insider Trans":
                    q.insider_trans_pct = _num_pct(value)
                elif label == "Inst Own":
                    q.inst_own = _num_pct(value)
                elif label == "Inst Trans":
                    q.inst_trans = _num_pct(value)
                elif label == "Short Float":
                    q.short_float = _num_pct(value)
                elif label == "Short Ratio":
                    q.short_ratio = _num(value)
                elif label == "ATR (14)":
                    q.atr_14 = _num(value)
                elif label == "RSI (14)":
                    q.rsi_14 = _num(value)
                elif label == "Volatility":
                    parts = value.split()
                    if len(parts) >= 2:
                        q.volatility_week = _num_pct(parts[0])
                        q.volatility_month = _num_pct(parts[1])
                elif label == "SMA20":
                    q.sma20_pct = _num_pct(value)
                elif label == "SMA50":
                    q.sma50_pct = _num_pct(value)
                elif label == "SMA200":
                    q.sma200_pct = _num_pct(value)
                elif label == "Perf Week":
                    q.perf_week = _num_pct(value)
                elif label == "Perf Month":
                    q.perf_month = _num_pct(value)
                elif label == "Perf Quarter":
                    q.perf_quarter = _num_pct(value)
                elif label == "Perf Half Y":
                    q.perf_half_y = _num_pct(value)
                elif label == "Perf Year":
                    q.perf_year = _num_pct(value)
                elif label == "Perf YTD":
                    q.perf_ytd = _num_pct(value)
                elif label == "Perf 3Y":
                    q.perf_3y = _num_pct(value)
                elif label == "Perf 5Y":
                    q.perf_5y = _num_pct(value)
                elif label == "Perf 10Y":
                    q.perf_10y = _num_pct(value)
                elif label == "52W High":
                    # value is like "317.40-10.59%" — price then dash then pct
                    try:
                        clean = re.sub(r"[^\d.]", ".", value)
                        nums = [n for n in clean.split(".") if n]
                        q.w52_high = float(nums[0]) if nums else 0.0
                    except Exception:
                        pass
                elif label == "52W Low":
                    try:
                        clean = re.sub(r"[^\d.]", ".", value)
                        nums = [n for n in clean.split(".") if n]
                        q.w52_low = float(nums[0]) if nums else 0.0
                    except Exception:
                        pass
                elif label == "Current Ratio":
                    q.current_ratio = _num(value)
                elif label == "Quick Ratio":
                    q.quick_ratio = _num(value)
                elif label == "Debt/Eq":
                    q.debt_equity = _num(value)
                elif label == "LT Debt/Eq":
                    q.lt_debt_equity = _num(value)
                elif label == "Target Price":
                    q.target_price = _num(value)
                elif label == "Recom":
                    q.recommendation = _num(value)
                elif label == "Employees":
                    q.employees = _int_val(value)
                elif label == "Industry":
                    q.industry = value
                elif label == "Sector":
                    q.sector = value
                elif label == "Country":
                    q.country = value
                elif label == "Index":
                    q.index = value
                elif label == "Rel Volume":
                    q.rel_volume = _num(value)
                elif label == "EPS next Y":
                    q.eps_next_y = _num(value)
                elif label == "EPS this Y":
                    q.eps_this_y = _num_pct(value)
                elif label == "EPS next 5Y":
                    q.eps_next_5y = _num_pct(value)
                elif label == "Payout":
                    q.payout_ratio = _num_pct(value)
                elif label == "Dividend Ex-Date":
                    pass  # skip date
                elif label == "Earnings":
                    pass  # skip date
                elif label == "IPO":
                    q.ipo_date = value
                elif label == "PEG":
                    q.peg_ratio = _num(value)
                elif label == "Sales past 3/5Y":
                    pass  # skip
                elif label == "Dividend Gr. 3/5Y":
                    pass  # skip
                elif label == "EPS past 3/5Y":
                    pass  # skip
                elif label == "Option/Short":
                    pass  # skip
                elif label == "Trades":
                    pass  # skip
                elif label == "EV/Sales":
                    pass  # already mapped above
                else:
                    pass  # unhandled label
        break  # found the quote table

    return q


def fetch_futu_news(ticker, lang="en", size=10):
    lang_code = LANG_MAP.get(lang, "en")
    url = FUTU_NEWS_API + "/news_search"
    try:
        r = requests.get(
            url,
            params={"keyword": ticker, "size": size, "news_type": 1, "sort_type": 2, "lang": lang_code},
            headers={"User-Agent": FUTU_UA},
            timeout=15,
        )
        r.raise_for_status()
        d = r.json()
        if d.get("code") != 0:
            return []
        items = []
        for item in d.get("data", [])[:size]:
            ts = item.get("publish_time", "")
            try:
                t = int(ts)
                if t > 1e12:
                    t = t // 1000
                dt = datetime.fromtimestamp(t, tz=timezone.utc).astimezone(timezone(timedelta(hours=8)))
                ts = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
            title = re.sub(r"<[^>]+>", "", item.get("title", ""))
            items.append(NewsItem(title=title, publish_time=ts, url=item.get("url", "")))
        return items
    except Exception:
        return []


def generate_report(result, lang="en"):
    q = result.quote
    L = []
    if lang == "zh":
        L.append("# " + q.ticker + " 深度研究报告")
        L.append("数据来源: " + str(result.data_sources) + " | 时间: " + result.fetched_at)
        L.append("")
        L.append("## 一、基本面概览")
        if q.company_name:
            L.append("**公司**: " + q.company_name)
        L.append("**股价**: $" + "{:.2f}".format(q.price))
        L.append("**市值**: $" + "{:.2f}".format(q.market_cap) + "B")
        L.append("**P/E**: " + "{:.1f}".format(q.pe) + " | **Forward P/E**: " + "{:.1f}".format(q.forward_pe))
        L.append("**EPS(TTM)**: $" + "{:.2f}".format(q.eps) + " | **股息率**: " + "{:.2f}".format(q.dividend_yield) + "%")
        L.append("**营收(TTM)**: $" + "{:.2f}".format(q.revenue_ttm) + "B | **毛利率**: " + "{:.1f}".format(q.gross_margin) + "%")
        L.append("**净利率**: " + "{:.1f}".format(q.profit_margin) + "% | **ROE**: " + "{:.1f}".format(q.roe) + "%")
        L.append("**52周范围**: $" + "{:.2f}".format(q.w52_low) + " - $" + "{:.2f}".format(q.w52_high))
        L.append("")
        L.append("## 二、近期新闻")
        if result.news:
            for i, n in enumerate(result.news[:5], 1):
                L.append(str(i) + ". " + n.title + " (" + n.publish_time + ")")
                if n.url:
                    L.append("   " + n.url)
        else:
            L.append("暂无最新新闻数据")
        L.append("")
        L.append("## 三、核心指标")
        L.append("- **PB**: " + "{:.1f}".format(q.pb) + " | **PS**: " + "{:.2f}".format(q.ps))
        L.append("- **Beta**: " + "{:.2f}".format(q.beta) + " | **RSI(14)**: " + "{:.1f}".format(q.rsi_14))
        L.append("- **机构持股**: " + "{:.1f}".format(q.inst_own) + "% | **做空比例**: " + "{:.1f}".format(q.short_float) + "%")
        L.append("- **债务/权益**: " + "{:.2f}".format(q.debt_equity) + " | **流动比率**: " + "{:.2f}".format(q.current_ratio))
        L.append("")
        L.append("*本分析仅供参考，不构成投资建议。*")
    else:
        L.append("# " + q.ticker + " Deep Research Report")
        L.append("Data Sources: " + str(result.data_sources) + " | Fetched: " + result.fetched_at)
        L.append("")
        L.append("## 1. Fundamentals")
        if q.company_name:
            L.append("**Company**: " + q.company_name)
        L.append("**Price**: $" + "{:.2f}".format(q.price))
        L.append("**Market Cap**: $" + "{:.2f}".format(q.market_cap) + "B")
        L.append("**P/E**: " + "{:.1f}".format(q.pe) + " | **Forward P/E**: " + "{:.1f}".format(q.forward_pe))
        L.append("**EPS (TTM)**: $" + "{:.2f}".format(q.eps) + " | **Div Yield**: " + "{:.2f}".format(q.dividend_yield) + "%")
        L.append("**Revenue (TTM)**: $" + "{:.2f}".format(q.revenue_ttm) + "B | **Gross Margin**: " + "{:.1f}".format(q.gross_margin) + "%")
        L.append("**Net Margin**: " + "{:.1f}".format(q.profit_margin) + "% | **ROE**: " + "{:.1f}".format(q.roe) + "%")
        L.append("**52W Range**: $" + "{:.2f}".format(q.w52_low) + " - $" + "{:.2f}".format(q.w52_high))
        L.append("")
        L.append("## 2. Recent News")
        if result.news:
            for i, n in enumerate(result.news[:5], 1):
                L.append(str(i) + ". " + n.title + " (" + n.publish_time + ")")
                if n.url:
                    L.append("   " + n.url)
        else:
            L.append("No recent news data available")
        L.append("")
        L.append("## 3. Key Metrics")
        L.append("- **PB**: " + "{:.1f}".format(q.pb) + " | **PS**: " + "{:.2f}".format(q.ps))
        L.append("- **Beta**: " + "{:.2f}".format(q.beta) + " | **RSI(14)**: " + "{:.1f}".format(q.rsi_14))
        L.append("- **Inst Own**: " + "{:.1f}".format(q.inst_own) + "% | **Short Float**: " + "{:.1f}".format(q.short_float) + "%")
        L.append("- **D/E**: " + "{:.2f}".format(q.debt_equity) + " | **Curr Ratio**: " + "{:.2f}".format(q.current_ratio))
        L.append("")
        L.append("*This analysis is for informational purposes only and does not constitute investment advice.*")
    return "\n".join(L)


def main():
    parser = argparse.ArgumentParser(description="Stock Research Engine v2")
    parser.add_argument("ticker", help="Stock ticker (e.g., AAPL, TSLA, NVDA)")
    parser.add_argument("--source", "-s", choices=["futu", "finviz", "both"], default="both")
    parser.add_argument("--lang", "-l", choices=["zh", "en"], default="en")
    parser.add_argument("--output", "-o", help="Save JSON to file")
    parser.add_argument("--report", "-r", action="store_true", help="Generate text report")
    parser.add_argument("--news-size", "-n", type=int, default=10, help="Number of news items")
    args = parser.parse_args()
    result = ResearchResult(
        ticker=args.ticker,
        fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    if args.source in ("finviz", "both"):
        try:
            q = fetch_finviz(args.ticker)
            if q and q.price > 0:
                result.quote = q
                result.data_sources["finviz"] = True
                print("[Finviz] OK for " + args.ticker, file=sys.stderr)
            else:
                result.data_sources["finviz"] = False
                result.errors.append("Finviz: no data or price=0")
        except Exception as e:
            result.data_sources["finviz"] = False
            result.errors.append("Finviz error: " + str(e))
    if args.source in ("futu", "both"):
        try:
            news = fetch_futu_news(args.ticker, lang=args.lang, size=args.news_size)
            result.news = news
            result.data_sources["futu_news"] = len(news) > 0
            print("[Futu] Got " + str(len(news)) + " news for " + args.ticker, file=sys.stderr)
        except Exception as e:
            result.data_sources["futu_news"] = False
            result.errors.append("Futu news error: " + str(e))
    if args.report:
        print(generate_report(result, lang=args.lang))
    else:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        print("Saved JSON to " + args.output, file=sys.stderr)


if __name__ == "__main__":
    main()
