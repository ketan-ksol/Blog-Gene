"""Main blog generation orchestration system."""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from agents import (
    PlannerAgent,
    ResearchAgent,
    WriterAgent,
    EditorAgent,
    HumanizerAgent,
    SEOAgent,
    FactCheckAgent
)
from utils import (
    get_default_config,
    clean_markdown_for_word_count,
    sanitize_topic,
    extract_images_from_markdown,
    remove_duplicate_headers
)
from utils.logger import get_logger
from database import get_database

load_dotenv()

logger = get_logger(__name__)


class BlogGenerator:
    """Main orchestrator for the blog generation pipeline."""
    
    def __init__(self):
        """Initialize the blog generator with configuration from database."""
        # Get configuration from database (single source of truth)
        db = get_database()
        
        # Get defaults
        self.config = get_default_config()
        
        # Load system settings from database
        self.config["model_name"] = db.get_system_setting("model_name", "gpt-5")
        self.config["temperature"] = db.get_system_setting("temperature", 0.7)
        self.config["enable_web_search"] = db.get_system_setting("enable_web_search", True)
        self.config["max_research_sources"] = db.get_system_setting("max_research_sources", 10)
        self.config["min_word_count"] = db.get_system_setting("min_word_count", 500)
        self.config["max_word_count"] = db.get_system_setting("max_word_count", 1000)
        
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./output"))
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize agents with settings from database
        model_name = self.config["model_name"]
        temperature = self.config["temperature"]
        
        self.planner = PlannerAgent(model_name=model_name, temperature=temperature)
        self.research = ResearchAgent(model_name=model_name, temperature=temperature)
        self.writer = WriterAgent(model_name=model_name, temperature=temperature)
        self.editor = EditorAgent(model_name=model_name, temperature=temperature)
        self.humanizer = HumanizerAgent(model_name=model_name, temperature=temperature)
        self.seo = SEOAgent(model_name=model_name, temperature=temperature)
        self.fact_check = FactCheckAgent(model_name=model_name, temperature=temperature)
    
    def _run_agent_step(self, agent, step_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run an agent step with error handling.
        
        Args:
            agent: Agent instance to run
            step_name: Name of the step for error messages
            input_data: Input data for the agent
        
        Returns:
            Result dictionary with status and data, or error status
        """
        try:
            result = agent.process(input_data)
            if result.get("status") != "success":
                error_msg = result.get("message", "Unknown error")
                logger.error(f"{step_name.capitalize()} failed: {error_msg}")
                return {
                    "status": "error",
                    "message": f"{step_name.capitalize()} failed: {error_msg}",
                    "step": step_name
                }
            return result
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Exception in {step_name} step")
            if "Connection" in error_msg or "connection" in error_msg:
                return {
                    "status": "error",
                    "message": f"Connection error during {step_name}: {error_msg}. Please check your internet connection and OpenAI API key.",
                    "step": step_name
                }
            return {
                "status": "error",
                "message": f"{step_name.capitalize()} failed: {error_msg}",
                "step": step_name
            }
    
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
        logger.info(f"🚀 Starting blog generation for: {topic}")
        
        # Always reload system settings from database (single source of truth)
        db = get_database()
        system_settings = {
            "model_name": db.get_system_setting("model_name", "gpt-5"),
            "temperature": db.get_system_setting("temperature", 0.7),
            "enable_web_search": db.get_system_setting("enable_web_search", True),
            "max_research_sources": db.get_system_setting("max_research_sources", 10),
            "min_word_count": db.get_system_setting("min_word_count", 500),
            "max_word_count": db.get_system_setting("max_word_count", 1000),
        }
        
        # Merge custom config, but ensure system settings from DB are not overridden by None
        config = {**self.config}
        # First, ensure system settings are always from DB
        config.update(system_settings)
        # Then apply custom_config, but only non-None values to prevent None from overriding DB values
        if custom_config:
            for key, value in custom_config.items():
                if value is not None:
                    config[key] = value
            # Re-apply system settings after custom_config merge to ensure DB values are never None
            # This ensures that even if custom_config had None for a system setting, DB value is used
            for key in system_settings:
                if config.get(key) is None:
                    config[key] = system_settings[key]
        
        # Step 1: Planning
        logger.info("📋 Step 1/7: Planning blog structure...")
        plan_result = self._run_agent_step(
            agent=self.planner,
            step_name="planner",
            input_data={
                "topic": topic,
                "target_audience": config.get("target_audience") or config.get("reading_level", "business professional"),
                "tone": config.get("tone"),
                "word_count": config.get("max_word_count", 1000)
                # Note: sections_per_article removed - agent decides based on topic
            }
        )
        if plan_result.get("status") == "error":
            return plan_result
        
        plan = plan_result["plan"]
        logger.info(f"✓ Created outline with {len(plan.get('outline', []))} sections")
        
        # Step 2: Research
        logger.info("🔍 Step 2/7: Conducting research...")
        research_result = self.research.process({
            "search_queries": plan.get("search_queries", []),
            "required_facts": plan.get("required_facts", []),
            "topic": topic,
            "max_sources": config.get("max_research_sources", 10),
            "enable_web_search": config.get("enable_web_search", True)
        })
        
        if research_result.get("status") != "success":
            return {"status": "error", "message": "Research failed", "step": "research"}
        
        logger.info(f"✓ Found {research_result.get('sources_count', 0)} sources")
        
        # Step 3: Writing
        logger.info("✍️  Step 3/7: Writing content...")
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
        
        logger.info(f"✓ Wrote {writer_result.get('word_count', 0)} words across {writer_result.get('sections_written', 0)} sections")
        
        # Step 4: Editing
        logger.info("✏️  Step 4/7: Editing and refining...")
        editor_result = self.editor.process({
            "content": writer_result.get("content", {}),
            "tone": config.get("tone"),
            "reading_level": config.get("reading_level"),
            "style_guide": config.get("style_guide", {})
        })
        
        if editor_result.get("status") != "success":
            return {"status": "error", "message": "Editing failed", "step": "editor"}
        
        improvements = editor_result.get("improvements", [])
        logger.info(f"✓ Applied {len(improvements)} improvements: {', '.join(improvements)}")
        
        # Check if images were preserved after editing, restore if needed
        edited_content = editor_result.get("edited_content", {})
        has_images = any("![" in content or "Image needed:" in content for content in edited_content.values())
        if not has_images:
            # Re-add image descriptions if they were removed during editing
            logger.info("📷 Restoring image descriptions that may have been removed during editing...")
            from agents.writer import WriterAgent
            temp_writer = WriterAgent()
            edited_content = temp_writer._add_images_to_content(edited_content, topic, plan.get("outline", []))
            editor_result["edited_content"] = edited_content
        
        # Step 5: Humanize Content (Remove AI-generated patterns)
        logger.info("✍️  Step 5/7: Humanizing content (removing AI-generated patterns)...")
        humanizer_result = self.humanizer.process({
            "content": editor_result.get("edited_content", {}),
            "tone": config.get("tone"),
            "reading_level": config.get("reading_level")
        })
        
        if humanizer_result.get("status") != "success":
            return {"status": "error", "message": "Humanization failed", "step": "humanizer"}
        
        humanizer_improvements = humanizer_result.get("improvements", [])
        logger.info("✓ Humanization complete. Made content sound more natural and human-written.")
        
        # Step 6: SEO Optimization
        logger.info("🔎 Step 6/7: Optimizing for SEO...")
        seo_result = self.seo.process({
            "content": humanizer_result.get("humanized_content", {}),
            "topic": topic,
            "target_keywords": target_keywords or config.get("target_keywords", []),
            "include_faq": config.get("include_faq", True),
            "include_meta_tags": config.get("include_meta_tags", True)
        })
        
        if seo_result.get("status") != "success":
            return {"status": "error", "message": "SEO optimization failed", "step": "seo"}
        
        logger.info(f"✓ SEO optimization complete. Keyword density: {seo_result.get('keyword_density', {})}")
        
        # Step 7: Fact-checking & Safety (always enabled)
        logger.info("✅ Step 7/7: Fact-checking and safety review...")
        fact_check_result = self._run_agent_step(
            agent=self.fact_check,
            step_name="fact_check",
            input_data={
                "content": seo_result.get("optimized_content", {}),
                "fact_table": research_result.get("fact_table", {}),
                "citations": research_result.get("citations", []),
                "require_citations": True,  # Always require citations
                "add_disclaimers": False,  # Never add disclaimers
                "disclaimer_types": [],  # No disclaimers
                "topic": topic
            }
        )
        if fact_check_result.get("status") == "error":
            return fact_check_result
        
        verification_score = fact_check_result.get("verification_score", 0)
        logger.info(f"✓ Fact-checking complete. Verification score: {verification_score:.2%}")
        
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
        
        logger.info("🎉 Blog generation complete!")
        logger.info(f"📄 Output saved to: {output_file}")
        
        # Calculate word count excluding references and FAQ
        content_word_count = 0
        exclude_sections = ["References", "FAQ", "Disclaimer"]
        for section in final_blog.get("sections", []):
            section_title = section.get("title", "")
            section_content = section.get("content", "")
            # Skip References, FAQ, and Disclaimer sections from word count
            if section_title not in exclude_sections:
                cleaned_content = clean_markdown_for_word_count(section_content)
                words = [w.strip() for w in cleaned_content.split() if w.strip()]
                content_word_count += len(words)
        
        return {
            "status": "success",
            "blog": final_blog,
            "output_file": str(output_file),
            "metadata": {
                "topic": topic,
                "word_count": content_word_count,  # Excludes References, FAQ, and Disclaimer sections
                "sections": len(final_blog.get("sections", [])),  # Includes all sections: Introduction, main sections, Conclusion, FAQ, Disclaimer
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
        images = []
        for section in sections:
            content = section.get("content", "")
            images.extend(extract_images_from_markdown(content))
        
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
        safe_topic = sanitize_topic(topic)
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
            content = remove_duplicate_headers(content, title)
            
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

