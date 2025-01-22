import os
import requests
import logging
from typing import Dict
from dotenv import load_dotenv
from typing import Dict
from firecrawl_tool.schemas import InputSchema
from naptha_sdk.schemas import ToolDeployment, ToolRunInput
from naptha_sdk.user import sign_consumer_id

logger = logging.getLogger(__name__)
load_dotenv()

class FirecrawlTool:
    def __init__(self, tool_deployment: ToolDeployment):
        self.tool_deployment = tool_deployment
        self.api_key = os.environ.get('FIRECRAWL_API_KEY')
        self.api_base = "https://api.firecrawl.dev/v1"
        
        if not self.api_key:
            raise ValueError("Firecrawl API key not set")

    def scrape_website(self, inputs: InputSchema):
        logger.info(f"Scraping website: {inputs.tool_input_data}")
        
        url = f"{self.api_base}/scrape"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "url": inputs.tool_input_data,
            "formats": ["markdown"]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["data"]["markdown"]
        except Exception as e:
            logger.error(f"Failed to scrape website: {str(e)}")
            raise ValueError(f"Failed to scrape website: {str(e)}")
        
    def extract_data(self, inputs: InputSchema) -> str:
        logger.info(f"Extracting data from: {inputs.tool_input_data}")
        
        if not inputs.query:
            raise ValueError("Query is required for extraction")

        url = f"{self.api_base}/scrape"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "url": inputs.tool_input_data,
            "formats": ["extract"],
            "extract": {
                "prompt": inputs.query
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["data"]["extract"]
        except Exception as e:
            logger.error(f"Failed to extract data: {str(e)}")
            raise ValueError(f"Failed to extract data: {str(e)}")

def run(module_run: Dict, *args, **kwargs):
    """Run the module to scrape or extract data from a website using Firecrawl API"""
    module_run = ToolRunInput(**module_run)
    module_run.inputs = InputSchema(**module_run.inputs)
    
    scraper_or_extractor = FirecrawlTool(module_run.deployment)
    method = getattr(scraper_or_extractor, module_run.inputs.tool_name, None)
    
    if not method:
        raise ValueError(f"Method {module_run.inputs.tool_name} not found")
    
    return method(module_run.inputs)

if __name__ == "__main__":
    import asyncio
    from naptha_sdk.client.naptha import Naptha
    from naptha_sdk.configs import setup_module_deployment
    
    naptha = Naptha()
    deployment = asyncio.run(setup_module_deployment(
        "tool", 
        "firecrawl_tool/configs/deployment.json",
        node_url=os.getenv("NODE_URL")
    ))

    # Example usage for scraping
    input_params = {
        "tool_name": "scrape_website",
        "tool_input_data": "https://naptha.ai/"
    }

    # Example usage for extraction
    # input_params = {
    #     "tool_name": "extract_data",
    #     "tool_input_data": "https://naptha.ai/",
    #     "query": "Extract the company mission from the page."
    # }
    
    # For scraping
    #naptha run tool:firecrawl_tool -p "tool_name='scrape_website', tool_input_data='https://naptha.ai/'"

    # For extraction
    #naptha run tool:firecrawl_tool -p "tool_name='extract_data', tool_input_data='https://naptha.ai/', query='Extract the company mission from the page.'"
    module_run = {
        "inputs": input_params,
        "deployment": deployment,
        "consumer_id": naptha.user.id,
        "signature": sign_consumer_id(naptha.user.id, os.getenv("PRIVATE_KEY"))
    }
    
    print(run(module_run))