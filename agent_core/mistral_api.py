import os
import requests
from typing import Any, Dict, Optional
from pydantic import BaseModel, ValidationError
import time
import logging

# Load environment variables from .env file if it exists
from pathlib import Path
env_path = Path(__file__).parent.parent.parent / '.env'  # Go up to project root
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
else:
    # If dotenv is not available, try to import it
    try:
        from dotenv import load_dotenv
        load_dotenv()  # Try to load from current directory
    except ImportError:
        pass  # dotenv not installed, continue without it

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
            # For testing purposes, we'll allow the system to run without an API key
            # but with reduced functionality
            logger.warning("MISTRAL_API_KEY not set. Running in test mode without API access.")
            self.api_key = None
            self.session = None
            return

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

    def chat_completion(self, messages: list, model: str = "mistral-medium-latest", response_format: Optional[dict] = None, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Create chat completion with JSON mode support, optionally with image"""
        endpoint = "chat/completions"
        
        # If there's an image to include, modify the messages
        if image_path and os.path.exists(image_path):
            import base64
            from PIL import Image
            import io
            
            try:
                # Open and encode the image
                with Image.open(image_path) as img:
                    # Resize image if too large (to stay within API limits)
                    img = img.convert("RGB")  # Ensure RGB format
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=85)
                    img_bytes = buffer.getvalue()
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                # Modify the first message to include image
                if messages and len(messages) > 0:
                    # Add image to the first user message
                    content = messages[0].get('content', '')
                    messages[0]['content'] = [
                        {
                            "type": "text",
                            "text": content
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
            except Exception as e:
                logger.warning(f"Failed to process image for API: {e}")
                # Continue without the image if processing fails
                pass
        
        data = {
            "model": model,
            "messages": messages,
            "response_format": response_format or {"type": "json_object"}
        }

        result = self._make_request("POST", endpoint, json=data)
        
        # Handle both APIResponseModel objects and raw dictionaries
        if hasattr(result, 'dict') and callable(getattr(result, 'dict')):
            # It's an APIResponseModel object
            return result.dict()
        elif isinstance(result, dict):
            # It's already a dictionary
            return result
        else:
            # Fallback to JSON conversion
            return result

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

    def query(self, prompt: str, image_path: Optional[str] = None) -> str:
        """
        Query the Mistral API with a text prompt and optional image

        Args:
            prompt (str): The text prompt to send to Mistral
            image_path (str, optional): Path to image to include with the prompt

        Returns:
            str: The response text from Mistral
        """
        # If no API key is set, return a default response for testing
        if not self.api_key:
            logger.warning("Running in test mode - returning default response")
            return '{"action": "move", "direction": "up", "reason": "Test mode - moving up"}'
        
        try:
            # Convert prompt to chat format
            messages = [{"role": "user", "content": prompt}]

            # Use chat completion with JSON response format for structured output
            response = self.chat_completion(
                messages=messages,
                model="mistral-medium-latest",
                response_format={"type": "json_object"},
                image_path=image_path
            )

            # Extract the response text
            choices = response.get("choices", [])
            if not choices:
                logger.error("No choices returned in API response")
                return '{"error": "No response generated"}'

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if not content:
                logger.error("Empty content in API response")
                return '{"error": "Empty response from API"}'

            # Log successful response
            logger.info(f"Mistral API query successful, response length: {len(content)} characters")

            return content

        except MistralAPIError as e:
            logger.error(f"Mistral API error: {e}")
            return f'{{"error": "Mistral API error: {str(e)}"}}'
        except Exception as e:
            logger.error(f"Unexpected error in Mistral query: {e}")
            return f'{{"error": "Unexpected error: {str(e)}"}}'