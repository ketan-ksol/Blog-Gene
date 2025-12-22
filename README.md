# Enterprise Blog Generator

An AI-powered blog generation system using an agentic workflow. This application creates high-quality, SEO-optimized blog posts through a multi-agent pipeline that handles planning, research, writing, editing, SEO optimization, and fact-checking.

## Features

### Agentic Workflow

1. **Planner Agent** - Creates blog structure, thesis, outline, and research queries
2. **Research Agent** - Gathers facts, statistics, and citations from web search and local sources
3. **Writer Agent** - Writes content section-by-section with proper tone and style
4. **Editor Agent** - Improves flow, clarity, and removes repetitions
5. **SEO Agent** - Optimizes for search engines (keywords, meta tags, FAQs, internal links)
6. **Fact-check & Safety Agent** - Validates claims, adds citations, and includes disclaimers

## Installation

1. Clone or download this repository

2. Create and activate a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here  # Optional, for web search
MODEL_NAME=gpt-4o  # Recommended: gpt-4o (latest, fastest, most capable)
TEMPERATURE=0.7
```

**Model Options:**
- `gpt-4o` (Recommended) - Latest model, fastest, most capable, best for quality content
- `gpt-4-turbo` - High quality, good for complex tasks
- `gpt-4` - Original, slower but very capable
- `gpt-3.5-turbo` - Faster, lower cost, good for simple tasks

## Usage

### Command Line Interface

Basic usage:
```bash
python main.py "Your blog topic here"
```

With SEO keywords:
```bash
python main.py "Cloud Computing Best Practices" --keywords cloud computing enterprise security scalability
```

With custom tone and word count:
```bash
python main.py "AI in Healthcare" --tone professional --word-count 2500
```

With custom configuration file:
```bash
python main.py "Topic" --config custom_config.yaml
```

### Python API

```python
from blog_generator import BlogGenerator

# Initialize generator
generator = BlogGenerator()

# Generate blog
result = generator.generate(
    topic="Enterprise AI Adoption",
    target_keywords=["AI", "enterprise", "automation"],
    custom_config={
        "tone": "professional",
        "word_count": 2000
    }
)

if result["status"] == "success":
    print(f"Blog saved to: {result['output_file']}")
    print(f"Word count: {result['metadata']['word_count']}")
```

## Configuration

Edit `config.yaml` to customize default settings:

```yaml
tone: "professional"
reading_level: "college"
target_audience: "enterprise professionals"
min_word_count: 1500
max_word_count: 3000
include_faq: true
include_meta_tags: true
require_citations: true
add_disclaimers: false
disclaimer_types: []  # e.g., ["medical", "legal", "financial"]
```

## Project Structure

```
blog_generator/
├── agents/
│   ├── __init__.py
│   ├── base.py           # Base agent class
│   ├── planner.py        # Planning agent
│   ├── research.py       # Research agent
│   ├── writer.py         # Writing agent
│   ├── editor.py         # Editing agent
│   ├── seo.py            # SEO agent
│   └── fact_check.py     # Fact-checking agent
├── blog_generator.py     # Main orchestration
├── main.py              # CLI interface
├── config.yaml          # Configuration file
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Output

Generated blogs are saved in the `output/` directory (configurable via `OUTPUT_DIR` environment variable) with:
- Markdown file (`.md`) - Formatted blog post
- JSON file (`.json`) - Complete metadata and structured data

## Local Sources

You can provide local research sources by placing text files in a `sources/` directory (configurable via `SOURCES_DIR` environment variable). The Research Agent will automatically include these in its research.

## Requirements

- Python 3.8+
- OpenAI API key (required)
- Tavily API key (optional, for web search)

## Agent Details

### Planner Agent
- Creates structured outline with sections and subsections
- Defines thesis and unique angle
- Generates research queries
- Identifies required facts and data points

### Research Agent
- Performs web searches (via Tavily API)
- Loads local source files
- Matches facts to sources
- Creates citation database

### Writer Agent
- Writes introduction, sections, and conclusion
- Incorporates research and citations naturally
- Maintains consistent tone and reading level
- Follows outline structure

### Editor Agent
- Improves flow and transitions
- Enhances clarity and readability
- Removes repetitive content
- Applies style guide requirements

### SEO Agent
- Optimizes headings (H1/H2/H3)
- Places keywords naturally
- Generates meta title and description
- Creates FAQ section
- Suggests internal linking opportunities

### Fact-check & Safety Agent
- Identifies factual claims
- Verifies against sources
- Adds citation markers
- Generates appropriate disclaimers

## License

This project is provided as-is for enterprise use.

## Support

For issues or questions, please review the code documentation or create an issue in your repository.



