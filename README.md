# Stock Research Skill

基于 TSEM 分析框架的股票研究工具，整合 **Finviz** 基本面数据 + **富途新闻 API** 实时资讯。

## 功能

- **Finviz 抓取**: 50+ 财务指标（P/E, Market Cap, EPS, Margins, ROE, Technicals 等）
- **富途新闻**: 实时新闻搜索，支持中英文
- **TSEM 分析框架**: 基本面 → 催化剂 → 优势 → 风险 → 估值
- **双语言输出**: 中文 / 英文报告

## 目录结构

```
├── research_v2.py          # 主研究引擎（Finviz + Futu）
├── SKILL.md                # 使用说明
├── futu-search/            # 富途搜索技能（无需 OpenD）
│   ├── futu-news-search/
│   ├── futu-stock-digest/
│   └── futu-comment-sentiment/
└── futu-anomaly/           # 富途异常检测技能（需要 OpenD）
    ├── futu-capital-anomaly/
    ├── futu-derivatives-anomaly/
    └── futu-technical-anomaly/
```

## 快速开始

```bash
# 中文报告 + 双数据源
python research_v2.py AAPL --source both --report --lang zh

# 英文报告
python research_v2.py NVDA --source both --report --lang en

# 仅 Finviz 基本面
python research_v2.py TSLA --source finviz

# 保存 JSON
python research_v2.py AAPL --output report.json
```

## 依赖

```bash
pip install requests beautifulsoup4
# futu-api 可选（需要 OpenD 客户端）
pip install futu-api
```

## 数据源

| 来源 | 类型 | 是否需要客户端 | 覆盖市场 |
|------|------|--------------|---------|
| Finviz | 基本面指标 | 否 | 美股 |
| 富途新闻 API | 实时新闻 | 否 | 美股/港股/A股 |
| 富途 OpenAPI | 实时行情/交易 | 需要 OpenD | 美股/港股/A股 |

## License

MIT
