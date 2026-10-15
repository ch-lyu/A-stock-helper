# 运行说明与数据能力

本包有12个原创技能和一个共享Python运行器；安装器把runtime复制到主技能中。
专业技能的RUNNER路径为 `../a-share-assistant/scripts/astock.py`。
源码中可运行 `python scripts/astock.py`，核心无模型/API费用，无第三方依赖。
程序提供证据、确定计算和回测，AI须按技能解释并核公告。

| 命令 | 已实现 | 前提/限制 |
|---|---|---|
| doctor | Python/可选依赖检查 | Python3.10+；不证明AI技能发现 |
| fetch | 腾讯/AKShare/Tushare日K，来源/哈希/量单位 | 网络；可选包或凭据/权限 |
| audit / compare | CSV/覆盖/哈希/重合OHLC核验 | 非全交易日历核验；成交量独立校验未实现 |
| analyze | 均线/收益/波动/回撤与中文行情报告 | 不自动完整财报研究 |
| news | 东方财富新闻窗口，日期/原文链接 | AKShare；不是公告、不是全网归档 |
| fundamentals | 四张Tushare财报表，公告日筛选 | Token/权限；不保证修订版本历史 |
| valuation | 三情景FCFF/DCF | 用户核实输入，不适合所有行业 |
| screen | 同日观察名单60日动量排序 | 不等于全市场多因子筛选 |
| portfolio | 同日CNY快照集中度 | 用户CSV，不查账户/不算相关性VaR |
| backtest | 日频原始价格账本/复权收益代理 | 见backtest.md，无自动交易 |
| validate | 时间三段选择与成本压力 | 复权收益代理，固定三候选 |

可选包：在仓库venv运行 `python -m pip install -e '.[data]'`。
Tushare只从环境变量读取Token，不输出Token；部分接口需单独权限，不保证免费。
AKShare调用有60秒进程级超时。失败请换源/官方网页核查，不上传密钥到聊天或git。
公开腾讯接口无SLA，非官方交易所feed；当前日K默认剔除，最后日期必须显示。
qfq/hfq不是实际成交价；历史复权负值拒绝，不自动裁切或改成raw冒充相同研究。
工作数据、持仓、API配置放本地 `work/`、`private/` 或其他私有目录。
手机纯聊天不能通过一条命令获得它没有的shell能力；读SKILL.md不等于能执行Python。

