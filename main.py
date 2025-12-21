"""Command-line interface for blog generation."""
import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from blog_generator import BlogGenerator

console = Console()


def main():
    """Main entry point for the blog generator CLI."""
    parser = argparse.ArgumentParser(
        description="Enterprise Blog Generator - AI-powered blog creation with agentic workflow"
    )
    parser.add_argument(
        "topic",
        type=str,
        help="The main topic for the blog post"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        nargs="+",
        help="Target SEO keywords (space-separated)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom configuration YAML file"
    )
    parser.add_argument(
        "--tone",
        type=str,
        choices=["professional", "casual", "academic", "conversational"],
        help="Tone of the blog post"
    )
    parser.add_argument(
        "--word-count",
        type=int,
        help="Target word count"
    )
    
    args = parser.parse_args()
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]Enterprise Blog Generator[/bold blue]\n"
        "AI-powered blog creation with agentic workflow",
        border_style="blue"
    ))
    
    try:
        # Initialize generator
        generator = BlogGenerator(config_path=args.config)
        
        # Prepare custom config
        custom_config = {}
        if args.tone:
            custom_config["tone"] = args.tone
        if args.word_count:
            custom_config["max_word_count"] = args.word_count
        
        # Generate blog
        result = generator.generate(
            topic=args.topic,
            target_keywords=args.keywords,
            custom_config=custom_config if custom_config else None
        )
        
        if result.get("status") == "success":
            metadata = result.get("metadata", {})
            console.print("\n[bold green]✓ Blog generated successfully![/bold green]\n")
            console.print(f"[cyan]Topic:[/cyan] {metadata.get('topic', 'N/A')}")
            console.print(f"[cyan]Word Count:[/cyan] {metadata.get('word_count', 0)}")
            console.print(f"[cyan]Sections:[/cyan] {metadata.get('sections', 0)}")
            console.print(f"[cyan]Verification Score:[/cyan] {metadata.get('verification_score', 0):.2%}")
            console.print(f"[cyan]Output File:[/cyan] {result.get('output_file', 'N/A')}\n")
        else:
            console.print(f"\n[bold red]✗ Error:[/bold red] {result.get('message', 'Unknown error')}")
            console.print(f"[red]Failed at step:[/red] {result.get('step', 'unknown')}\n")
            sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation cancelled by user[/yellow]\n")
        sys.exit(1)
    except ValueError as e:
        # API key or configuration errors
        console.print(f"\n[bold red]✗ Configuration Error:[/bold red] {str(e)}\n")
        console.print("[yellow]Tip:[/yellow] Make sure your .env file exists and contains a valid OPENAI_API_KEY\n")
        sys.exit(1)
    except ConnectionError as e:
        # Connection errors
        console.print(f"\n[bold red]✗ Connection Error:[/bold red] {str(e)}\n")
        console.print("[yellow]Troubleshooting:[/yellow]")
        console.print("  1. Check your internet connection")
        console.print("  2. Verify your OpenAI API key is valid")
        console.print("  3. Check if OpenAI API is experiencing issues")
        console.print("  4. Try again in a few moments\n")
        sys.exit(1)
    except Exception as e:
        # Other errors
        error_type = type(e).__name__
        console.print(f"\n[bold red]✗ Fatal Error ({error_type}):[/bold red] {str(e)}\n")
        console.print("[yellow]If this persists, please check:[/yellow]")
        console.print("  - Your .env file configuration")
        console.print("  - Your OpenAI API key validity")
        console.print("  - Your internet connection\n")
        sys.exit(1)


if __name__ == "__main__":
    main()



