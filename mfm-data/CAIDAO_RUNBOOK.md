# MFM 采道采集器：日常使用说明

当前入口：`mfm-data/mfm_caidao_service.py`  
GitHub Actions：`.github/workflows/mfm-caidao-service.yml`

## 1. 如何使用

- **自动刷新**：北京时间每天约 **10:05、15:05、18:05、21:05、23:05**。GitHub Actions 定时任务存在延迟，不能保证精确分钟。
- **GitHub手动刷新**：打开 Actions → **MFM Caidao Daily and On-Demand** → **Run workflow**。日期为空表示北京时间今天；也可输入 `YYYY-MM-DD`，但历史比赛只有在采道服务端仍提供数据时才能采集。
- **聊天请求刷新**：用户可说“刷新今天采道数据/重新预测008”。在GitHub连接可写的情况下，助手更新 `mfm-data/caidao-control/refresh.txt`，它的 push 事件触发同一个工作流。需要等待完成并读取产物；若当前无法触发，则只提供明确标注时间的最新已存档数据，绝不声称已刷新。
- **本地运行**（必须有公开网页网络连通）：`python mfm-data/mfm_caidao_service.py --date 2026-10-14`。

## 2. 数据文件和长期保留

- `mfm-data/caidao-live/latest-summary.json`：小文件，当前已存档赛单、每场最新三项SP、数据覆盖率和采集时间。
- `mfm-data/caidao-live/latest.json`：完整采集结果，每场基本资料、SP历史、源时间戳、字段质量。
- `mfm-data/caidao-live/latest-football-only.json`：**仅足球事实特征**（采道提供，未经外部逐项验证）。不含赔率或采道预测结论；独立模型必须先读取它。
- `mfm-data/caidao-live/latest-market-only.json`：当前普通/整数让球报价和普通胜平负历史报价；必须在冻结独立判断后才读取。
- `mfm-data/caidao-live/YYYY-MM-DD/YYYYMMDDTHHMMSSffffff+0800.json`：每次采集不可覆盖的时间戳快照。该销售日目录下另外保存最新、足球事实和市场数据。
- 每次GitHub运行还保存一个45天的独立artifact。仓库快照本身无45天自动删除规则；注意长期体积和服务平台的公开数据使用条款。

**注意：仓库是公开的。绝不要写入API key、登录令牌、手机号、用户账户、个人下注明细等。**

## 3. 取数范围与质量纪律

通过采道公开H5的只读接口获取：

1. `GET /api/web/game/footballQuery?type=0`：在售/即时比赛；`type=1`：近期赛果，补回当天已完成的编号。
2. `POST /api/web/game/getMatchAllData`，参数 `matchInfo`：近期状态、攻防字段、历史交锋及阵容相关结构等。
3. `POST /api/web/game/getJcOddsDetail`，参数 `matchInfo`：普通胜平负历史，真实记录位置是 `result.oddsDetails[]`。

检测日期-比赛ID映射、主客身份、赔率三项数值与时间戳、报价时间是否异常、历史记录是否重复、当前SP与历史最新一条是否一致。API失败会明确保存，绝不把接口返回200直接当“完整数据”。

采道记录均属于**第三方转载/聚合数据**，不是直接从中国竞彩网成功取得的官方SP。官方竞彩SP接口此前仍返回 HTTP 567。

- 让球的当前展示SP和让球数已能采集，但**让球玩法的完整历史时间序列尚未证明可用**。
- 13/14个伤停数据结构存在不等于真实确定缺阵；要由俱乐部/官方赛事核验。
- 数据结构存在不等于完整5/10场可比较战绩，也不等于已经拥有完整 xG、首发、裁判、买量。
- 采集器**禁止引入第三方泊松概率、外部预测结论或专家观点**到独立模型。
- 采集时间晚于开球的快照标记 `POST_KICKOFF`，不能用后来抓到的历史报价假装此前已保存正式预测。

## 4. 预测流程

**不可跳过的顺序：**

1. 检查 `latest-summary.json` 日期/采集时间、覆盖率和 `quality_gate`。
2. 先读取 `latest-football-only.json`，结合独立来源核验球队强度、近期5/10场、对手强度、主客、伤停和赛程。
3. 生成并**明确记录版本和冻结时间**的独立90分钟胜/平/负方向；概率只有校准后才能作为正式胜率。
4. 再读取 `latest-market-only.json`：核验竞彩整数让球、SP时点、普通胜平负开盘-现盘、平局和爆冷变化。
5. 对普通胜平负、让球、总进球、比分/半全场**分别判断**，输出每场至少3条证据、最强反证、防平结论、数据缺口和置信度。
6. 最佳 **2串1** 必须有可信国内SP、单腿赔率达用户阈值及独立校准概率的正EV证据。否则仍可给研究性赛果方向，但标记 **NO BET**，不能重仓或称稳赢。

目前自动化完成的是**数据层**。独立完整MFM模型、历史回测与校准概率引擎尚未实现；不能把“采集成功”升级表述为“预测系统已跑通”。

## 5. 故障排查

- 运行绿色 ≠ 数据完整。必须查 `quality_gate`：`RESEARCH_DATA_AVAILABLE`、`PARTIAL_RESEARCH_DATA`、`NO_DATA`。
- 如果最新文件日期不是用户要求的日期，必须明确“仅有旧快照”。
- HTTP 401/403/429/567 视作访问限制，停止相关请求，不使用身份伪装或绕过验证码。
- 临时DNS/5xx按脚本规则有限重试；请求失败必须保留来源/错误类型/时间。
- GitHub并发写入时先 `git fetch` + `git rebase` 再重试 push。无法提交时从该运行的 artifact 读取，不可声称仓库文件已更新。
- 修改模型脚本不能借机重启免费 API-Football 全量探测，以免浪费免费额度。
