import os
import requests
from typing import Any, Dict, Optional
from pydantic import BaseModel, ValidationError
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MistralAPIError(Exception):
    """Custom exception for Mistral API errors"""
    pass

class APIResponseModel(BaseModel):
    """Pydantic model for validating API responses"""
    # Define expected fields based on Mistral API documentation
    # This is a basic example - adjust according to actual API response structure
    id: str
    object: str
    created: int
    model: str
    choices: list
    usage: Dict[str, int]

class MistralAPI:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.mistral.ai/v1"):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided and MISTRAL_API_KEY environment variable not set")

        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _make_request(self, method: str, endpoint: str, max_retries: int = 3, **kwargs) -> Any:
        """Make API request with retries and error handling"""
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)

                # Check for successful response
                if 200 <= response.status_code < 300:
                    try:
                        # Validate response with Pydantic
                        return APIResponseModel(**response.json())
                    except ValidationError as e:
                        logger.error(f"Response validation failed: {e}")
                        raise MistralAPIError(f"Invalid API response format: {e}")

                # Handle API errors
                self._handle_api_error(response)

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise MistralAPIError(f"Request failed after {max_retries} attempts: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def _handle_api_error(self, response: requests.Response) -> None:
        """Handle API error responses"""
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", str(error_data))
        except ValueError:
            error_msg = response.text

        logger.error(f"API Error {response.status_code}: {error_msg}")
        raise MistralAPIError(f"API Error {response.status_code}: {error_msg}")

    def chat_completion(self, messages: list, model: str = "mistral-medium-latest", response_format: Optional[dict] = None) -> Dict[str, Any]:
        """Create chat completion with JSON mode support"""
        endpoint = "chat/completions"
        data = {
            "model": model,
            "messages": messages,
            "response_format": response_format or {"type": "json_object"}
        }

        return self._make_request("POST", endpoint, json=data)

    def detect_tool_invocation(self, response: Dict[str, Any]) -> bool:
        """Detect if the response indicates a tool invocation is needed"""
        # Basic implementation - adjust based on actual tool invocation format
        # This is a placeholder and should be customized
        choices = response.get("choices", [])
        if not choices:
            return False

        # Check if any choice indicates tool use
        for choice in choices:
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                return True

        return False