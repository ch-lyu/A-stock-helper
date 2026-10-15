# 方法来源与能力映射

这不是只保存链接的索引：保留原始公开投研资料、A股适配底稿、公式/规则、执行程序和验收边界。完整版本/许可见source-catalog.json（整合包）或仓库docs/research/adoption.json；20个早期候选的核读范围另见仓库repositories.json。

## 已有Notion方法的迁移

| 已有方法 | 此包实际内容 | 可执行状态 |
|---|---|---|
| 美股thesis/comps/DCF、财报前瞻/更新、催化与晨报 | company-research.md、valuation-events.md；下方10套公开原始资料 | DCF可执行；公司/同行/事件需AI核公告 |
| quant-equity-review公式与技术证据分层 | quant-methods.md，明确窗口/ATR/通道/相对强弱约定 | analyze已有输出可执行；未实现公式不能补称已算 |
| personal-quant-risk组合方法 | 集中度与现金、协方差/贡献/VaR/ES公式和数据契约 | portfolio集中度及risk当前权重风险代理已实现；情景/优化仍待实现 |
| quant-strategy-audit固定假设、下一开盘、成本与留出 | backtest.md、quant-methods.md、实验模板 | ledger/proxy/validate可执行；高级统计与滚动前推METHOD_ONLY |
| 缠论理论、规则卡、标记字典、首次确认/重绘和平台对照 | chanlun.md、技术模块与未验证边界 | 无内置引擎；不继承其他环境的验证结论 |
| 维护规范、保留失败、版本与回滚 | 版本/哈希manifest、records.py、研究记录模板 | 本地版本保存/迁移已设验收；云端目录另验 |

未取得已有本地美股技能的源码：Notion提供描述与公式，无法据此声称直接复制脚本。当前代码是独立实现，尚未实现项明确列出。私人偏好、真实持仓、私有页面原文不进入公开包；妈妈档案重新确认。

## 随包保存的公开原始投研资料

来自[anthropics/financial-services](https://github.com/anthropics/financial-services/tree/574ed3624aebd0418c7e96cd101262f30210ab26)，Apache-2.0，原文及LICENSE/NOTICE保留。只按问题读，不作为额外自动执行技能，不继承其美国制度、工具权限、默认评级或盈利承诺。

| 资料 | 原始文件 | A股适配 |
|---|---|---|
| 逻辑跟踪 | [thesis-tracker](../../../vendor/financial-services/thesis-tracker/SKILL.md) | 可证伪卡与披露日 |
| 同行估值 | [comps-analysis](../../../vendor/financial-services/comps-analysis/SKILL.md) | 归母/EV范围、LTM/预测、周期差异 |
| DCF | [dcf-model](../../../vendor/financial-services/dcf-model/SKILL.md) | CNY情景、净债务/稀释、行业适用性 |
| 财报解读 | [earnings-analysis](../../../vendor/financial-services/earnings-analysis/SKILL.md) | 扣非、累计转单季、现金与治理 |
| 财报前瞻 | [earnings-preview](../../../vendor/financial-services/earnings-preview/SKILL.md) | 预告/快报与可核预期 |
| 催化日历 | [catalyst-calendar](../../../vendor/financial-services/catalyst-calendar/SKILL.md) | 政策传导、生效日、确定性 |
| 晨报 | [morning-note](../../../vendor/financial-services/morning-note/SKILL.md) | 中文重要变化与待核 |
| 行业总览 | [sector-overview](../../../vendor/financial-services/sector-overview/SKILL.md) | 产业链/周期/竞争 |
| 模型更新 | [model-update](../../../vendor/financial-services/model-update/SKILL.md) | 更新差异与时间边界 |
| 工作表审计 | [audit-xls](../../../vendor/financial-services/audit-xls/SKILL.md) | 口径、公式、单位与交叉检查 |

## 量化与缠论扩展

QuantSkills的[方向因子](https://github.com/quantskills/skill-quant-factor-directional-alpha)、[过拟合](https://github.com/quantskills/skill-backtest-overfit)、[滚动验证](https://github.com/quantskills/skill-walk-forward-validator)、[实验登记](https://github.com/quantskills/skill-quant-research-experiment-registry)、[成本校准](https://github.com/quantskills/skill-transaction-cost-calibration)：此次核README/版本/许可，未完整审计或运行源码。GPL-3.0实现不复制进本MIT代码；采纳实验透明、标签隔离、成本数据契约与预测/交易分离的独立流程。自报pass不证明此包通过，不自动安装PandaData或使用其凭据。

以上为v0.2核读范围。v0.3按professional-routing.md新增34个独立原始资料归档，保留各自许可/源代码；不将GPL/AGPL项目并入原创MIT实现。原始实验登记模块因已知问题BLOCKED，不能执行。已有RedSkill财报排雷、估值治理、选股进化、私募尽调与缠论方法另经核对适配；原包保留在私有扩展备份，公开核心不冒充迁移了其完整运行时。

[book2skill](https://github.com/shenqistart/book2skill)与[chanlun-engine-skill](https://github.com/adsorgcn/chanlun-engine-skill)为MIT候选；理论与引擎的规则/验收分离，未内置计算器。CZSC、chan.py、Qlib、RQAlpha、Jansen第二版资料继续作为研究候选，不能写成已运行。数据已实现与候选详见运行说明。
