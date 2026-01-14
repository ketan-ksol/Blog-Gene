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

Edit `.env` and add your API keys (credentials only):
```
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here  # Optional, for web search
```

**Note**: Configuration (model, temperature, word count, etc.) is managed through the Admin panel in the web interface, not via environment variables.

**Image Sources:**
- The system automatically extracts image URLs from research citations when available
- Uses Wikimedia Commons API for technical diagrams (open license, no API key required)
- Falls back to descriptive placeholder images if no suitable images are found
- All image URLs are included in the JSON output for easy access

**Model Options** (configured in Admin panel):
- `gpt-5` (Default) - Latest generation, most advanced and capable model
- `gpt-4o` - Latest, fastest, most capable model
- `gpt-4-turbo` - High quality, good for complex tasks
- `gpt-4` - Original, slower but very capable
- `gpt-3.5-turbo` - Faster, lower cost, good for simple tasks

## Usage

### Web Interface

Start the Streamlit web application:

```bash
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501` and use the interactive interface to generate blogs.

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

All configuration is managed through the **Admin panel** in the web interface and stored in the database. This provides a single source of truth for all settings.

### System Settings (Admin Panel)
- **Model Settings**: Choose OpenAI model (gpt-5, gpt-4o, etc.) and temperature
- **Agent Settings**: Configure web search, research sources, and word count limits
- **User Management**: Manage user accounts and roles

### Blog Settings (Sidebar)
- **Content Settings**: Tone and reading level/target audience
- **SEO Settings**: Keywords, FAQ inclusion, meta tags

**Note**: Configuration is stored in the database, not in files. Use the Admin panel to change system-wide settings.

## Project Structure

```
blog_generator/
├── agents/              # Agent modules
│   ├── __init__.py
│   ├── base.py           # Base agent class
│   ├── planner.py        # Planning agent
│   ├── research.py       # Research agent
│   ├── writer.py         # Writing agent
│   ├── editor.py         # Editing agent
│   ├── seo.py            # SEO agent
│   ├── fact_check.py     # Fact-checking agent
│   └── humanizer.py      # Humanization agent
├── tests/                # Test files
│   ├── __init__.py
│   └── test_connection.py
├── scripts/              # Utility scripts
│   ├── __init__.py
│   ├── init_database.py
│   └── check_docker_env.py
├── data/                 # Data directory (database)
├── output/               # Generated blog outputs
├── pages/                # Streamlit pages
├── sources/              # Local research sources
├── blog_generator.py     # Main orchestration
├── streamlit_app.py     # Web interface
├── database.py          # Database management
├── admin.py             # Admin panel
├── auth.py              # Authentication
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
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

## Docker Setup

This section explains how to run the Blog Generator using Docker.

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

### Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   cd blog_generator
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file** and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_actual_api_key_here
   ```

4. **Build and start the application**:
   ```bash
   docker-compose up -d
   ```

5. **Access the application**:
   - Open your browser and go to: `http://localhost:8501`
   - Login with default credentials:
     - **Admin**: `admin` / `admin123`
     - **User**: `user` / `user123`

### Default Credentials

⚠️ **IMPORTANT**: Change these default passwords in production!

- **Admin User**: 
  - Username: `admin`
  - Password: `admin123`
  - Can access: Admin panel + Blog Generator

- **Regular User**:
  - Username: `user`
  - Password: `user123`
  - Can access: Blog Generator only

### Docker Commands

**Start the application:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f app
```

**Stop the application:**
```bash
docker-compose down
```

**Rebuild after code changes:**
```bash
docker-compose up -d --build
```

**Access container shell:**
```bash
docker-compose exec app bash
```

### Data Persistence

The following data is persisted using Docker volumes:

- **Database**: `./data/blog_generator.db` - SQLite database file (contains all configuration)
- **Output**: `./output/` - Generated blog files

### Docker Environment Variables

Environment variables are only for **credentials and infrastructure settings**:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `TAVILY_API_KEY`: Your Tavily API key (optional, for web search)
- `SSL_VERIFY`: SSL verification (default: `true`)
- `OUTPUT_DIR`: Output directory (default: `./output`)
- `DB_PATH`: Database file path (default: `./data/blog_generator.db`)

**Note**: All configuration (model, temperature, word count, etc.) is managed through the **Admin panel** in the web interface and stored in the database. This provides a single source of truth for all settings.

### Docker Troubleshooting

**Port already in use:**
If port 8501 is already in use, change it in `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Use 8502 instead
```

**Database permissions:**
If you get database permission errors, ensure the database file is writable:
```bash
chmod 666 blog_generator.db
```

**View application logs:**
```bash
docker-compose logs -f app
```

### Production Deployment

For production deployment:

1. **Change default passwords** - Update default user passwords in the database
2. **Use environment variables** - Don't commit `.env` file
3. **Use HTTPS** - Set up reverse proxy (nginx/traefik) with SSL
4. **Backup database** - Regularly backup `blog_generator.db`
5. **Monitor logs** - Set up log aggregation
6. **Resource limits** - Add resource limits in `docker-compose.yml`

### Using PostgreSQL (Optional)

To use PostgreSQL instead of SQLite, uncomment the PostgreSQL service in `docker-compose.yml` and update the database connection in the code.

## Support

For issues or questions, please review the code documentation or create an issue in your repository.

