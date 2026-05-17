#!/usr/bin/env python3
"""
Hermes Auto-Learner Heartbeat Monitor v2.0
2分钟检测一次学习进程是否存活
运行到今天 17:30
"""

import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
LOG_FILE = HERMES_HOME / "logs" / "heartbeat_v2.log"
SCRIPT = HERMES_HOME / "scripts" / "auto_learn_v2.py"
STOP_TIME = datetime.now().replace(hour=17, minute=30, second=0, microsecond=0)
if STOP_TIME <= datetime.now():
    STOP_TIME += timedelta(days=1)

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def is_running():
    """检查学习进程是否在运行"""
    try:
        r = subprocess.run(["pgrep", "-f", "auto_learn_v2.py"], capture_output=True, text=True)
        return r.returncode == 0
    except:
        return False

def start_learner():
    """启动学习器"""
    log("🚀 启动 Auto-Learner v2.0...")
    subprocess.Popen(
        ["python3", str(SCRIPT)],
        stdout=open(HERMES_HOME / "logs" / "learner_v2_out.log", "w"),
        stderr=open(HERMES_HOME / "logs" / "learner_v2_err.log", "w"),
        start_new_session=True
    )
    time.sleep(3)

def main():
    log("💓 Heartbeat Monitor v2.0 启动!")
    log(f"⏰ 监控至: {STOP_TIME.strftime('%H:%M')}")
    log(f"📍 检测间隔: 2分钟")

    # 首次启动
    if not is_running():
        start_learner()
    else:
        log("✅ Auto-Learner 已在运行")

    check_count = 0

    while datetime.now() < STOP_TIME:
        time.sleep(120)  # 2分钟检测一次
        check_count += 1

        if is_running():
            log(f"💓 心跳 #{check_count}: ✓ 存活")
        else:
            log(f"⚠️ 心跳 #{check_count}: 停止! 重新启动...")
            start_learner()

    # 17:30 后确保 learner 也停止
    try:
        subprocess.run(["pkill", "-f", "auto_learn_v2.py"])
        log("🛑 Auto-Learner 已停止")
    except:
        pass

    log("🏁 Heartbeat Monitor 完成!")

if __name__ == "__main__":
    main()
