#!/bin/bash
cd /home/ubuntu/longnan-new
echo '🔄 拉取最新代码...'
sudo git pull

echo '🔨 构建 Docker 镜像...'
sudo docker build -t longnan-enterprise:latest .

echo '🛑 停止旧容器...'
sudo docker rm -f longnan-enterprise 2>/dev/null

echo '🚀 启动新容器...'
sudo docker run -d --name longnan-enterprise -p 8080:8080 longnan-enterprise:latest

echo '✅ 部署完成！'
curl -s -o /dev/null -w 'HTTP状态码: %{http_code}\n' http://localhost:8080/
