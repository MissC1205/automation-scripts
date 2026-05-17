#!/bin/bash
cd /home/ubuntu/longnan-new
sudo git fetch origin 2>/dev/null
LOCAL=$(sudo git rev-parse HEAD 2>/dev/null)
REMOTE=$(sudo git rev-parse @{u} 2>/dev/null)
if [ "$LOCAL" != "$REMOTE" ]; then
  echo "$(date) - 检测到新代码，开始部署..." >> /home/ubuntu/deploy-log.txt
  /home/ubuntu/deploy.sh >> /home/ubuntu/deploy-log.txt 2>&1
  echo "$(date) - 部署完成" >> /home/ubuntu/deploy-log.txt
fi
