import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
import yaml
from pathlib import Path

class NotificationService:
    """通知服务 - 支持微信、短信、邮箱"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.notification_config = config.get("notifications", {})
    
    async def send_alert(self, alert_type: str, severity: str, title: str, message: str):
        """发送告警通知"""
        tasks = []
        
        # 企业微信
        if self.notification_config.get("wechat", {}).get("enabled", False):
            tasks.append(self.send_wechat(title, message, severity))
        
        # 短信
        if self.notification_config.get("sms", {}).get("enabled", False) and severity == "critical":
            tasks.append(self.send_sms(title, message))
        
        # 邮件
        if self.notification_config.get("email", {}).get("enabled", False):
            tasks.append(self.send_email(title, message, severity))
        
        # 并行发送所有通知
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "wechat": "success" if not isinstance(results[0], Exception) else "failed",
            "sms": "success" if len(results) > 1 and not isinstance(results[1], Exception) else "failed",
            "email": "success" if len(results) > 2 and not isinstance(results[2], Exception) else "failed"
        }
    
    async def send_wechat(self, title: str, message: str, severity: str):
        """发送企业微信通知"""
        try:
            wechat_config = self.notification_config["wechat"]
            
            # 获取access_token
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wechat_config['corp_id']}&corpsecret={wechat_config['secret']}"
            token_response = requests.get(token_url)
            token_data = token_response.json()
            
            if token_data.get("errcode") != 0:
                raise Exception(f"获取微信token失败: {token_data.get('errmsg')}")
            
            access_token = token_data["access_token"]
            
            # 构建消息内容
            color_map = {
                "critical": "warning",
                "warning": "info",
                "info": "comment"
            }
            
            data = {
                "touser": "@all",
                "msgtype": "textcard",
                "agentid": wechat_config["agent_id"],
                "textcard": {
                    "title": title,
                    "description": message,
                    "url": "http://localhost:3000/alerts",
                    "btntxt": "查看详情"
                }
            }
            
            # 发送消息
            send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            response = requests.post(send_url, json=data)
            result = response.json()
            
            if result.get("errcode") != 0:
                raise Exception(f"发送微信消息失败: {result.get('errmsg')}")
            
            return {"status": "success"}
        except Exception as e:
            print(f"微信通知发送失败: {str(e)}")
            raise
    
    async def send_sms(self, title: str, message: str):
        """发送阿里云短信通知"""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
            
            sms_config = self.notification_config["sms"]
            
            client = AcsClient(
                sms_config["access_key_id"],
                sms_config["access_key_secret"],
                "cn-hangzhou"
            )
            
            request = SendSmsRequest()
            request.set_PhoneNumbers("13800138000")  # 需要配置接收手机号
            request.set_SignName(sms_config["sign_name"])
            request.set_TemplateCode(sms_config["template_code"])
            request.set_TemplateParam(f'{{"title":"{title}","content":"{message[:50]}"}}')
            
            response = client.do_action_with_exception(request)
            
            return {"status": "success"}
        except Exception as e:
            print(f"短信通知发送失败: {str(e)}")
            raise
    
    async def send_email(self, title: str, message: str, severity: str):
        """发送邮件通知"""
        try:
            email_config = self.notification_config["email"]
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = email_config["from_address"]
            msg['To'] = ", ".join(email_config["to_addresses"])
            msg['Subject'] = f"[{severity.upper()}] {title}"
            
            # 邮件正文
            body = f"""
            <html>
            <body>
                <h2>{title}</h2>
                <p><strong>严重级别:</strong> {severity}</p>
                <p><strong>时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>{message}</p>
                <hr>
                <p><small>此邮件由华为网络设备自动化运维系统自动发送</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # 发送邮件
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                server.starttls()
                server.login(email_config["smtp_username"], email_config["smtp_password"])
                server.send_message(msg)
            
            return {"status": "success"}
        except Exception as e:
            print(f"邮件通知发送失败: {str(e)}")
            raise

import asyncio
from datetime import datetime
