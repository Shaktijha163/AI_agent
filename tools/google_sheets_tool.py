"""
Google Sheets API Tool - Write recommendations for human approval
"""
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from utils.logger import get_logger
from utils.config_loader import get_config

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

logger = get_logger("google_sheets")

class GoogleSheetsTool:
    """Google Sheets API wrapper for recommendation tracking"""
    
    def __init__(self, credentials_file: Optional[str] = None, mock_mode: bool = False):
        self.credentials_file = credentials_file or get_config().get_env(
            "GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json"
        )
        self.sheet_id = get_config().get_env("GOOGLE_SHEET_ID", "")
        self.mock_mode = mock_mode or get_config().get_workflow_config().enable_mock_mode
        
        if not GSPREAD_AVAILABLE:
            logger.warning("  gspread library not installed, using mock mode")
            self.mock_mode = True
        
        if not self.mock_mode and GSPREAD_AVAILABLE:
            try:
                self._initialize_client()
            except Exception as e:
                logger.warning(f"  Failed to initialize Google Sheets: {e}, using mock mode")
                self.mock_mode = True
        else:
            self.client = None
            self.sheet = None
    
    def _initialize_client(self):
        """Initialize Google Sheets client"""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(
            self.credentials_file,
            scopes=scopes
        )
        
        self.client = gspread.authorize(creds)
        logger.info(" Google Sheets client initialized")
    
    def write_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        campaign_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Write recommendations to Google Sheet
        
        Args:
            recommendations: List of recommendation dicts
            campaign_id: Campaign identifier
            metrics: Campaign performance metrics
            
        Returns:
            Write status
        """
        if self.mock_mode:
            return self._mock_write_recommendations(recommendations, campaign_id, metrics)
        
        try:
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            
            # Prepare data rows
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            rows = []
            for rec in recommendations:
                row = [
                    timestamp,
                    campaign_id,
                    rec.get('category', ''),
                    rec.get('recommendation', ''),
                    rec.get('expected_impact', ''),
                    rec.get('priority', ''),
                    metrics.get('open_rate', 0),
                    metrics.get('reply_rate', 0),
                    'pending'  # approval_status
                ]
                rows.append(row)
            
            # Append rows
            sheet.append_rows(rows)
            
            logger.info(f" Wrote {len(recommendations)} recommendations to Google Sheets")
            
            return {
                "status": "success",
                "rows_written": len(recommendations),
                "sheet_id": self.sheet_id,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f" Failed to write to Google Sheets: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def get_approved_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations that have been approved"""
        if self.mock_mode:
            return self._mock_get_approved()
        
        try:
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            records = sheet.get_all_records()
            
            approved = [
                rec for rec in records
                if rec.get('approval_status', '').lower() == 'approved'
            ]
            
            logger.info(f" Retrieved {len(approved)} approved recommendations")
            return approved
            
        except Exception as e:
            logger.error(f" Failed to read from Google Sheets: {e}")
            return []
    
    def update_approval_status(
        self,
        campaign_id: str,
        recommendation_index: int,
        status: str
    ) -> Dict[str, Any]:
        """
        Update approval status of a recommendation
        
        Args:
            campaign_id: Campaign identifier
            recommendation_index: Row index of the recommendation
            status: New status (approved/rejected)
            
        Returns:
            Update status
        """
        if self.mock_mode:
            return self._mock_update_status(campaign_id, recommendation_index, status)
        
        try:
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            
            # Find the row with matching campaign_id
            # Note: This is a simple implementation; production would need better row tracking
            sheet.update_cell(recommendation_index, 9, status)  # Column 9 is approval_status
            
            logger.info(f" Updated approval status to '{status}' for recommendation {recommendation_index}")
            
            return {
                "status": "success",
                "campaign_id": campaign_id,
                "recommendation_index": recommendation_index,
                "new_status": status
            }
            
        except Exception as e:
            logger.error(f" Failed to update approval status: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def create_recommendations_sheet(self) -> Dict[str, Any]:
        """
        Create a new sheet with proper headers for recommendations
        
        Returns:
            Creation status
        """
        if self.mock_mode:
            logger.info("🎭 MOCK MODE: Would create recommendations sheet")
            return {"status": "success", "mock": True}
        
        try:
            # Try to open existing sheet or create new
            try:
                workbook = self.client.open("AI Agent Recommendations")
            except gspread.exceptions.SpreadsheetNotFound:
                workbook = self.client.create("AI Agent Recommendations")
            
            sheet = workbook.sheet1
            
            # Set headers
            headers = [
                "Timestamp",
                "Campaign ID",
                "Category",
                "Recommendation",
                "Expected Impact",
                "Priority",
                "Open Rate",
                "Reply Rate",
                "Approval Status"
            ]
            
            sheet.update('A1:I1', [headers])
            
            # Format headers (bold)
            sheet.format('A1:I1', {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
            
            logger.info(f" Created/updated recommendations sheet: {workbook.id}")
            
            return {
                "status": "success",
                "sheet_id": workbook.id,
                "sheet_url": workbook.url
            }
            
        except Exception as e:
            logger.error(f" Failed to create recommendations sheet: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _mock_write_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        campaign_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock writing to Google Sheets"""
        logger.info(f"🎭 MOCK MODE: Writing {len(recommendations)} recommendations to Google Sheets")
        logger.info(f"   Campaign: {campaign_id}")
        logger.info(f"   Metrics: Open Rate={metrics.get('open_rate', 0):.1%}, Reply Rate={metrics.get('reply_rate', 0):.1%}")
        
        for idx, rec in enumerate(recommendations, 1):
            logger.info(f"\n   Recommendation {idx}:")
            logger.info(f"   - Category: {rec.get('category')}")
            logger.info(f"   - Recommendation: {rec.get('recommendation')}")
            logger.info(f"   - Priority: {rec.get('priority')}")
        
        return {
            "status": "success",
            "rows_written": len(recommendations),
            "sheet_id": "mock_sheet_id",
            "timestamp": datetime.now().isoformat()
        }
    
    def _mock_get_approved(self) -> List[Dict[str, Any]]:
        """Mock reading approved recommendations"""
        logger.info(" MOCK MODE: Retrieving approved recommendations")
        
        # Return some mock approved recommendations
        return [
            {
                "timestamp": "2024-01-15 10:30:00",
                "campaign_id": "camp_20240115_103000",
                "category": "subject_line",
                "recommendation": "Use more specific value propositions in subject lines",
                "expected_impact": "15% increase in open rate",
                "priority": "high",
                "approval_status": "approved"
            },
            {
                "timestamp": "2024-01-15 10:30:00",
                "campaign_id": "camp_20240115_103000",
                "category": "icp_refinement",
                "recommendation": "Focus on companies with 200-500 employees",
                "expected_impact": "20% increase in qualified leads",
                "priority": "medium",
                "approval_status": "approved"
            }
        ]
    
    def _mock_update_status(
        self,
        campaign_id: str,
        recommendation_index: int,
        status: str
    ) -> Dict[str, Any]:
        """Mock updating approval status"""
        logger.info(f" MOCK MODE: Updating recommendation {recommendation_index} to '{status}'")
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "recommendation_index": recommendation_index,
            "new_status": status,
            "mock": True
        }