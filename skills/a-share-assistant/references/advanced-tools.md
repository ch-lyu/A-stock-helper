# 新增确定工具的输入和限制

## 当前权重风险代理

先用fetch保存各持仓qfq或hfq行情及元数据，holdings.csv按portfolio已有规范。series.json中的CSV路径相对清单所在目录：

```json
{"series":{"600519":"600519.csv","600036":"600036.csv"},"window":252,"confidence":0.95}
```

```text
python RUNNER risk holdings.csv series.json --out risk.json
```

身份/来源/哈希须过审。先按各证券原始相邻两端日期计算收益，再交集相同起止区间；不是先交集价格再桥接缺口。至少60共同期，截止持仓快照；更晚行情排除并计数。现金日收益假设零，当前权重每天再平衡代理，不是实际账户盈亏。

输出相关矩阵、年化协方差/波动、年化风险贡献、历史1日VaR/ES与CNY金额。协方差样本自由度n−1、252年化；风险贡献可负、总和为组合波动；零波动时贡献/相关未定义项null。损失为负收益、nearest-rank分位数、ES为不小于该分位的样本均值；尾部并列全部纳入并列出样本数。VaR可为负，不截零，不代表最大损失或未来概率保障。无停牌盘口/独立总回报审计，报告限制必须保留。

## 估值数值复核

valuation-review输入包含model（原bear/base/bull模型）、probabilities（三个概率和1）、wacc_grid、growth_grid、可选target_price。三情景股本/净债务桥须一致，不一致先显式建模，不能无声混合。

```text
python RUNNER valuation-review review.json --out valuation-review.json
```

输出概率加权、基础情景敏感性、固定其他假设下全部FCFF统一倍数反向结果。无效WACC/g网格单元null并标错，不伪造值。数值成功仍DRAFT_REVIEW，不能冒充有公告证据或完整经营模型的治理PASS。

## 年度财报线索

financial-audit输入：symbol、as_of、currency=CNY、unit=CNY、industry=ordinary_nonfinancial、periods列表。每个年度：period为12-31、disclosed_at为实际披露日、source_url、comparable=true，以及有证据的金额字段：revenue、receivables、inventory、goodwill、equity、cash、restricted_cash、net_profit、ocf、nonrecurring_profit。缺失用null，别填零；audit_opinion为unmodified/qualified/adverse/disclaimer/unknown。

```text
python RUNNER financial-audit annuals.json --out financial-flags.json
```

只筛6类线索。comparable=true是输入者核对声明，不是程序自己验证；来源URL存在不代表已访问。拒绝未来披露、重复年度、非自然年或行业不适配。不能把启发式触发当造假判断，也不以未触发宣称安全。完整排雷仍需专业工作底稿、会计/经营/现金互证和反方复核。
