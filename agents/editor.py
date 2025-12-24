"""Editor Agent: Improves flow, clarity, and style."""
from typing import Dict, Any
from .base import BaseAgent


class EditorAgent(BaseAgent):
    """Agent responsible for editing and improving blog content."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edit and improve blog content.
        
        Input:
            - content: dict mapping section titles to content
            - tone: str
            - reading_level: str
            - style_guide: dict (optional)
        
        Output:
            - edited_content: dict
            - improvements: list of changes made
            - word_count: int
        """
        from agents.base import _thought_callback
        import time
        
        content = input_data.get("content", {})
        section_count = len(content) if isinstance(content, dict) else 0
        
        if _thought_callback:
            _thought_callback("Editor", f"Starting editing phase: Analyzing {section_count} sections for improvements...")
            time.sleep(0.3)
            _thought_callback("Editor", f"Improving flow and transitions between sections for better readability...")
            time.sleep(0.3)
            _thought_callback("Editor", f"Removing repetitions and enhancing clarity while preserving key information...")
        
        content = input_data.get("content", {})
        tone = input_data.get("tone", "professional")
        reading_level = input_data.get("reading_level", "college")
        style_guide = input_data.get("style_guide", {})
        
        edited_content = {}
        improvements = []
        
        # Combine all content for full-article editing
        full_article = self._combine_content(content)
        
        # First pass: Flow and coherence
        flow_improved = self._improve_flow(full_article, tone, reading_level)
        if flow_improved != full_article:
            improvements.append("Improved overall flow and transitions between sections")
        
        # Second pass: Clarity and readability
        clarity_improved = self._improve_clarity(flow_improved, reading_level)
        if clarity_improved != flow_improved:
            improvements.append("Enhanced clarity and readability")
        
        # Third pass: Remove repetitions
        deduplicated = self._remove_repetitions(clarity_improved)
        if deduplicated != clarity_improved:
            improvements.append("Removed repetitive phrases and ideas")
        
        # Fourth pass: Style guide compliance
        style_edited = self._apply_style_guide(deduplicated, style_guide, tone)
        if style_edited != deduplicated:
            improvements.append("Applied style guide requirements")
        
        # Split back into sections
        edited_content = self._split_into_sections(style_edited, content.keys())
        
        word_count = sum(len(text.split()) for text in edited_content.values())
        
        return {
            "status": "success",
            "edited_content": edited_content,
            "improvements": improvements,
            "word_count": word_count
        }
    
    def _combine_content(self, content: Dict[str, str]) -> str:
        """Combine all sections into a single article."""
        sections = []
        for section_title, section_content in content.items():
            sections.append(f"## {section_title}\n\n{section_content}")
        return "\n\n".join(sections)
    
    def _split_into_sections(self, full_article: str, original_section_titles: list) -> Dict[str, str]:
        """Split the edited article back into sections."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in full_article.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()
        
        # Ensure all original sections are present and not empty
        for title in original_section_titles:
            if title not in sections or not sections[title].strip():
                # If section is missing or empty, mark it for regeneration
                sections[title] = None  # Use None to indicate missing content
        
        # Remove None entries (empty sections)
        sections = {k: v for k, v in sections.items() if v is not None and v.strip()}
        
        return sections
    
    def _improve_flow(self, content: str, tone: str, reading_level: str) -> str:
        """Improve flow and transitions between sections."""
        prompt = f"""You are an expert editor. Improve the flow and coherence of this blog post to make it sound more human-written and natural.

Tone: {tone}
Reading Level: {reading_level}

Focus on:
1. Smooth transitions between sections (avoid formulaic transitions like "Furthermore", "In addition")
2. Logical progression of ideas with natural flow
3. Connecting paragraphs naturally without forced connectors
4. Maintaining narrative flow that feels conversational
5. Varying sentence structure and length for human-like rhythm
6. Making it sound like a human expert wrote it, not AI

CRITICAL - MAKE IT SOUND HUMAN:
- Vary sentence openings - don't start every paragraph the same way
- Mix short and long sentences naturally
- Remove AI-sounding phrases and formulaic structures
- Use contractions where appropriate for natural flow
- Let ideas flow organically rather than forcing rigid structures
- Add personality and voice while maintaining professionalism

CRITICAL: Preserve ALL image markdown syntax exactly as written (e.g., ![Alt text](url) and *description*). Do not remove, modify, or move images.

Return the improved article that sounds like it was written by a human expert, not AI. Keep all the original content and structure, just improve transitions and make it more natural.

Article:
{content}
"""
        
        return self.call_llm(prompt)
    
    def _improve_clarity(self, content: str, reading_level: str) -> str:
        """Improve clarity and readability."""
        prompt = f"""You are an expert editor. Improve the clarity and readability of this blog post while making it sound more human-written.

Target Reading Level: {reading_level}

Focus on:
1. Simplifying complex sentences while keeping natural flow
2. Clarifying ambiguous statements with human-like explanations
3. Using precise language that sounds natural, not robotic
4. Ensuring each paragraph has a clear purpose and flows naturally
5. Making technical concepts accessible with conversational explanations
6. Varying sentence structure to avoid repetitive patterns
7. Using natural transitions instead of formulaic connectors

CRITICAL - SOUND HUMAN:
- Write as a human expert would explain to a colleague
- Avoid overly structured or formulaic language
- Use natural phrasing and varied sentence patterns
- Make it conversational while maintaining clarity
- Remove AI-sounding patterns and repetitive structures

CRITICAL: Preserve ALL image markdown syntax exactly as written (e.g., ![Alt text](url) and *description*). Do not remove, modify, or move images.

Return the improved article that's clearer AND sounds more human-written. Maintain the same meaning and structure.

Article:
{content}
"""
        
        return self.call_llm(prompt)
    
    def _remove_repetitions(self, content: str) -> str:
        """Remove repetitive phrases and ideas."""
        # First, remove duplicate headers manually
        lines = content.split("\n")
        seen_headers = set()
        cleaned_lines = []
        
        for line in lines:
            if line.startswith("## "):
                header_text = line.strip()
                if header_text not in seen_headers:
                    seen_headers.add(header_text)
                    cleaned_lines.append(line)
                # Skip duplicate headers
            else:
                cleaned_lines.append(line)
        
        content = "\n".join(cleaned_lines)
        
        # Then use LLM for content deduplication
        prompt = f"""You are an expert editor. Remove repetitive content from this blog post while maintaining natural, human-like writing.

Focus on:
1. Eliminating repeated phrases or sentences
2. Consolidating redundant ideas
3. Removing unnecessary repetition of the same point
4. Keeping only the best version of repeated concepts
5. Removing duplicate section headers (keep only the first occurrence)
6. Varying sentence structures and paragraph openings after removing repetitions

CRITICAL - MAINTAIN HUMAN VOICE:
- After removing repetitions, ensure the writing still flows naturally
- Don't make it sound overly edited or robotic
- Keep the conversational, human tone
- Vary how information is presented to avoid new repetitive patterns
- Make sure it still sounds like a human expert wrote it

CRITICAL: Preserve ALL image markdown syntax exactly as written (e.g., ![Alt text](url) and *description*). Do not remove, modify, or move images.

Return the article without repetitions, but still sounding natural and human-written. Maintain all unique information and insights.

Article:
{content}
"""
        
        return self.call_llm(prompt)
    
    def _apply_style_guide(self, content: str, style_guide: Dict[str, Any], tone: str) -> str:
        """Apply style guide requirements."""
        if not style_guide:
            return content
        
        style_rules = "\n".join([f"- {k}: {v}" for k, v in style_guide.items()])
        
        prompt = f"""You are an expert editor. Apply the following style guide to this blog post.

Tone: {tone}
Style Guide Rules:
{style_rules}

CRITICAL: Preserve ALL image markdown syntax exactly as written (e.g., ![Alt text](url) and *description*). Do not remove, modify, or move images.

Ensure the article follows all style guide requirements while maintaining its quality and meaning.

Article:
{content}
"""
        
        return self.call_llm(prompt)


