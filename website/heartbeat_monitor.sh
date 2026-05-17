#!/bin/bash
# 网站心跳监控 - 2分钟检测一次，故障自动重启+记录日志
# 监控目标：https://zxclx.cn

SITE_URL="https://zxclx.cn"
CONTAINER_NAME="longnan-enterprise"
LOG_FILE="/home/ubuntu/heartbeat.log"
MAX_RESTART=5  # 最多连续重启次数

count=0
last_action=""

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

check_site() {
    # 检测HTTP状态码
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SITE_URL")
    if [ "$HTTP_CODE" = "200" ]; then
        return 0
    else
        return 1
    fi
}

restart_site() {
    log "⚠️ 检测到故障，HTTP=$1，执行重启..."
    sudo docker restart $CONTAINER_NAME
    sleep 5
    last_action=$(date '+%m-%d %H:%M')
}

# 主循环
while true; do
    if check_site; then
        status="✅ 在线"
        if [ $((count % 10)) -eq 0 ]; then
            log "💓 心跳正常 ($last_action)"
        fi
        count=0
    else
        count=$((count + 1))
        if [ $count -le $MAX_RESTART ]; then
            restart_site "$HTTP_CODE"
        else
            log "🚨 连续重启$count次仍有故障，请人工检查！"
            count=0  # 重置避免日志刷屏
        fi
    fi
    sleep 120  # 2分钟
done
