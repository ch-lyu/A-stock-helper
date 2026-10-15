# 证据与报告规则

关键数字记录source_id、URL、报告/数据日期、披露时间、抓取时间、单位和口径。
来源等级：公司公告/交易所/巨潮/监管部委 → 可核供应商 → 财经媒体 → 研报观点 → 社交情绪。
转载不构成多源独立确认。事实、推断、假设、未核信息分开。缺失不能填零。
归母、扣非、经营现金流不混用；累计/单季/TTM/预测分开；万元/亿元/股/万股/手标清。
报告期不等于可获得时间；日期级公告按更保守的下一日处理。
只有最新修订值时标非完整PIT；公告日过滤不能恢复被替换的历史数值。
新闻回测还需证明当时档案存在；现代LLM可能记住未来，不把历史叙述直接当信号。

市场规则按证券、板块、特殊状态、日期维护，不用统一10%/100股覆盖全市场。
上交所2026规则：<https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml>
深交所风险警示2026指南：<https://www.szse.cn/lawrules/service/member/t20260630_621404.html>
北交所2026规则：<https://www.bse.cn/jygl_list/200028217.html>
发布、生效、暂缓条款分开；回测优先逐日upper_limit/lower_limit，不用今日ST回填历史。

状态：VERIFIED_FACT / CALCULATED / ASSUMPTION / INFERENCE / UNVERIFIED。
报告显示缺失事实及其影响，不用评分掩盖证据缺口。

