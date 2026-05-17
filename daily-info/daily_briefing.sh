#!/bin/bash
# ============================================
# 每日AI资讯推送脚本
# 每天自动抓取 + 整理 + 发微信
# ============================================
cd /home/ubuntu

# 1. 运行抓取（输出到JSON）
echo "[$(date '+%H:%M:%S')] 开始抓取资讯..."
python3 ai_briefing.py > /tmp/briefing_output.txt 2>&1

# 2. 找到最新的JSON文件
NEWS_FILE=$(ls -t /home/ubuntu/.hermes/ai_news/ai_news_*.json 2>/dev/null | head -1)

if [ -z "$NEWS_FILE" ]; then
    echo "未找到资讯JSON文件"
    exit 1
fi

echo "[$(date '+%H:%M:%S')] 资讯文件: $NEWS_FILE"

# 3. 读取服务器状态
UPTIME_DAYS=$(uptime | awk '{print $3}')
LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}')
DISK=$(df -h / | tail -1 | awk '{print $3"/"$2" ("$5")"}')
MEM=$(free -h | grep Mem | awk '{print $3"可用/"$2"总"}')

# 4. 整理成推送消息
MSG="📅 每日资讯 · $(date '+%m月%d日 %H:%M')"

MSG="${MSG}

🤖 AI资讯"

# 从JSON里读标题，格式化
COUNT=0
while IFS= read -r line; do
    TITLE=$(echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('title',''))" 2>/dev/null)
    SOURCE=$(echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('source',''))" 2>/dev/null)
    
    if [ -n "$TITLE" ] && [ $COUNT -lt 8 ]; then
        CLEAN_TITLE=$(echo "$TITLE" | sed 's/丨/, /g' | sed 's/，/, /g' | cut -c1-60)
        NUM=$((COUNT + 1))
        MSG="${MSG}

${NUM}. ${SOURCE}: ${CLEAN_TITLE}"
        COUNT=$((COUNT + 1))
    fi
done < <(cat "$NEWS_FILE" | python3 -c "import sys,json; [print(json.dumps(item)) for item in json.load(sys.stdin)]" 2>/dev/null)

# 5. 服务器状态
MSG="${MSG}

🖥️ 服务器状态
• 运行时间: ${UPTIME_DAYS}天
• 负载: ${LOAD}
• 磁盘: ${DISK}
• 内存: ${MEM}"

# 6. 域名状态
ZX_CHECK=$(curl -sI --connect-timeout 5 https://zxclx.cn 2>/dev/null | head -1)
if echo "$ZX_CHECK" | grep -q "200"; then
    MSG="${MSG}
• zxclx.cn: ✅ 正常"
else
    MSG="${MSG}
• zxclx.cn: ⚠️ 异常"
fi

MSG="${MSG}

⏰ $(date '+%H:%M:%S') 自动推送"

echo "$MSG" > /tmp/daily_msg.txt
echo "[$(date '+%H:%M:%S')] 消息已生成"
cat /tmp/daily_msg.txt
