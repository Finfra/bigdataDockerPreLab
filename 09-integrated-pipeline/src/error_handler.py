# modules/error_handler.py
import logging
from enum import Enum

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FMSErrorHandler:
    def __init__(self):
        self.logger = self.setup_logger()
        
    def setup_logger(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/fms/logs/pipeline.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('FMS-Pipeline')
    
    def handle_error(self, error, severity=ErrorSeverity.MEDIUM):
        error_map = {
            ErrorSeverity.LOW: self.logger.info,
            ErrorSeverity.MEDIUM: self.logger.warning,
            ErrorSeverity.HIGH: self.logger.error,
            ErrorSeverity.CRITICAL: self.logger.critical
        }
        
        error_map[severity](f"Error: {error}")
        
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.send_alert(error, severity)
    
    def send_alert(self, error, severity):
        # Slack/이메일 알림 전송
        pass