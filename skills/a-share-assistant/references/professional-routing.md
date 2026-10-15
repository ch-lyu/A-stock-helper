# 专业参考路由与覆盖边界

使用当前根目录scripts/references.py；它只检索/解包，不执行源代码。先读本包professional-workflows.md；需要详细方法时读取对应原文和其引用资料，不能只读这里的摘要便声称掌握或运行原技能。

```text
python REFERENCE list --query factor
python REFERENCE read factor-evaluate --out /新工作目录/factor-evaluate
```

REFERENCE为本技能scripts/references.py，整合包为根scripts/references.py。返回INSTRUCTIONS.md和完整资源目录，先核依赖与输入。source-SKILL.md保留原始指令字节；阅读副本中的SKILL.md文件引用已由来源库改为INSTRUCTIONS.md，两份分别固定哈希。脚本/许可与归档保持原样，不将参考脚本自动加入当前工具或执行来源要求的交易/发信/付款。

| 场景 | 随包原始模块名称 |
|---|---|
| 公司尽调/双向逻辑/候选 | a-share-stock-dossier、build-thesis、stock-screener、ashare-pre-st-filter |
| 估值/配置 | valuation-model、asset-allocation |
| 因子/HPO/残差 | factor-evaluate、model-hpo-evidence-driven、residual-guided-factor-selection |
| 回测数据/成交 | backtest-assumption-check、backtesting-bias-avoidance、a-share-tradability-auditor、survivorship-universe-auditor、corporate-action-adjustment-auditor、walk-forward-validator、strategy-capacity-tca |
| 组合与归因 | quant-portfolio-risk、risk-return-metrics、pair-correlation、brinson-performance-attribution |
| 龙虎榜/事件/治理 | skill-b7-lhb-monitor、event-risk-alert、skill-a-share-market-risk-radar、guarantee-risk-scan、buyback-monitor、block-trade-radar |
| 交易行为复盘 | trade-journal |
| 缠论 | chanlun-engine-skill、chanlun-structure-parser、chanlun-zhongshu-mapper、chanlun-divergence-diagnosis、chanlun-buy-sell-points、chanlun-multi-level-scenario |
| 筹码研究 | stock-cyq-analyzer；模型估计，不是券商真实成本分布 |

以上34个原始资料包是REFERENCE_ONLY，保留代码不代表已接入它的API、项目运行时、市场数据或已验证盈利。缠论源引擎现在随参考包保留，但未集成为本包命令，未通过平台一致性或收益验证。

quant-research-experiment-registry因来源安装审计发现配置/冲突/样例/日志问题，明确BLOCKED，不解包不执行。本包records.py为独立记录工具，不能叫已修复上游项目。

## 覆盖清单怎么读

coverage.json逐项记录本轮实际可访问的13页484项投资目录：34项核心原始参考、439项完整扩展资料对应、3项非投资开发流程、7项缺源、1项停用；另列5个新增方法适配。

独立完整资料库保留当前已恢复的475个投资模块和5项新增原包，供开发者按需审核。未逐一执行/语义审计475模块，不叫475个可运行功能。扩展包不自动安装为手机技能，不自动授权账号或交易。开发/系统技能和整个Notion所有页面不在覆盖承诺内。

全工作区安装清单仍有8项缺原源码：review-agent、chanlun-evidence-review、chanlun-review、personal-quant-risk、quant-equity-review、quant-strategy-audit、stock_analyzer、write-memo。前者为开发流程，因此投资目录中计7项。已有公式/方法适配不等于取得其完整源码。

若用户问是否包含全部Notion：回答“已核本次投资目录和列出的新增方法，不保证全工作区；完整扩展资料已保留，缺源/停用/运行依赖见清单”。不得将目录覆盖率混为专业判断准确率、策略胜率或安装成功率。
