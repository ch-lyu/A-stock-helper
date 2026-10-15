# A-stock-helper｜给家人用的 A 股投资研究助手

**一个家庭入口 + 12 个中文专业模块 + 可执行 Python 工具**，随包保留10套公开原始投研技能及参考资料、A股适配底稿、量化/缠论规则卡、可导出的版本化研究记录。

**v0.3升级：**新增34套有许可的原始参考归档、Notion投资目录484项逐项覆盖清单、财报排雷/估值治理/因子HPO/龙虎榜流程；新增可执行risk、financial-audit与valuation-review。475个已恢复投资模块另提供私有扩展资料备份，未宣称全部执行验证或完整覆盖整个Notion工作区。缺源与停用项目明确保留。

你可以直接对支持技能和命令执行的 AI 说：

> 用 A 股助手帮我看看600519。先核实最新公告和数据，再解释它靠什么赚钱、价格隐含什么、主要风险是什么。用我能理解的中文，不要只给一个分数。

程序负责取数据、检查口径、确定计算与回测；AI负责结合公告原文解释。它不连接券商，不自动下单。

给家人直接阅读：[妈妈使用指南](docs/MOM_GUIDE.md)，包含可复制给AI的安装说明和中文提问示例。

**给妈妈的手机路线：**由家人在她自己的扣子账号上传、预览并部署整合技能包。以后她在对话中选择“A股家庭投研助手”提问，无需记12个模块或运行命令。[导入与验收步骤](docs/COZE_SETUP.md)。本地包已验证，目标账号的Python/联网/个人记录持久化尚未验收；不声称已安装到豆包。

构建可导入的完整ZIP：

```bash
python scripts/export_suite.py --out dist/a-share-family-suite.zip
```

ZIP包含根SKILL.md、全部模块、原始参考及许可、独立运行器、模板和逐文件哈希manifest。官方扣子流程会解析、安全检测并重新打包，目标环境可能需要适配，见导入指南。原来单段手机提示词保留作有限降级入口，不作为完整专业包。

## 安装：把这条命令交给她的 AI

前提：电脑上的 AI 有终端权限，已安装 Git 和 Python 3.10+。在一个新的工作目录执行。

**Codex：**

```bash
git clone https://github.com/ch-lyu/A-stock-helper.git && cd A-stock-helper && python3 scripts/install.py --target codex
```

**Claude Code：**

```bash
git clone https://github.com/ch-lyu/A-stock-helper.git && cd A-stock-helper && python3 scripts/install.py --target claude
```

**其他支持 Agent Skills 的 AI：**

```bash
python3 scripts/install.py --target generic --dest /实际技能目录
```

Windows 使用 `python` 替代 `python3`；PowerShell旧版不支持`&&`时逐行执行。安装器会复制所有技能和共享运行器，保留其他技能，拒绝覆盖同名未知技能或已修改文件。重复运行无变化；更新先 `git pull --ff-only`，再安装加 `--replace-managed`。

安装器输出 `doctor_command`，让AI运行它检查Python。再让AI确认能发现 `a-share-assistant`；**文件复制成功与客户端技能发现是两个检查**。不同AI可能需重新加载技能。

**ChatGPT手机或其他纯聊天环境**通常不能执行这些本地命令。可以阅读技能说明，但要运行程序，仍需支持终端的AI/电脑执行环境。本仓库的plugin.json是技能包元数据，不会自动把GitHub仓库安装到ChatGPT账号；其他客户端能否导入要按它的功能确认。

## 开启新闻与财报数据

腾讯日K、CSV分析、估值计算和回测核心不需额外Python包。新闻和AKShare行情需可选依赖：

```bash
python3 -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell 使用 .venv\Scripts\Activate.ps1
python -m pip install -e '.[data]'
python -m astock doctor
```

让AI用这个venv的Python执行技能运行器。Tushare财报/限价接口另需环境变量 `TUSHARE_TOKEN` 及相应权限，部分数据可能收费。无需提供模型API密钥：使用妈妈现有的AI，确定计算不调用LLM API。不要把Token、账户或私人持仓提交到公共仓库。

## 能做什么

| 技能 | 用法例子 |
|---|---|
| a-share-assistant | 帮我完整研究这家公司 |
| a-share-data-audit | 检查行情、复权和财报时间是否可信 |
| a-share-fundamentals | 这次财报的增长质量怎么样 |
| a-share-valuation | 给我三种估值情景，解释假设 |
| a-share-policy-news | 查近期消息，哪些是真的影响利润 |
| a-share-technical-review | 看趋势，区分形成中和已确认结构 |
| a-share-screener | 从我的观察名单里筛选研究候选 |
| a-share-quant-validation | 验证这个策略，有没有过拟合 |
| a-share-portfolio-review | 看我的持仓有哪些集中风险 |
| a-share-weekly-review | 用一页中文整理本周变化 |
| a-share-thesis-tracker | 跟踪当初买入逻辑有没有被推翻 |
| a-share-source-discovery | 找并审核新的数据、工具和skills |

方法复用了已有Notion美股研究与量化方法，补充归母/扣非、政策传导、治理、A股规则与历史信息时点。私人页面原文/持仓不公开；Notion描述的本地源码尚未取得，不冒充直接复用了脚本。公开Apache-2.0资料独立置于vendor并保留许可；本项目原创代码MIT。[具体采用映射](skills/a-share-assistant/references/adoption-map.md)。

## 常用命令

在仓库根目录执行；安装后AI也可用主技能内 `scripts/astock.py`。

```bash
python scripts/astock.py doctor
python scripts/astock.py fetch 600519 --start 2020-01-01 --adjust raw --out work/600519-raw.csv
python scripts/astock.py audit work/600519-raw.csv
python scripts/astock.py analyze work/600519-raw.csv --out work/600519.md
python scripts/astock.py news 600519 --out work/600519-news.json
python scripts/astock.py fundamentals 600519 --as-of 2026-10-07 --out work/600519-finance.json
python scripts/astock.py valuation examples/dcf.json --out work/dcf-demo.json
python scripts/astock.py portfolio examples/holdings.csv --out work/risk-demo.json
python scripts/astock.py financial-audit examples/synthetic-financials.json --out work/financial-demo.json
python scripts/astock.py valuation-review examples/synthetic-valuation-review.json --out work/valuation-review.json
python skills/a-share-assistant/scripts/references.py list --query factor
```

`analyze`只自动生成**行情证据**，完整投研需要AI补查财报/公告、估值和反方观点。`examples/`全部是教学输入，**不是实际持仓、公司行动或公司估值**。

risk需要持仓快照及每只股票带来源元数据的复权CSV，至少60个相同起止区间收益；输出相关性、风险贡献与历史VaR/ES，属于当前权重风险代理。financial-audit仅6类线索，valuation-review不自动通过治理门禁。输入格式见主技能references/advanced-tools.md。

原始参考的脚本不自动执行。references.py仅哈希校验、检索、解包；各自API/ML库/PandaData和原项目依赖未接成核心能力。源许可独立于原创MIT代码，见THIRD_PARTY_NOTICES.md。

量化研究示例：

```bash
python scripts/astock.py fetch 600519 --start 2018-01-01 --adjust qfq --out work/600519-qfq.csv
python scripts/astock.py validate work/600519-qfq.csv --out work/validation.json
python scripts/reproduce_validation.py --out work/study.json
```

严格原始价格账本需已核元数据、逐日实际涨跌停和完整公司行动：

```bash
python scripts/astock.py backtest your-raw.csv --mode ledger --strict --corporate-actions-complete --actions your-actions.json --out work/ledger.json
```

不能直接用教学公司行动或声明代替事实。复权收益代理不含真实股数、最低佣金、涨跌停/停牌可成交性；它是信号研究，不是实盘收益证明。

## 验证与资料

- [实际验证结果与限制](docs/VALIDATION.md)：测试、安装、真实数据、回测和独立技能试用。
- [数据/新闻/政策来源](docs/DATA_SOURCES.md)：哪些已实现、哪些需AI原文核查或后续接入。
- [GitHub资源审查](docs/RESEARCH.md)：20个项目入口、commit、许可和采用决策。
- [回测协议](skills/a-share-assistant/references/backtest.md)：资金、时间、成本与独立留出。
- [开发规格](docs/SPEC.md)：实现边界。

本版没有全市场PIT数据库、实时L2、已验证缠论引擎、自动交易或盈利保证；已有相应研究流程和扩展路径。把这些限制写在结果里，比编造“完美助手”更有用。

## 开发检查

```bash
python -m pip install -e '.[dev]'
python -m unittest discover -s tests -v
python -m ruff check src scripts tests
python scripts/check_skills.py
```

MIT许可仅覆盖本项目原创代码和技能；底层数据/第三方项目适用各自条款。
