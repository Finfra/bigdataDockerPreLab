# notification/alert_manager.py
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class AlertManager:
    def __init__(self, config):
        self.config = config
        self.slack_webhook = config.get('slack_webhook')
        self.email_config = config.get('email')
        
    def send_slack_alert(self, message, severity="INFO"):
        """Slack 알림 전송"""
        if not self.slack_webhook:
            return False
            
        color_map = {
            "INFO": "#36a64f",      # 녹색
            "WARNING": "#ff9900",   # 주황색  
            "ERROR": "#ff0000",     # 빨간색
            "CRITICAL": "#8B0000"   # 진빨간색
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(severity, "#36a64f"),
                    "title": f"FMS Alert - {severity}",
                    "text": message,
                    "timestamp": datetime.utcnow().timestamp(),
                    "fields": [
                        {
                            "title": "Timestamp",
                            "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": severity,
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Slack 알림 전송 실패: {e}")
            return False
    
    def send_email_alert(self, subject, message, recipients):
        """이메일 알림 전송"""
        if not self.email_config:
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # HTML 형태 메시지
            html_message = f"""
            <html>
            <body>
                <h2>FMS System Alert</h2>
                <p><strong>Timestamp:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                <p><strong>Message:</strong></p>
                <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
                    {message}
                </div>
                <br>
                <p><em>This is an automated alert from FMS monitoring system.</em></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_message, 'html'))
            
            # SMTP 서버 연결
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['from'], recipients, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"이메일 알림 전송 실패: {e}")
            return False
    
    def process_alert(self, alert_data):
        """알림 데이터 처리 및 전송"""
        severity = alert_data.get('severity', 'INFO')
        message = alert_data.get('message', '')
        device_id = alert_data.get('device_id', 'Unknown')
        
        # 메시지 포맷팅
        formatted_message = f"Device {device_id}: {message}"
        
        # 심각도에 따른 알림 채널 결정
        if severity in ['ERROR', 'CRITICAL']:
            # 이메일 + Slack 모두 전송
            self.send_email_alert(
                subject=f"FMS {severity} Alert - Device {device_id}",
                message=formatted_message,
                recipients=self.config.get('alert_recipients', [])
            )
            self.send_slack_alert(formatted_message, severity)
        elif severity == 'WARNING':
            # Slack만 전송
            self.send_slack_alert(formatted_message, severity)
        else:
            # INFO 레벨은 로그만 기록
            print(f"INFO Alert: {formatted_message}")

# 사용 예제
if __name__ == "__main__":
    config = {
        'slack_webhook': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
        'email': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password',
            'from': 'fms-alerts@company.com'
        },
        'alert_recipients': ['admin@company.com', 'engineer@company.com']
    }
    
    alert_manager = AlertManager(config)
    
    # 테스트 알림
    test_alert = {
        'severity': 'CRITICAL',
        'message': 'Temperature sensor reading exceeded critical threshold (95°C)',
        'device_id': 'FMS-001'
    }
    
    alert_manager.process_alert(test_alert)