# 技能与个人记录保存协议

技能安装保存方法，档案/持仓/研究结果是另一类数据。不要依赖聊天记忆，不因云端部署就承诺临时目录永久保存。

## 进入与退出

用户明确指定私有持久目录后，用当前用户的库先list/get档案和研究；旧持仓核日期，不继承开发者资料。无已验证持久目录则提供可下载交接文件，标跨聊天保存待验。只保存确认的事实，未知null；不收账号密码/验证码/API密钥。

RECORD为本技能scripts/records.py；整合包为根scripts/records.py。标准库SQLite，位置显式指定，不上传、不自动git提交。

```text
python RECORD --store /私有持久目录/research.sqlite put profile assets/profile-template.json
python RECORD --store /私有持久目录/research.sqlite get profile
python RECORD --store /私有持久目录/research.sqlite put thesis:600519.SH work/thesis.json
python RECORD --store /私有持久目录/research.sqlite export --out /私有持久目录/handoff.json
python RECORD --store /新目录/research.sqlite import /私有持久目录/handoff.json
```

示例路径须替换，null不能替用户猜填。put保留旧版，相同内容不增版；返回哈希和版本。export全部版本，import先校验内容与冲突；交接文件含私有资料，只放用户指定位置。未保存成功就说明。

## 验收

教学记录→导出→新目录/新进程导入→读取版本/哈希一致，仅证明工具文件可迁移，不证明云端自动持久、跨账号共享或后台更新。

手机端还需验：新任务点选已部署技能、读取教学记录、导出恢复、数据网络/依赖。未经目标账号验收的项列明，不让妈妈调试。

