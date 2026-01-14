"""Base agent class for all blog generation agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Global callback for capturing AI thoughts
_thought_callback: Optional[Callable[[str, str], None]] = None

def set_thought_callback(callback: Optional[Callable[[str, str], None]]):
    """Set a global callback function to capture AI thoughts.
    
    Args:
        callback: Function that takes (agent_name, thought) as parameters
    """
    global _thought_callback
    _thought_callback = callback


class BaseAgent(ABC):
    """Base class for all agents in the blog generation pipeline."""
    
    def __init__(self, model_name: Optional[str] = None, temperature: Optional[float] = None):
        """Initialize the base agent with LLM configuration."""
        # Model settings should always be provided by BlogGenerator (which reads from database)
        # Fallback to database lookup only if not provided (for backward compatibility)
        if model_name is None:
            try:
                from database import get_database
                db = get_database()
                model_name = db.get_system_setting("model_name", "gpt-5")
            except:
                model_name = "gpt-5"  # Ultimate fallback
        if temperature is None:
            try:
                from database import get_database
                db = get_database()
                temperature = db.get_system_setting("temperature", 0.7)
            except:
                temperature = 0.7  # Ultimate fallback
        
        self.model_name = model_name
        self.temperature = temperature
        api_key = os.getenv("OPENAI_API_KEY")
        self.agent_name = self.__class__.__name__.replace("Agent", "")
        
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please set it in your .env file or environment."
            )
        
        if not api_key.startswith("sk-"):
            raise ValueError(
                "Invalid OpenAI API key format. API keys should start with 'sk-'. "
                "Please check your .env file."
            )
        
        # Configure LLM with extended timeout and retry settings
        llm_kwargs = {
            "model": self.model_name,
            "temperature": self.temperature,
            "api_key": api_key,
            "timeout": 120,  # 120 second timeout for slow connections
            "max_retries": 3,  # LangChain built-in retries
        }
        
        # Add base URL if specified (for proxy or custom endpoints)
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            llm_kwargs["base_url"] = base_url
        
        # Handle SSL certificate verification
        # If behind a proxy with self-signed certificates, disable verification
        # WARNING: This reduces security - only use if necessary
        ssl_verify = os.getenv("SSL_VERIFY", "true").lower()
        if ssl_verify == "false":
            import httpx
            import urllib3
            # Disable SSL warnings when verification is disabled
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Create a custom HTTP client with SSL verification disabled
            custom_client = httpx.Client(
                verify=False,
                timeout=120
            )
            llm_kwargs["http_client"] = custom_client
            print("⚠️  WARNING: SSL certificate verification is disabled. This reduces security.")
        
        self.llm = ChatOpenAI(**llm_kwargs)
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results."""
        pass
    
    def create_prompt(self, template: str, **kwargs):
        """Create a prompt template (placeholder for future use)."""
        # Can be implemented with langchain_core.prompts if needed
        return template
    
    def call_llm(self, prompt: str, system_message: Optional[str] = None, capture_thoughts: bool = False) -> str:
        """Call the LLM with a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            system_message: Optional system message
            capture_thoughts: If True, capture AI reasoning/thoughts (default: False, agents provide explicit thoughts)
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        import time
        
        # Note: Automatic thought capture is disabled by default.
        # Agents should provide explicit, user-friendly thoughts in their process() methods.
        # This prevents showing raw prompt text to users.
        
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        # Retry logic for connection errors
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                return response.content
            except Exception as e:
                error_msg = str(e).lower()
                error_type = type(e).__name__
                
                # Check for SSL certificate errors
                if "ssl" in error_msg or "certificate" in error_msg or "certificate_verify_failed" in error_msg:
                    raise ConnectionError(
                        f"SSL Certificate verification failed. This usually happens when behind a corporate proxy/VPN.\n\n"
                        f"To fix this, add to your .env file:\n"
                        f"  SSL_VERIFY=false\n\n"
                        f"⚠️  WARNING: Disabling SSL verification reduces security. Only use if necessary.\n\n"
                        f"Original error: {str(e)}"
                    )
                
                # Check for specific error types
                if "connection" in error_msg or "timeout" in error_msg or "network" in error_msg or "connect" in error_msg or "ConnectError" in error_type:
                    if attempt < max_retries - 1:
                        print(f"⚠️  Connection error (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        raise ConnectionError(
                            f"Failed to connect to OpenAI API after {max_retries} attempts.\n"
                            f"Possible causes:\n"
                            f"  • Internet connection issue\n"
                            f"  • Firewall or proxy blocking the connection\n"
                            f"  • OpenAI API service is temporarily unavailable\n"
                            f"  • Network timeout (try increasing timeout in .env)\n\n"
                            f"Original error: {str(e)}\n\n"
                            f"Troubleshooting:\n"
                            f"  1. Check your internet connection\n"
                            f"  2. Try running: python test_connection.py\n"
                            f"  3. Check OpenAI status: https://status.openai.com\n"
                            f"  4. If behind a proxy, set OPENAI_BASE_URL in .env"
                        )
                elif "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
                    raise ValueError(
                        f"Invalid OpenAI API key. Please check your .env file and ensure OPENAI_API_KEY is set correctly. "
                        f"Error: {str(e)}"
                    )
                elif "rate limit" in error_msg or "quota" in error_msg:
                    raise RuntimeError(
                        f"OpenAI API rate limit or quota exceeded. Please wait and try again later. "
                        f"Error: {str(e)}"
                    )
                else:
                    # For other errors, raise immediately
                    raise RuntimeError(f"Error calling OpenAI API: {str(e)}")
        
        # Should not reach here, but just in case
        raise RuntimeError("Failed to call LLM after retries")

