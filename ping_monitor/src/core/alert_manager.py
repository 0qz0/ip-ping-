#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
import json
from plyer import notification
import winsound
from dotenv import load_dotenv

@dataclass
class AlertConfig:
    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    desktop_notification: bool = True
    sound_alert: bool = True
    sound_file: str = ""

class AlertManager:
    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or AlertConfig()
        self.alert_history: List[Dict] = []
        self._load_config()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> None:
        """从环境变量加载配置"""
        load_dotenv()
        
        if not self.config.email_username:
            self.config.email_username = os.getenv("ALERT_EMAIL_USERNAME", "")
        if not self.config.email_password:
            self.config.email_password = os.getenv("ALERT_EMAIL_PASSWORD", "")
        if not self.config.email_smtp_server:
            self.config.email_smtp_server = os.getenv("ALERT_EMAIL_SMTP_SERVER", "")
        if not self.config.email_recipients:
            recipients = os.getenv("ALERT_EMAIL_RECIPIENTS", "")
            self.config.email_recipients = [r.strip() for r in recipients.split(",")] if recipients else []

    def send_alert(self, ip: str, message: str, alert_type: str = "error") -> None:
        """发送报警"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "ip": ip,
            "message": message,
            "type": alert_type
        }
        self.alert_history.append(alert_data)
        
        # 发送桌面通知
        if self.config.desktop_notification:
            try:
                notification.notify(
                    title=f"IP监控报警 - {ip}",
                    message=message,
                    app_name="IP Ping Monitor"
                )
            except Exception as e:
                self.logger.error(f"发送桌面通知失败: {str(e)}")

        # 播放声音
        if self.config.sound_alert:
            try:
                if self.config.sound_file and os.path.exists(self.config.sound_file):
                    winsound.PlaySound(self.config.sound_file, winsound.SND_FILENAME)
                else:
                    winsound.Beep(1000, 1000)  # 默认蜂鸣声
            except Exception as e:
                self.logger.error(f"播放声音报警失败: {str(e)}")

        # 发送邮件
        if self.config.email_enabled and self.config.email_recipients:
            self._send_email_alert(ip, message)

    def _send_email_alert(self, ip: str, message: str) -> None:
        """发送邮件报警"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.email_username
            msg["To"] = ", ".join(self.config.email_recipients)
            msg["Subject"] = f"IP监控报警 - {ip}"
            
            body = f"""
            IP地址: {ip}
            时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            报警信息: {message}
            """
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port) as server:
                server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
                
            self.logger.info(f"邮件报警已发送: {ip}")
        except Exception as e:
            self.logger.error(f"发送邮件报警失败: {str(e)}")

    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """获取报警历史记录"""
        return self.alert_history[-limit:]

    def clear_alert_history(self) -> None:
        """清除报警历史记录"""
        self.alert_history.clear()

    def save_alert_history(self, filepath: str) -> None:
        """保存报警历史记录到文件"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.alert_history, f, ensure_ascii=False, indent=2)
            self.logger.info(f"报警历史记录已保存到: {filepath}")
        except Exception as e:
            self.logger.error(f"保存报警历史记录失败: {str(e)}")

    def load_alert_history(self, filepath: str) -> None:
        """从文件加载报警历史记录"""
        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    self.alert_history = json.load(f)
                self.logger.info(f"已从 {filepath} 加载报警历史记录")
        except Exception as e:
            self.logger.error(f"加载报警历史记录失败: {str(e)}") 