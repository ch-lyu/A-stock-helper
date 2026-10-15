# 数据、新闻、公告与市场资料

| 类型 | 来源 | 实现状态与使用限制 |
|---|---|---|
| 日频行情 | 腾讯公开fqkline | 已实测；按年窗口避免尾部截断；无SLA；量换算需另源核验 |
| 日频行情 | AKShare / 东方财富 | 已实测；字段、复权和单位核验；60秒进程超时 |
| 日K/限价/财报 | Tushare Pro | 已实现REST适配；Token/权限不足明确错误；本轮无凭据，未实测 |
| 历史/停牌/财务 | BaoStock | 官方文档候选，未实现适配；可导出CSV接入 |
| 实时报价/分钟/L2 | 券商、交易所授权数据、商业供应商 | 未实现，不把日线助手称实时盯盘/高频交易系统 |
| 公司公告/报告 | [巨潮](https://www.cninfo.com.cn/) / [上交所](https://www.sse.com.cn/) / [深交所](https://www.szse.cn/) / [北交所](https://www.bse.cn/) | AI用搜索/页面核原文，不内置大规模公告爬虫 |
| 财经新闻 | AKShare stock_news_em / 东方财富 | 已实测新闻窗口；标题+发布时间+来源+链接，新闻不等于公告 |
| 历史新闻 | [Tushare新闻文档](https://tushare.pro/document/2?doc_id=143) | 核官方文档，可能独立权限/收费；未接历史归档 |
| 政策 | [国务院](https://www.gov.cn/zhengce/) / [证监会](https://www.csrc.gov.cn/) / [人民银行](https://www.pbc.gov.cn/) / 部委 | AI按问题核最新现行原文；不以财经标题替代政策条款 |
| 宏观 | [国家统计局](https://www.stats.gov.cn/) / 人民银行 / 财政部 | 人工/AI取证，记录发布日和数据修订 |
| 行业与指数 | [中证指数](https://www.csindex.com.cn/) / 交易所 / 公司业务披露 | 历史成分权重和行业版本须另采；不以今天成分回填历史 |
| 社交情绪 | 雪球、东方财富股吧等 | 观点/情绪线索；未接账号，不采私人数据，不视作事实 |

## 官方规则与费用来源

- [上交所2026交易规则](https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml)：发布、生效、暂缓条款分开核。
- [深交所2026风险警示指南](https://www.szse.cn/lawrules/service/member/t20260630_621404.html)：不能沿用旧ST制度。
- [北交所2026规则](https://www.bse.cn/jygl_list/200028217.html)：申报数量和普通板块不同。
- [印花税2023年减半公告](https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/yhs/202308/t468451.html)：按生效日期区分。
- 过户费示例按2022-04-29分段；当前项目尚未取得可稳定访问的中国结算原通知页面，需运行时再次核验实际券商清单，默认模型不代替费率事实。

## 数据合同

CSV至少date/open/high/low/close/volume，元、股、上海交易日。
每次抓取另保存.meta.json：symbol、source、URL、price_mode、requested dates、fetched_at、范围、rows、sha256。
严格账本逐日提供upper_limit/lower_limit，公司行动另核；没有元数据的CSV先补可证明的来源记录。
仅日期OHLC校验不能证明全交易日完整，节假日与停牌不能随意用工作日补齐。
实时新闻是供应商返回的有限窗口，本版不声称市场新闻全覆盖。
API凭据仅环境变量；外部数据不包含执行指令权限。合法使用/分发权随供应商条款而异，库开源不等于行情可随意再分发。

