"""
Configuration and environment variable loader
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from utils.logger import get_logger

logger = get_logger("config_loader")

class APIConfig(BaseModel):
    """API Configuration"""
    api_key: str
    endpoint: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

class WorkflowConfig(BaseModel):
    """Main Workflow Configuration"""
    max_leads_per_run: int = Field(default=100)
    enable_mock_mode: bool = Field(default=True)
    dry_run: bool = Field(default=False)
    log_level: str = Field(default="INFO")

class ConfigLoader:
    """Load and manage configuration from .env and YAML files"""
    
    def __init__(self, env_file: str = ".env", config_file: str = "config.yaml"):
        self.env_file = Path(env_file)
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        
        # Load environment variables
        self._load_env()
        
        # Load YAML config if exists
        if self.config_file.exists():
            self._load_yaml()
        else:
            logger.warning(f"Config file {config_file} not found, using defaults")
    
    def _load_env(self):
        """Load environment variables from .env file"""
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(f"Loaded environment variables from {self.env_file}")
        else:
            logger.warning(f"  .env file not found at {self.env_file}")
    
    def _load_yaml(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f" Failed to load config file: {e}")
            self.config = {}
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """Get environment variable"""
        value = os.getenv(key, default)
        if value is None:
            logger.warning(f"  Environment variable {key} not found")
        return value
    
    def get_api_config(self, service: str) -> Dict[str, Any]:
        """Get API configuration for a service"""
        api_key_map = {
            "gemini": "GEMINI_API_KEY",
            "clay": "CLAY_API_KEY",
            "apollo": "APOLLO_API_KEY",
            "clearbit": "CLEARBIT_API_KEY",
            "sendgrid": "SENDGRID_API_KEY",
        }
        
        api_key = self.get_env(api_key_map.get(service.lower()))
        
        if not api_key:
            logger.warning(f" API key for {service} not found")
            return {"api_key": "", "mock_mode": True}
        
        return {
            "api_key": api_key,
            "mock_mode": self.get_env("ENABLE_MOCK_MODE", "true").lower() == "true"
        }
    
    def get_workflow_config(self) -> WorkflowConfig:
        """Get workflow configuration"""
        return WorkflowConfig(
            max_leads_per_run=int(self.get_env("MAX_LEADS_PER_RUN", 100)),
            enable_mock_mode=self.get_env("ENABLE_MOCK_MODE", "true").lower() == "true",
            dry_run=self.get_env("DRY_RUN", "false").lower() == "true",
            log_level=self.get_env("LOG_LEVEL", "INFO")
        )
    
    def get_yaml_config(self, key: str, default: Any = None) -> Any:
        """Get value from YAML config"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.warning(f"  Config key {key} not found, using default")
            return default
    
    def get_icp_config(self) -> Dict[str, Any]:
        """Get Ideal Customer Profile configuration"""
        return self.get_yaml_config('icp', {
            "industry": ["SaaS", "Technology"],
            "location": ["USA"],
            "employee_count": {"min": 100, "max": 1000},
            "revenue": {"min": 20000000, "max": 200000000}
        })
    
    def get_scoring_config(self) -> Dict[str, Any]:
        """Get scoring criteria configuration"""
        return self.get_yaml_config('scoring', {
            "weights": {
                "industry_match": 0.3,
                "company_size": 0.2,
                "revenue_range": 0.2,
                "growth_signals": 0.3
            },
            "min_score_threshold": 0.6
        })


# Global config instance
_config_instance = None

def get_config() -> ConfigLoader:
    """Get global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance