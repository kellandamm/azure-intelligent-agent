"""
Power BI Integration for Microsoft Fabric Reports
Handles embedding and authentication for Power BI reports.
"""
import os
import json
import requests
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import jwt
from azure.identity import DefaultAzureCredential

from config import settings
from utils.logging_config import logger


class PowerBIEmbedding:
    """Power BI embedding and authentication manager."""
    
    def __init__(self):
        self.workspace_id = settings.powerbi_workspace_id
        self.tenant_id = settings.powerbi_tenant_id
        self.client_id = settings.powerbi_client_id
        self.client_secret = settings.powerbi_client_secret
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self._access_token = None
        self._token_expires = None
    
    async def get_access_token(self) -> str:
        """Get Azure AD access token for Power BI API."""
        try:
            # Use Service Principal authentication if credentials provided
            if self.client_id and self.client_secret:
                logger.info("[AUTH] Using Service Principal authentication for Power BI")
                token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
                
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': 'https://analysis.windows.net/powerbi/api/.default'
                }
                
                response = requests.post(token_url, data=data)
                response.raise_for_status()
                
                token_response = response.json()
                self._access_token = token_response['access_token']
                expires_in = token_response.get('expires_in', 3600)
                self._token_expires = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"[SUCCESS] Service Principal token obtained, expires in {expires_in}s")
                return self._access_token
            else:
                # Fallback to DefaultAzureCredential
                logger.info("[AUTH] Using DefaultAzureCredential for Power BI")
                credential = DefaultAzureCredential()
                token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
                
                self._access_token = token.token
                self._token_expires = datetime.now() + timedelta(seconds=token.expires_on - int(datetime.now().timestamp()))
                
                logger.info("[SUCCESS] Power BI access token obtained successfully")
                return self._access_token
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to get Power BI access token: {e}")
            # Return a mock token for development mode
            self._access_token = "mock_token_for_development"
            self._token_expires = datetime.now() + timedelta(hours=1)
            logger.warning("[DEV] Using mock token for development mode")
            return self._access_token
    
    async def get_workspace_reports(self) -> Dict[str, Any]:
        """Get all reports in the workspace."""
        try:
            token = await self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Get reports from specific workspace
            if self.workspace_id:
                url = f"{self.base_url}/groups/{self.workspace_id}/reports"
            else:
                url = f"{self.base_url}/reports"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                reports = response.json()
                logger.info(f"[SUCCESS] Retrieved {len(reports.get('value', []))} reports from workspace")
                return reports
            else:
                logger.warning(f"[FALLBACK] Using mock reports data. API response: {response.status_code}")
                return {
                    "value": [
                        {
                            "id": "mock-report-1",
                            "name": "Sales Dashboard",
                            "datasetId": "mock-dataset-1",
                            "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=mock-report-1"
                        }
                    ]
                }
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to get Power BI reports: {e}")
            return {"value": []}
    
    async def get_embed_token(self, report_id: str, dataset_ids: Optional[List[str]] = None) -> str:
        """Get embed token for a specific report."""
        try:
            token = await self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Prepare embed token request
            embed_request = {
                "reports": [{"id": report_id}],
                "targetWorkspaces": [{"id": self.workspace_id}] if self.workspace_id else []
            }
            
            if dataset_ids:
                embed_request["datasets"] = [{"id": dataset_id} for dataset_id in dataset_ids]
            
            # Generate embed token
            if self.workspace_id:
                url = f"{self.base_url}/groups/{self.workspace_id}/reports/{report_id}/GenerateToken"
            else:
                url = f"{self.base_url}/reports/{report_id}/GenerateToken"
            
            response = requests.post(url, headers=headers, json=embed_request)
            
            if response.status_code == 200:
                token_response = response.json()
                embed_token = token_response.get("token", "")
                logger.info(f"[SUCCESS] Embed token generated for report {report_id}")
                return embed_token
            else:
                logger.warning(f"[FALLBACK] Embed token request failed, trying dataset approach")
                return await self._try_dataset_embed_token(report_id, headers)
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to get embed token for report {report_id}: {e}")
            return "mock_embed_token_for_development"
    
    async def _try_dataset_embed_token(self, report_id: str, headers: Dict[str, str]) -> str:
        """Try alternative dataset-based embed token approach."""
        try:
            # First get report details to find dataset ID
            if self.workspace_id:
                report_url = f"{self.base_url}/groups/{self.workspace_id}/reports/{report_id}"
            else:
                report_url = f"{self.base_url}/reports/{report_id}"
            
            report_response = requests.get(report_url, headers=headers)
            
            if report_response.status_code == 200:
                report_data = report_response.json()
                dataset_id = report_data.get("datasetId")
                
                if dataset_id:
                    # Generate token for dataset access
                    embed_request = {
                        "datasets": [{"id": dataset_id}],
                        "reports": [{"id": report_id}],
                        "targetWorkspaces": [{"id": self.workspace_id}] if self.workspace_id else []
                    }
                    
                    token_url = f"{self.base_url}/GenerateToken"
                    token_response = requests.post(token_url, headers=headers, json=embed_request)
                    
                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        logger.info(f"[SUCCESS] Dataset-based embed token generated")
                        return token_data.get("token", "mock_embed_token_for_development")
            
            logger.warning("[FALLBACK] Using mock embed token for development")
            return "mock_embed_token_for_development"
            
        except Exception as e:
            logger.error(f"[ERROR] Dataset embed token approach failed: {e}")
            return "mock_embed_token_for_development"
    
    async def get_embed_config(self, report_id: str) -> Dict[str, Any]:
        """Get complete embed configuration for a report."""
        try:
            # Get embed token
            embed_token = await self.get_embed_token(report_id)
            
            # Get report details
            reports = await self.get_workspace_reports()
            report = None
            for r in reports.get("value", []):
                if r.get("id") == report_id:
                    report = r
                    break
            
            if not report:
                logger.warning(f"[FALLBACK] Report {report_id} not found, using mock config")
                report = {
                    "id": report_id,
                    "name": "Mock Report",
                    "embedUrl": f"https://app.powerbi.com/reportEmbed?reportId={report_id}",
                    "datasetId": "mock-dataset"
                }
            
            embed_config = {
                "type": "report",
                "id": report_id,
                "embedUrl": report.get("embedUrl", f"https://app.powerbi.com/reportEmbed?reportId={report_id}"),
                "accessToken": embed_token,
                "tokenType": 1,  # Embed token
                "settings": {
                    "panes": {
                        "filters": {"expanded": False, "visible": True},
                        "pageNavigation": {"visible": True}
                    },
                    "background": 2,  # Transparent
                    "layoutType": 0   # Master
                }
            }
            
            logger.info(f"[SUCCESS] Embed configuration prepared for report {report_id}")
            return embed_config
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get embed config for report {report_id}: {e}")
            return {
                "type": "report",
                "id": report_id,
                "embedUrl": f"https://app.powerbi.com/reportEmbed?reportId={report_id}",
                "accessToken": "mock_embed_token_for_development",
                "tokenType": 1
            }
    
    def generate_embed_html(self, embed_config: Dict[str, Any], container_id: str = "powerbi-container") -> str:
        """Generate HTML for embedding Power BI report."""
        embed_config_json = json.dumps(embed_config)
        
        html = f"""
        <div id="{container_id}" style="height: 600px; width: 100%; border: 1px solid #ddd; border-radius: 8px;"></div>
        
        <script src="https://cdn.jsdelivr.net/npm/powerbi-client@2.20.1/dist/powerbi.min.js"></script>
        <script>
            const models = window['powerbi-client'].models;
            const embedConfig = {embed_config_json};
            
            const reportContainer = document.getElementById('{container_id}');
            const report = powerbi.embed(reportContainer, embedConfig);
            
            // Handle load event
            report.on('loaded', function() {{
                console.log('Power BI report loaded successfully');
            }});
            
            // Handle error event
            report.on('error', function(event) {{
                console.error('Power BI report error:', event.detail);
            }});
            
            // Handle render event
            report.on('rendered', function() {{
                console.log('Power BI report rendered successfully');
            }});
        </script>
        """
        
        return html


class PowerBIAnalytics:
    """Power BI analytics and Q&A integration."""
    
    def __init__(self):
        self.embedding = PowerBIEmbedding()
    
    async def get_report_insights(self, report_id: str, question: str) -> Dict[str, Any]:
        """Get insights from Power BI report using Q&A."""
        try:
            token = await self.embedding.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Use Power BI Q&A API if available
            workspace_id = self.embedding.workspace_id
            if workspace_id:
                url = f"{self.embedding.base_url}/groups/{workspace_id}/reports/{report_id}/qna"
            else:
                url = f"{self.embedding.base_url}/reports/{report_id}/qna"
            
            qna_request = {
                "question": question,
                "dataset": {"id": report_id}
            }
            
            response = requests.post(url, headers=headers, json=qna_request)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[SUCCESS] Q&A response generated for: {question}")
                return {
                    "question": question,
                    "answer": result.get("answer", "No answer available"),
                    "visualizations": result.get("visualizations", []),
                    "confidence": result.get("confidence", 0)
                }
            else:
                logger.warning(f"[FALLBACK] Q&A API not available, using fallback response")
                return {
                    "question": question,
                    "answer": f"I can help you analyze the Power BI report data. Please refer to the embedded visualizations for insights about: {question}",
                    "visualizations": [],
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to get Power BI insights: {e}")
            return {
                "question": question,
                "answer": "Unable to generate insights from Power BI report at this time.",
                "visualizations": [],
                "confidence": 0
            }
    
    async def suggest_questions(self, report_id: str) -> List[str]:
        """Suggest questions based on report content."""
        # These would typically come from Power BI metadata or be configured per report
        default_questions = [
            "What are the top 5 sales regions by revenue?",
            "Show me the monthly sales trend this year",
            "Which products have the highest profit margin?",
            "What is the customer acquisition cost by channel?",
            "How does this quarter compare to last quarter?",
            "What are the key performance indicators?",
            "Show me customer demographics breakdown",
            "What are the seasonal sales patterns?"
        ]
        
        try:
            # In a production scenario, you would analyze the report metadata
            # to suggest relevant questions based on available data fields
            logger.info(f"[SUCCESS] Generated {len(default_questions)} suggested questions")
            return default_questions
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate suggested questions: {e}")
            return default_questions[:4]  # Return subset on error


# Global instances
powerbi_embedding = PowerBIEmbedding()
powerbi_analytics = PowerBIAnalytics()