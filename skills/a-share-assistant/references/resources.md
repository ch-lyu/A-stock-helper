# 来源导航

按问题选源，工具可用性须每次最小实测。研究元数据在仓库docs/research/repositories.json；安装后此页提供入口。

| 任务 | 来源 | 采用边界 |
|---|---|---|
| A股行情/新闻 | https://akshare.akfamily.xyz/data/stock/stock.html | Python库开源不保证底层源稳定/分发权限 |
| 结构化/PIT线索 | https://tushare.pro/document/2 | 公告日与报告期分开，接口权限单核 |
| 历史数据候选 | https://baostock.com/ | 本包未内置，核官方SDK，不把第三方下载器称官方 |
| 公告原文 | https://www.cninfo.com.cn/ | 结合交易所/公司IR，核发布/更正时间 |
| 现行规则 | https://www.sse.com.cn/ https://www.szse.cn/ https://www.bse.cn/ | 现行有效与暂缓实施分开 |
| 政策宏观 | https://www.gov.cn/ https://www.csrc.gov.cn/ https://www.pbc.gov.cn/ https://www.stats.gov.cn/ | 财经新闻只是检索线索 |
| 技能设计 | https://github.com/ZICXR/A-Stock-Skills | 当前README为10核心，不照旧搜索摘要计数 |
| 技能索引 | https://github.com/lzwme/finance-quant-skills | 许可不明先链接，不自动安装 |
| 财务方法 | https://github.com/anthropics/financial-services | 复用thesis/comps/DCF思路，市场数据重做 |
| 中文报告 | https://github.com/ZhuLinsen/daily_stock_analysis | 评分不是胜率，推送需授权 |
| 中文Agent研究 | https://github.com/hsliuping/TradingAgents-CN | 混合许可，不能整体复制 |
| 多因子/ML | https://github.com/microsoft/qlib | 需历史股票池/PIT/成本，样例不等于策略收益 |
| 因子/验证 | https://github.com/quantskills/quantskills | 抽查实际compute参数、样本和未来泄漏；自报pass不采信为盈利 |
| 回测扩展 | https://github.com/ricequant/rqalpha https://github.com/vnpy/vnpy | 产品/分红/退市/费用和授权另核 |
| 事件回放 | https://github.com/nautechsystems/nautilus_trader | 不能未经适配把加密规则套到A股 |
| 缠论候选 | https://github.com/Vespa314/chan.py https://github.com/waditu/czsc | 原文/实现/平台一致/历史信号/盈利分别验证 |
| 学习/评估 | https://github.com/stefan-jansen/machine-learning-for-trading/tree/second-edition | 书籍版本对应分支，不以示例证明超额收益 |

本包12个技能原创，只使用流程思路与公开API；第三方源码未直接整包分发。缺少授权不得复制出版书全文。

