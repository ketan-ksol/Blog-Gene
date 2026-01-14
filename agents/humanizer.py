"""Humanizer Agent: Detects and converts AI-generated text to human-written language."""
from typing import Dict, Any
from .base import BaseAgent


class HumanizerAgent(BaseAgent):
    """Agent responsible for making content sound more human-written."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert AI-generated text to human-written language.
        
        Input:
            - content: dict mapping section titles to content
            - tone: str
            - reading_level: str
        
        Output:
            - humanized_content: dict
            - improvements: list of changes made
        """
        from agents.base import _thought_callback
        import time
        
        content = input_data.get("content", {})
        section_count = len(content) if isinstance(content, dict) else 0
        
        if _thought_callback:
            _thought_callback("Humanizer", f"Analyzing {section_count} sections for AI-generated patterns...")
            time.sleep(0.3)
            _thought_callback("Humanizer", f"Rewriting content to sound more natural and human-written...")
            time.sleep(0.3)
        
        content = input_data.get("content", {})
        tone = input_data.get("tone", "professional")
        reading_level = input_data.get("reading_level", "business professional")
        
        humanized_content = {}
        improvements = []
        
        # Process each section
        for section_title, section_content in content.items():
            if _thought_callback and section_title not in ["Introduction", "Conclusion"]:
                _thought_callback("Humanizer", f"Humanizing section: '{section_title}' - removing AI patterns and adding natural flow...")
                time.sleep(0.2)
            
            humanized_section = self._humanize_section(section_content, section_title, tone, reading_level)
            
            if humanized_section != section_content:
                improvements.append(f"Humanized {section_title}")
            
            humanized_content[section_title] = humanized_section
        
        if _thought_callback:
            _thought_callback("Humanizer", f"Humanization complete! Content now sounds more natural and human-written.")
        
        return {
            "status": "success",
            "humanized_content": humanized_content,
            "improvements": improvements
        }
    
    def _humanize_section(self, content: str, section_title: str, tone: str, reading_level: str) -> str:
        """Convert AI-generated text to human-written language."""
        prompt = f"""You are an expert editor specializing in making AI-generated text sound like it was written by a human expert.

Your task: Rewrite this content to sound completely natural and human-written, removing all AI-sounding patterns.

Section: {section_title}
Tone: {tone}
Reading Level: {reading_level}

CRITICAL INSTRUCTIONS - MAKE IT SOUND HUMAN:

1. REMOVE AI-SOUNDING PATTERNS:
   - Eliminate phrases like "Furthermore", "In addition", "It is important to note", "Additionally", "Moreover"
   - Remove "In conclusion", "To summarize", "In summary" (unless absolutely necessary)
   - Avoid "In today's digital landscape", "In the realm of", "It is worth noting"
   - Remove excessive qualifiers like "very", "extremely", "significantly" when overused
   - Eliminate formulaic structures like "First... Second... Third..." unless truly needed

2. VARY SENTENCE STRUCTURE:
   - Mix short punchy sentences (5-10 words) with longer explanatory ones (15-25 words)
   - Vary paragraph openings - don't start every paragraph with "The", "This", "It", "When"
   - Use different sentence types: declarative, interrogative, imperative
   - Break up long complex sentences into shorter, clearer ones when appropriate

3. ADD HUMAN TOUCHES:
   - Use contractions naturally (don't, can't, it's, we're) where appropriate
   - Include occasional rhetorical questions to engage readers
   - Add personality and voice - don't sound robotic
   - Use specific, concrete language instead of vague generalizations
   - Include occasional asides or parenthetical thoughts that feel natural
   - Use active voice primarily, but mix in passive voice naturally when it flows better

4. NATURAL FLOW:
   - Let ideas flow organically rather than forcing rigid structures
   - Use natural transitions that don't sound formulaic
   - Connect ideas smoothly without overusing transition words
   - Write as if explaining to a colleague or friend, not a formal report

5. REMOVE REPETITIVE PATTERNS:
   - If you see the same sentence structure repeated, vary it
   - If paragraphs always start the same way, change the openings
   - If you see the same transition words repeatedly, remove or replace them

6. PRESERVE:
   - All markdown formatting (headers, lists, code blocks, images)
   - Technical accuracy and facts
   - Key information and insights
   - Citations and references
   - The overall meaning and message

CRITICAL: Preserve ALL image markdown syntax exactly as written (e.g., <!-- Image needed: ... -->). Do not remove, modify, or move images.

Return the rewritten content that sounds like it was written by a human expert, not AI. Make it natural, conversational, and engaging while maintaining professionalism.

Original content:
{content}

Rewritten human-sounding content:"""
        
        return self.call_llm(prompt, capture_thoughts=False)

