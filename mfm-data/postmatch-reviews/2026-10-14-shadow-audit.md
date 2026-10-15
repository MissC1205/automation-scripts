# 2026-10-14 MFM 14场赛后研究版对照（非FINAL）

来源：GitHub 2026-10-14 21:35 采道快照 `mfm-data/caidao-live/2026-10-14/20261014T213538071228+0800.json` 的赛事身份；Notion 14场SHADOW研究初判 https://app.notion.com/p/3f97ffb409ee81749eb2ff3eb0b19d23；赛果来自公开赛事组织方/赛果资料，需逐场自动化二次核验后才可升级为官方结算。

**重要：这不是赛前最后有效FINAL，不可计入正式月度投注业绩；采道快照没有赛后比分字段，赛果由独立网页核验得到。**

|编号|对阵|SHADOW普通1X2|90分钟比分|实际1X2|研究命中|
|---|---|---|---|---|---|
|001|墨尔本胜利—首尔FC|负|3:0|胜|失|
|002|神户胜利—全北现代|胜|2:0|胜|中|
|003|柏太阳神—泰港|胜|5:1|胜|中|
|004|横滨水手—清水鼓动|胜|2:1|胜|中|
|005|费耶诺德—科莫|负|3:2|胜|失|
|006|LASK—利物浦|负|3:6|负|中|
|007|诺维奇—南安普敦|平|0:1|负|失|
|008|罗马—皇马|负|3:4|负|中|
|009|博德闪耀—多特蒙德|平|1:0|胜|失|
|010|贝蒂斯—波尔图|胜|3:2|胜|中|
|011|曼城—巴黎|胜|2:4|负|失|
|012|维拉—费内巴切|胜|6:0|胜|中|
|013|弗鲁米嫩塞—帕尔梅拉斯|平|1:2|负|失|
|014|圣路易斯—温哥华|胜|3:1|胜|中|

研究版14场8中6失，57.14%；仅方向研究准确率。原始SHADOW总进球双候选命中002、004，2/14；不代表完整概率模型校准表现。

赛果来源：https://www.psg.fr/en/content/uefa-champions-league-matchday-2-results-2026-2027-manchester-city-paris-saint-germain ; https://melbournevictory.com.au/news/victory-hit-three-to-sink-seoul/ ; https://www.jleague.jp/en/club/kashiwa/ ; https://www.f-marinos.com/matches/results ; https://www.footballwebpages.co.uk/match/2026-2027/sky-bet-championship/norwich-city/southampton/567991 ; https://www.uol.com.br/esporte/futebol/ultimas-noticias/2026/10/14/fluminense-x-palmeiras---libertadores.ghtm ; https://www.covers.com/sport/soccer/mls/teams/main/saint-louis-city-sc

## 结构性错误与改进候选
1. 001客胜误判：跨洲主客场与轮换权重需重检；赛后主队三球获胜。
2. 005客胜误判：欧冠首轮表现外推过重、费耶诺德主场强度低估。
3. 007平局误判：客队近期强势、主队防守脆弱，赛后0:1；赛后xG诺维奇1.15、南安普敦2.4（来源FootballWebPages），研究平局依据不足。
4. 009平局误判：爆冷风险已标很高，但研究Primary未转成主胜；应检验北欧主场与对位强度。
5. 011曼城主胜误判：研究已标极高爆冷风险，却依然把主胜方向选为Primary；不能将强队名气当成风险消除。
6. 013平局误判：淘汰赛首回合90分钟平局倾向高估，反击效率与阵容伤停需单独建模。
7. 总进球双候选仅2/14，严重漏掉6–9球极端尾部；需验证总进球分布、过度离散参数及比赛状态转移，先做影子回测不直接修改生产权重。
8. 数据链：采道赔率快照缺赛后结果字段、官方SP未核验、历史让球赔率缺失；必须构建按销售日+赛事ID回填、官方交叉核验与不可变赛前预测关联。

## 正式结算限制
无经核验的最后有效FINAL与官方SP，正式2串1命中率/盈亏/CLV均不得据此生成。此前海报出现未经核验的盈利数字，不能作为真实成绩。
