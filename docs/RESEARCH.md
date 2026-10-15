# 资源审查与采用决策（2026-10-07）

v0.3于2026-10-15重新核对当前可访问Notion投资目录及新增方法：覆盖484条索引，核心新增34个原始资料归档。逐项覆盖与缺源/停用在主技能references/coverage.json；源许可/指纹在professional-catalog.json。475模块另存私有扩展，建库时的current-public-upstream不是今日最新保证。原Notion私人正文不公开；读取索引、保留源码、理解工作流和实测运行是不同验收层。

完整仓库元数据、核读commit和失败记录见 [repositories.json](research/repositories.json)。
本轮核读README和许可元数据，部分另核文档/代码；不是所有仓库完整代码审计。
这些项目是工具/框架，不是已盈利策略，星数、自报验证数量不用于验收。
本包代码与12个A股模块原创。v0.2保留10个Apache-2.0公开原始投研技能作为参考资料，附许可证及NOTICE，不冒充原创或已执行。详细方法与能力映射见主技能references/adoption-map.md，固定版本见research/adoption.json。

| 来源 | 本包用途与决策 |
|---|---|
| [anthropics/financial-services](https://github.com/anthropics/financial-services) | 新核固定commit的10套SKILL及财报附属参考；原文置vendor，A股会计/数据/制度独立适配；不包含上游示例xlsx、Excel工具或授权数据服务 |
| [ZICXR/A-Stock-Skills](https://github.com/ZICXR/A-Stock-Skills) | 数据缓存、观察名单与复盘结构参考；README现在10核心，旧29技能在archive-v1，不能照搜索摘要认定当前数量 |
| [lzwme/finance-quant-skills](https://github.com/lzwme/finance-quant-skills) | A股数据/量化技能索引；许可元数据缺失，链接参考不复制 |
| [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) | 中文研究与新闻界面参考；不采用其建议评分作为胜率，调度免费不等于数据/模型免费 |
| [hsliuping/TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) | 多源研究与中文交互参考；核心和应用层混合许可，未整体复制 |
| [akfamily/akshare](https://github.com/akfamily/akshare) | 实际适配日K/新闻；安装1.19.1，核过新闻函数源码和接口返回 |
| [waditu/tushare](https://github.com/waditu/tushare) | REST财报/日K/逐日限价适配；官方API文档核读，凭据缺失未进行付费接口实测 |
| [BaoStock官方](https://baostock.com/) | 历史日K/停牌/财务候选源，本版未实现适配；仓库zxygithub/baostock是第三方下载器，不称官方SDK |
| [microsoft/qlib](https://github.com/microsoft/qlib) | A股多因子/ML研究接入路径，核数据及exchange文档；未内置训练器，未跑它的模型 |
| [ricequant/rqalpha](https://github.com/ricequant/rqalpha) | 完整A股事件回测扩展候选；网站/仓库级资料核读，自动README请求失败记录保留，未安装 |
| [vnpy/vnpy](https://github.com/vnpy/vnpy) | 事件/网关/风控架构参考；本包没有交易网关 |
| [nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | 事件回放架构参考；A股产品和公司行动须额外适配，不直接套加密场景 |
| [quantskills/quantskills](https://github.com/quantskills/quantskills) | 因子、过拟合、walk-forward、成本和实验登记索引；原市场和自报pass不替代本项目验证 |
| [waditu/czsc](https://github.com/waditu/czsc) | 缠论候选，许可须核具体模块；未内置为已验证计算器 |
| [Vespa314/chan.py](https://github.com/Vespa314/chan.py) | 结构/增量回放参考；端点与首次确认分开，平台等价和盈利独立验收 |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | 多空论据/反方审查参考；不以Agent投票替代证据，不授权交易 |
| [Jansen配套源码](https://github.com/stefan-jansen/machine-learning-for-trading/tree/second-edition) | 时间切分、预测/交易质量、PIT与成本参考；当前main为第三版，用户旧书第二版须对应分支 |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | 跨市场数据聚合参考；接入器存在不代表所有源免费 |
| [Dexter](https://github.com/virattt/dexter) | 财务证据与研究问答流程参考；未复制许可不明代码 |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | 财报研究与报告分层参考，未部署框架 |

## 更进一步的研究

QuantSkills的因子参数、前视与自动筛选行为必须逐仓库核代码；本轮不声称逐因子验证。
Qlib历史股票池、财报历史修订和成本层补齐后，才适合全市场横截面因子研究。
现有美股知识中的方法论可复用，私人Notion持仓、账户与笔记原文未进入公开仓库。
已有缠论验证记录提示sure/端点可能变化，故保留候选模块而不承诺“准确复现TradeDesk”。
