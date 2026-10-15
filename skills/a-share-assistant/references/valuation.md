# 估值框架

复用thesis/comps/DCF/财报流程，重建中国公告、会计口径、人民币折现和治理风险。
银行看ROE/PB、资产质量与资本；保险核特定口径；周期看正常化利润；稳定企业可FCFF。
亏损成长不能PE强估。同业务同周期同行、同交易日/估值年度/币种，负分母不输出正倍数。
DCF三个情景：bear/base/bull，每个包含fcff数组、wacc、terminal_growth、net_debt、shares、currency=CNY、unit=CNY_and_shares。
净债务桥必须明确其他非经营资产、少数股东等，程序不会自动补齐。
WACC>g，稳定期FCFF>0、稀释股数>0；终值占比过高须指出敏感性。
输入示例仅教学；计算正确不代表假设正确。使用原公告/模型输入说明事实与估计。

