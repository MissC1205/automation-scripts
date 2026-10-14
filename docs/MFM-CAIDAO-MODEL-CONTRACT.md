# MFM × 采道采集器：统一模型数据契约与操作手册

更新：2026-10-14。仓库：MissC1205/automation-scripts。

## 固定入口
- 每次预测先读取 mfm-data/caidao-live/latest-summary.json，记录 collected_at_bj、last_snapshot_path、quality_gate、fixture_pool_integrity、betting_gate。
- 再读取 last_snapshot_path 对应原始快照；不能只根据汇总数量推断每场信息完整。
- 核验比赛编号、主客队、开赛时间、比赛状态、赛事来源池；球队匹配不得仅依赖相似名称，需赛事日期/联赛/主客/外部ID交叉确认。
- 每次预测优先运行或检查现有 MFM GitHub Actions 工作流（具体工作流名称以仓库当前配置为准）；失败时检查日志、上游限流、数据结构变化、空结果、重复行与球队匹配。禁止重新建立并行采集器或无故覆盖旧采集器。

## 数据使用与安全门禁
- 采道第三方 SPF 与让球SP必须标注第三方；verified_official_jc_sp_matches 为0时不得称为官方竞彩SP。
- 区分赛前快照和开赛后采集。开赛后采集的数据不可倒灌赛前预测或回测。
- 缺少让球历史、交易所资金、官方SP、伤停等字段必须标注缺失；不得编造。
- 数据源池完整不等于可下注。betting_gate为BLOCKED时不可宣称完成EV投注筛选。
- 独立1X2 Raw概率先根据实力、近期、主客、赛程、伤停、xG等非市场因素形成；采道赔率随后只用于价值/波动/风险校验。其他玩法独立建模。

## 每次预测标准顺序
1. 检查最新工作流状态及快照时间，必要时触发既有工作流并等待产物。
2. 核对当日完整赛事池、各场编号、主客队、开赛时间和映射置信。
3. 汇总各玩法当前报价、赔率历史及缺口；与官方及其他可信来源交叉验证。
4. 独立建模：1X2、比分/净胜球、官方整数让球、总进球、半全场；特别检查平局和爆冷。
5. 对比赔率变化与市场微结构；注明无法取得的买量、交易所数据。
6. 每场输出至少三项可核实依据、主方向、次选条件、最优玩法、置信等级与风险；不默认防平。
7. 串关最多推荐一组2串1；赔率、EV和收益必须使用同一时点已核实的价格；未核实则不给精确收益。
8. 按时间戳保存预测版本；赛前最后一次有效版本作为正式复盘基准，赛后不得改写。
9. 将快照路径、采集质量、模型版本、预测、最终比分、盈亏、CLV和复盘同步到Notion（需有可写页面及实际写入成功）。

## 已验证基线（2026-10-14 21:35北京时间）
fixture_ids=14; detail_objects=14; current_spf_prices=14; current_handicap_prices=14; historical_spf_rows=98; captured_before_kickoff=10; captured_after_kickoff=4; verified_official_jc_sp_matches=0; third_party_handicap_historical_rows=0; betting_gate=BLOCKED_REQUIRES_OFFICIAL_SP_INDEPENDENT_PROBABILITIES_AND_EV。

## 维护规则
只维护一个采集器与一个统一模型。新源作为可追溯适配器加入，先影子测试，再启用。保留旧快照和失败日志；异常不得静默回退为完整数据。README及Notion使用相同的数据契约；任何改动须核对工作流实际运行。