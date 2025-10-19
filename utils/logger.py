"""
Centralized logging utility for AI Agent Workflow
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import colorlog
import os

class WorkflowLogger:
    """Custom logger with colored output and file logging"""
    
    def __init__(self, name: str = "workflow", log_level: str = None):
        self.name = name
        self.log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with both console and file handlers"""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Clear existing handlers
        logger.handlers = []
        
        # Console handler with colors
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        console_format = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        return logger
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)
    
    def log_api_call(self, service: str, endpoint: str, status: str, response_time: float = None):
        """Log API call with structured format"""
        msg = f"API Call | Service: {service} | Endpoint: {endpoint} | Status: {status}"
        if response_time:
            msg += f" | Response Time: {response_time:.2f}s"
        self.info(msg)
    
    def log_agent_start(self, agent_name: str, input_data: dict):
        """Log agent execution start"""
        self.info(f"Agent Started: {agent_name} | Input Keys: {list(input_data.keys())}")
    
    def log_agent_complete(self, agent_name: str, output_data: dict, execution_time: float):
        """Log agent execution completion"""
        self.info(f"Agent Completed: {agent_name} | Output Keys: {list(output_data.keys())} | Time: {execution_time:.2f}s")
    
    def log_agent_error(self, agent_name: str, error: Exception):
        """Log agent execution error"""
        self.error(f" Agent Failed: {agent_name} | Error: {str(error)}")


# Global logger instance
def get_logger(name: str = "workflow") -> WorkflowLogger:
    """Get or create logger instance"""
    return WorkflowLogger(name)