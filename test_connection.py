"""Test script to diagnose API connection issues."""
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

console = Console()
load_dotenv()

def test_connection():
    """Test OpenAI API connection."""
    console.print(Panel.fit(
        "[bold blue]OpenAI API Connection Test[/bold blue]",
        border_style="blue"
    ))
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("\n[bold red]✗ OPENAI_API_KEY not found[/bold red]")
        console.print("[yellow]Solution:[/yellow] Create a .env file with your API key")
        return False
    
    console.print(f"\n[green]✓[/green] API Key found (length: {len(api_key)})")
    
    if not api_key.startswith("sk-"):
        console.print("\n[bold red]✗ Invalid API key format[/bold red]")
        console.print("[yellow]Solution:[/yellow] API keys should start with 'sk-'")
        return False
    
    console.print("[green]✓[/green] API Key format valid")
    
    # Test API call
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        import httpx
        
        console.print("\n[cyan]Testing API connection...[/cyan]")
        
        # Check SSL verification setting
        ssl_verify = os.getenv("SSL_VERIFY", "true").lower()
        llm_kwargs = {
            "model": os.getenv("MODEL_NAME", "gpt-4o"),
            "api_key": api_key,
            "timeout": 30
        }
        
        if ssl_verify == "false":
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            custom_client = httpx.Client(verify=False, timeout=30)
            llm_kwargs["http_client"] = custom_client
            console.print("[yellow]⚠️  SSL verification disabled[/yellow]")
        
        llm = ChatOpenAI(**llm_kwargs)
        
        response = llm.invoke([HumanMessage(content="Say 'Hello' if you can hear me.")])
        
        console.print(f"[green]✓[/green] API connection successful!")
        console.print(f"[green]✓[/green] Response: {response.content[:50]}...")
        
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        console.print(f"\n[bold red]✗ Connection failed[/bold red]")
        console.print(f"[red]Error:[/red] {str(e)}")
        
        if "ssl" in error_msg or "certificate" in error_msg or "certificate_verify_failed" in error_msg:
            console.print("\n[bold yellow]SSL Certificate Error Detected[/bold yellow]")
            console.print("\n[yellow]Solution:[/yellow]")
            console.print("  Add this to your .env file:")
            console.print("  [cyan]SSL_VERIFY=false[/cyan]")
            console.print("\n[yellow]⚠️  Warning:[/yellow] This disables SSL verification and reduces security.")
            console.print("  Only use this if you're behind a corporate proxy/VPN with self-signed certificates.")
        elif "connection" in error_msg or "timeout" in error_msg or "ConnectError" in str(type(e).__name__):
            console.print("\n[yellow]Possible causes:[/yellow]")
            console.print("  • Internet connection issue")
            console.print("  • OpenAI API is down")
            console.print("  • Firewall blocking the connection")
            console.print("  • Network timeout")
            console.print("  • SSL certificate issue (try setting SSL_VERIFY=false in .env)")
        elif "api key" in error_msg or "authentication" in error_msg:
            console.print("\n[yellow]Possible causes:[/yellow]")
            console.print("  • Invalid API key")
            console.print("  • API key expired")
            console.print("  • API key doesn't have required permissions")
        elif "rate limit" in error_msg or "quota" in error_msg:
            console.print("\n[yellow]Possible causes:[/yellow]")
            console.print("  • API rate limit exceeded")
            console.print("  • Account quota exhausted")
            console.print("  • Billing issue")
        
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

