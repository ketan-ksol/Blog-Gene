"""Utility functions for blog generation."""
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values.
    
    Note: Configuration is now managed through the Admin panel and stored in the database.
    This function only provides fallback defaults.
    
    Returns:
        Dictionary with default configuration values
    """
    return {
        "tone": "professional",
        "reading_level": "business professional",
        "target_audience": "business professional",  # Same as reading_level
        "target_keywords": [],
        "include_faq": True,
        "include_meta_tags": True,
        "enable_web_search": True,
        "max_research_sources": 10
        # Note: fact-checking is always enabled, citations always required, disclaimers never added
    }


def clean_markdown_for_word_count(text: str) -> str:
    """Clean markdown text to count only actual words.
    
    Removes:
    - Markdown images: ![alt](url)
    - URLs (http/https)
    - Markdown links (keeps text): [text](url) -> text
    - HTML comments
    - Markdown code blocks
    - Inline code (keeps text): `code` -> code
    
    Args:
        text: Markdown text to clean
    
    Returns:
        Cleaned text with only words
    """
    # Remove markdown images: ![alt](url)
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    # Remove URLs (http/https)
    text = re.sub(r'https?://\S+', '', text)
    # Remove markdown links but keep the text: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # Remove markdown code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code but keep the text
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    return text


def sanitize_topic(topic: str, max_length: int = 50) -> str:
    """Sanitize topic name for use in filenames.
    
    Args:
        topic: Topic string to sanitize
        max_length: Maximum length of sanitized topic
    
    Returns:
        Sanitized topic string safe for filenames
    """
    safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in topic)
    safe_topic = safe_topic.replace(' ', '_')[:max_length]
    return safe_topic


def extract_images_from_markdown(content: str) -> List[Dict[str, str]]:
    """Extract image URLs and descriptions from markdown content.
    
    Args:
        content: Markdown content string
    
    Returns:
        List of image dictionaries with 'url' or 'description' and 'type' keys
    """
    images = []
    
    # Extract image URLs from markdown image syntax: ![alt](url)
    for match in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", content):
        images.append({"url": match, "type": "url"})
    
    # Extract image descriptions from comments: <!-- Image needed: description -->
    for match in re.findall(r"<!-- Image needed: ([^>]+) -->", content):
        images.append({"description": match, "type": "description"})
    
    return images


def extract_json_from_markdown(text: str) -> Optional[str]:
    """Extract JSON from markdown code blocks.
    
    Args:
        text: Text that may contain JSON in markdown code blocks
    
    Returns:
        Extracted JSON string or None if not found
    """
    # Try to extract JSON from markdown code blocks
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    
    return None


def remove_duplicate_headers(content: str, section_title: str) -> str:
    """Remove duplicate headers from markdown content.
    
    Args:
        content: Markdown content
        section_title: Title of the section (to remove if duplicated)
    
    Returns:
        Content with duplicate headers removed
    """
    content_lines = content.split("\n")
    cleaned_content = []
    last_was_header = False
    
    for line in content_lines:
        # If this line is the same header as the section title, skip it
        if line.strip() == f"## {section_title}":
            continue
        # Remove consecutive duplicate headers
        if line.startswith("## "):
            if last_was_header:
                continue
            last_was_header = True
        else:
            last_was_header = False
        cleaned_content.append(line)
    
    return "\n".join(cleaned_content).strip()

