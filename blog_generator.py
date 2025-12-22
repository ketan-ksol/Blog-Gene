"""Main blog generation orchestration system."""
import os
import json
import yaml
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from agents import (
    PlannerAgent,
    ResearchAgent,
    WriterAgent,
    EditorAgent,
    SEOAgent,
    FactCheckAgent
)

load_dotenv()


class BlogGenerator:
    """Main orchestrator for the blog generation pipeline."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the blog generator with configuration."""
        self.config = self._load_config(config_path)
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./output"))
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize agents
        model_name = os.getenv("MODEL_NAME", "gpt-4o")
        temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        self.planner = PlannerAgent(model_name=model_name, temperature=temperature)
        self.research = ResearchAgent(model_name=model_name, temperature=temperature)
        self.writer = WriterAgent(model_name=model_name, temperature=temperature)
        self.editor = EditorAgent(model_name=model_name, temperature=temperature)
        self.seo = SEOAgent(model_name=model_name, temperature=temperature)
        self.fact_check = FactCheckAgent(model_name=model_name, temperature=temperature)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = "config.yaml"
        
        default_config = {
            "tone": "professional",
            "reading_level": "college",
            "target_audience": "enterprise professionals",
            "min_word_count": 1500,
            "max_word_count": 3000,
            "sections_per_article": 5,
            "target_keywords": [],
            "include_faq": True,
            "include_meta_tags": True,
            "require_citations": True,
            "add_disclaimers": False,
            "disclaimer_types": [],
            "enable_web_search": True,
            "max_research_sources": 10,
            "fact_check_enabled": True
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    file_config = yaml.safe_load(f) or {}
                default_config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return default_config
    
    def generate(
        self,
        topic: str,
        target_keywords: Optional[list] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete blog post.
        
        Args:
            topic: The main topic for the blog post
            target_keywords: Optional list of SEO keywords
            custom_config: Optional custom configuration overrides
        
        Returns:
            Dictionary containing the generated blog and metadata
        """
        print(f"\n🚀 Starting blog generation for: {topic}\n")
        
        # Merge custom config
        config = {**self.config}
        if custom_config:
            config.update(custom_config)
        
        # Step 1: Planning
        print("📋 Step 1/6: Planning blog structure...")
        try:
            plan_result = self.planner.process({
                "topic": topic,
                "target_audience": config.get("target_audience"),
                "tone": config.get("tone"),
                "word_count": config.get("max_word_count", 2000)
            })
        except Exception as e:
            error_msg = str(e)
            if "Connection" in error_msg or "connection" in error_msg:
                return {
                    "status": "error",
                    "message": f"Connection error during planning: {error_msg}. Please check your internet connection and OpenAI API key.",
                    "step": "planner"
                }
            return {
                "status": "error",
                "message": f"Planning failed: {error_msg}",
                "step": "planner"
            }
        
        if plan_result.get("status") != "success":
            error_msg = plan_result.get("message", "Unknown error")
            return {
                "status": "error",
                "message": f"Planning failed: {error_msg}",
                "step": "planner"
            }
        
        plan = plan_result["plan"]
        print(f"✓ Created outline with {len(plan.get('outline', []))} sections\n")
        
        # Step 2: Research
        print("🔍 Step 2/6: Conducting research...")
        research_result = self.research.process({
            "search_queries": plan.get("search_queries", []),
            "required_facts": plan.get("required_facts", []),
            "topic": topic,
            "max_sources": config.get("max_research_sources", 10),
            "enable_web_search": config.get("enable_web_search", True)
        })
        
        if research_result.get("status") != "success":
            return {"status": "error", "message": "Research failed", "step": "research"}
        
        print(f"✓ Found {research_result.get('sources_count', 0)} sources\n")
        
        # Step 3: Writing
        print("✍️  Step 3/6: Writing content...")
        writer_result = self.writer.process({
            "outline": plan.get("outline", []),
            "thesis": plan.get("thesis", ""),
            "angle": plan.get("angle", ""),
            "fact_table": research_result.get("fact_table", {}),
            "citations": research_result.get("citations", []),
            "tone": config.get("tone"),
            "reading_level": config.get("reading_level"),
            "section_goals": plan.get("section_goals", {}),
            "topic": topic,
            "target_word_count": config.get("max_word_count", 1500),
            "min_word_count": config.get("min_word_count", 1000)
        })
        
        if writer_result.get("status") != "success":
            return {"status": "error", "message": "Writing failed", "step": "writer"}
        
        print(f"✓ Wrote {writer_result.get('word_count', 0)} words across {writer_result.get('sections_written', 0)} sections\n")
        
        # Step 4: Editing
        print("✏️  Step 4/6: Editing and refining...")
        editor_result = self.editor.process({
            "content": writer_result.get("content", {}),
            "tone": config.get("tone"),
            "reading_level": config.get("reading_level"),
            "style_guide": config.get("style_guide", {})
        })
        
        if editor_result.get("status") != "success":
            return {"status": "error", "message": "Editing failed", "step": "editor"}
        
        improvements = editor_result.get("improvements", [])
        print(f"✓ Applied {len(improvements)} improvements: {', '.join(improvements)}\n")
        
        # Check if images were preserved after editing, restore if needed
        edited_content = editor_result.get("edited_content", {})
        has_images = any("![" in content or "Image needed:" in content for content in edited_content.values())
        if not has_images:
            # Re-add images if they were removed during editing
            print("📷 Restoring images that may have been removed during editing...")
            from agents.writer import WriterAgent
            temp_writer = WriterAgent()
            citations = research_result.get("citations", [])
            edited_content = temp_writer._add_images_to_content(edited_content, topic, plan.get("outline", []), citations)
            editor_result["edited_content"] = edited_content
        
        # Step 5: SEO Optimization
        print("🔎 Step 5/6: Optimizing for SEO...")
        seo_result = self.seo.process({
            "content": editor_result.get("edited_content", {}),
            "topic": topic,
            "target_keywords": target_keywords or config.get("target_keywords", []),
            "include_faq": config.get("include_faq", True),
            "include_meta_tags": config.get("include_meta_tags", True)
        })
        
        if seo_result.get("status") != "success":
            return {"status": "error", "message": "SEO optimization failed", "step": "seo"}
        
        print(f"✓ SEO optimization complete. Keyword density: {seo_result.get('keyword_density', {})}\n")
        
        # Step 6: Fact-checking & Safety
        print("✅ Step 6/6: Fact-checking and safety review...")
        fact_check_result = self.fact_check.process({
            "content": seo_result.get("optimized_content", {}),
            "fact_table": research_result.get("fact_table", {}),
            "citations": research_result.get("citations", []),
            "require_citations": config.get("require_citations", True),
            "add_disclaimers": config.get("add_disclaimers", False),
            "disclaimer_types": config.get("disclaimer_types", []),
            "topic": topic
        })
        
        if fact_check_result.get("status") != "success":
            return {"status": "error", "message": "Fact-checking failed", "step": "fact_check"}
        
        verification_score = fact_check_result.get("verification_score", 0)
        print(f"✓ Fact-checking complete. Verification score: {verification_score:.2%}\n")
        
        # Compile final blog
        final_blog = self._compile_final_blog(
            content=fact_check_result.get("verified_content", {}),
            plan=plan,
            seo_data=seo_result,
            fact_check_data=fact_check_result,
            research_data=research_result
        )
        
        # Save blog
        output_file = self._save_blog(final_blog, topic)
        
        print(f"🎉 Blog generation complete!\n")
        print(f"📄 Output saved to: {output_file}\n")
        
        # Calculate word count excluding references and FAQ
        content_word_count = 0
        for section in final_blog.get("sections", []):
            section_title = section.get("title", "")
            section_content = section.get("content", "")
            # Skip References and FAQ sections from word count
            if section_title not in ["References", "FAQ"]:
                # Count words, excluding markdown syntax, URLs, and image links
                words = section_content.split()
                filtered_words = [w for w in words 
                                 if not w.startswith('#') 
                                 and not w.startswith('![') 
                                 and not w.startswith('http') 
                                 and not (w.startswith('[') and '](' in w)
                                 and not w.startswith('*')]
                content_word_count += len(filtered_words)
        
        return {
            "status": "success",
            "blog": final_blog,
            "output_file": str(output_file),
            "metadata": {
                "topic": topic,
                "word_count": content_word_count,  # Excludes references
                "sections": len(final_blog.get("sections", [])),
                "verification_score": verification_score,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def _compile_final_blog(
        self,
        content: Dict[str, str],
        plan: Dict[str, Any],
        seo_data: Dict[str, Any],
        fact_check_data: Dict[str, Any],
        research_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile all components into final blog structure."""
        # Combine all sections
        sections = []
        for section_title, section_content in content.items():
            sections.append({
                "title": section_title,
                "content": section_content
            })
        
        # Extract image URLs and descriptions from sections for easy access in JSON
        import re
        images = []
        for section in sections:
            content = section.get("content", "")
            # Extract image URLs from markdown image syntax
            for match in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", content):
                images.append({"url": match, "type": "url"})
            # Extract image descriptions from comments (when no URL found)
            for match in re.findall(r"<!-- Image needed: ([^>]+) -->", content):
                images.append({"description": match, "type": "description"})
        
        # Add FAQ if generated
        if seo_data.get("faq_section"):
            sections.append({
                "title": "FAQ",
                "content": seo_data["faq_section"]
            })
        
        # Add disclaimers if present
        if fact_check_data.get("disclaimers"):
            sections.append({
                "title": "Disclaimer",
                "content": fact_check_data["disclaimers"]
            })
        
        return {
            "title": seo_data.get("meta_title", "Blog Post"),
            "meta_description": seo_data.get("meta_description", ""),
            "thesis": plan.get("thesis", ""),
            "angle": plan.get("angle", ""),
            "sections": sections,
            "images": images,
            "seo": {
                "meta_title": seo_data.get("meta_title", ""),
                "meta_description": seo_data.get("meta_description", ""),
                "target_keywords": seo_data.get("target_keywords", []),
                "keyword_density": seo_data.get("keyword_density", {}),
                "internal_link_suggestions": seo_data.get("internal_link_suggestions", [])
            },
            "citations": research_data.get("citations", []),
            "fact_check": {
                "verification_score": fact_check_data.get("verification_score", 0),
                "flagged_claims": fact_check_data.get("flagged_claims", [])
            }
        }
    
    def _save_blog(self, blog: Dict[str, Any], topic: str) -> Path:
        """Save the blog to a markdown file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in topic)
        safe_topic = safe_topic.replace(' ', '_')[:50]
        filename = f"{safe_topic}_{timestamp}.md"
        filepath = self.output_dir / filename
        
        # Format as markdown
        markdown = self._format_as_markdown(blog)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        # Also save JSON metadata
        json_filepath = self.output_dir / f"{safe_topic}_{timestamp}.json"
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(blog, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _format_as_markdown(self, blog: Dict[str, Any]) -> str:
        """Format blog as markdown."""
        lines = []
        
        # Title
        lines.append(f"# {blog.get('title', 'Blog Post')}\n")
        
        # Meta description as subtitle
        if blog.get("meta_description"):
            lines.append(f"*{blog['meta_description']}*\n")
        
        # Sections (skip thesis/angle - those are planning metadata)
        for section in blog.get("sections", []):
            title = section.get("title", "")
            content = section.get("content", "").strip()
            
            # Skip empty sections
            if not content or content == "## " + title or len(content) < 10:
                continue
            
            # Skip planning metadata sections
            if title in ["Thesis", "Angle"]:
                continue
            
            # Remove duplicate headers from content
            content_lines = content.split("\n")
            cleaned_content = []
            last_was_header = False
            
            for line in content_lines:
                # If this line is the same header as the section title, skip it
                if line.strip() == f"## {title}":
                    continue
                # Remove consecutive duplicate headers
                if line.startswith("## "):
                    if last_was_header:
                        continue
                    last_was_header = True
                else:
                    last_was_header = False
                cleaned_content.append(line)
            
            content = "\n".join(cleaned_content).strip()
            
            # Only add section if it has content
            if content:
                lines.append(f"\n## {title}\n")
                lines.append(f"{content}\n")
        
        # Citations
        citations = blog.get("citations", [])
        if citations:
            lines.append("\n## References\n\n")
            for i, citation in enumerate(citations[:10], 1):  # Top 10 citations
                title = citation.get("title", "Unknown")
                url = citation.get("url", "")
                lines.append(f"{i}. [{title}]({url})\n")
        
        # SEO metadata (as comments)
        seo_data = blog.get("seo", {})
        if seo_data:
            lines.append("\n<!-- SEO Metadata -->\n")
            lines.append(f"<!-- Meta Title: {seo_data.get('meta_title', '')} -->\n")
            lines.append(f"<!-- Meta Description: {seo_data.get('meta_description', '')} -->\n")
            if seo_data.get("target_keywords"):
                lines.append(f"<!-- Keywords: {', '.join(seo_data['target_keywords'])} -->\n")
        
        return "\n".join(lines)

