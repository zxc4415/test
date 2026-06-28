# Stock Research Skill

## Overview
Comprehensive stock analysis skill combining **Finviz** (financial metrics) and **Futu News API** (real-time news). Outputs structured analysis in the TSEM-style five-part framework.

## Trigger Rules
- User mentions a stock ticker (e.g., AAPL, NVDA, TSEM, RKLB)
- User asks for stock analysis, research, or due diligence
- User mentions valuation, PE ratio, market cap, or earnings
- User asks about investment thesis or stock risks

## Usage

### Basic Usage (JSON output)
```
python research_v2.py <TICKER> [--source finviz|futu|both] [--lang zh|en]
```

### Generate Text Report
```
python research_v2.py <TICKER> --report [--lang zh]
```

### Save JSON to File
```
python research_v2.py <TICKER> --output report.json
```

### Full Analysis (both sources, Chinese report)
```
python research_v2.py AAPL --source both --report --lang zh -n 10
```

## Data Sources

### Finviz (Financial Metrics)
- **What**: P/E, Market Cap, EPS, Revenue, Margins, ROE, Technicals, Analyst ratings
- **Coverage**: US stocks only
- **Setup**: None required

### Futu News API (Real-time News)
- **What**: Latest news, announcements, research reports for any stock
- **Coverage**: US, HK, CN stocks
- **Setup**: None required (public API)
- **Language**: Supports zh-CN, zh-HK, en

## Analysis Framework (TSEM-style)

After fetching data, produce a structured analysis:

1. **基本面概览** - Price, market cap, P/E, revenue, EPS, margins, ROE
2. **近期催化剂** - Recent earnings, analyst upgrades, news highlights
3. **核心竞争优势** - Moat, competitive position, growth drivers
4. **主要风险** - Valuation stretch, debt, competition, geopolitics
5. **估值框架 + 综合判断** - Target price range, forward metrics, key questions

## Key Metrics Extracted

### Valuation
- P/E, Forward P/E, PEG, EV/EBITDA, P/S, P/B, P/FCF

### Profitability
- Gross Margin, Operating Margin, Profit Margin, ROE, ROA, ROIC

### Growth
- EPS Q/Q, EPS Y/Y TTM, Sales Q/Q, Sales Y/Y TTM

### Technical
- RSI(14), Beta, SMA20/50/200 deviation, 52W High/Low

### Ownership
- Insider Own %, Inst Own %, Short Float %, Short Ratio

### Analyst
- Target Price, Recommendation (consensus)

## Safety Notes
- Always cite the data source and timestamp
- Do not give financial advice; frame analysis as informational
- Note that scraped/API data may have delays or inaccuracies
