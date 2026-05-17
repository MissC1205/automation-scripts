#!/bin/bash
# ============================================================
# 备案信息监控脚本 - 第4层防护
# 每5分钟检查线上网站是否包含备案信息
# 缺少时自动发送告警并写日志
# 备案号: 赣ICP备2026009729号-1
# ============================================================

ICP="赣ICP备2026009729号-1"
LOG="/var/log/icp-monitor.log"
ALERT_LOG="/var/log/icp-alert.log"
SITE_URL="https://zxclx.cn"

# 检查网站
RESPONSE=$(curl -s -o /tmp/icp_check.html -w "%{http_code}" "$SITE_URL" 2>/dev/null)

if [ "$RESPONSE" != "200" ]; then
    echo "[$(date)] ⚠️ 网站无法访问 HTTP $RESPONSE" >> "$LOG"
    exit 1
fi

# 检查备案信息
if ! grep -q "$ICP" /tmp/icp_check.html 2>/dev/null; then
    echo "[$(date)] 🚨 严重告警: 网站缺少备案信息！备案号: $ICP" >> "$ALERT_LOG"
    echo "[$(date)] 🚨 严重告警: 网站缺少备案信息！" >> "$LOG"
    
    # 尝试自动恢复: 用备份的 index.html 替换
    if [ -f /home/ubuntu/agent-web/dist-backup/index.html ]; then
        cp -r /home/ubuntu/agent-web/dist-backup/* /home/ubuntu/agent-web/dist/
        echo "[$(date)] ✅ 已从备份自动恢复备案信息" >> "$LOG"
    fi
    
    exit 2
else
    echo "[$(date)] ✅ 备案信息正常" >> "$LOG"
fi

# 日志轮转: 只保留最近1000行
tail -1000 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG" 2>/dev/null
