"""Planner Agent: Creates blog outline, thesis, and structure."""
import json
from typing import Dict, Any
from .base import BaseAgent


class PlannerAgent(BaseAgent):
    """Agent responsible for planning blog structure and content strategy."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comprehensive blog plan.
        
        Input:
            - topic: str
            - target_audience: str (optional)
            - tone: str (optional)
            - word_count: int (optional)
        
        Output:
            - angle: str
            - thesis: str
            - outline: list of sections
            - section_goals: dict
            - required_facts: list
            - search_queries: list
        """
        topic = input_data.get("topic", "")
        target_audience = input_data.get("target_audience", "enterprise professionals")
        tone = input_data.get("tone", "professional")
        word_count = input_data.get("word_count", 2000)
        sections_per_article = input_data.get("sections_per_article", 5)
        
        # Calculate section range based on sections_per_article
        min_sections = max(3, sections_per_article - 1)
        max_sections = sections_per_article + 2
        
        prompt = f"""You are an expert content strategist creating a comprehensive blog plan for an enterprise audience.

MARKETING CONTEXT:
- This blog is written by Ksolves, a company specializing in enterprise solutions, implementation, migration, and consulting
- The blog should be informative yet marketing-oriented - helping readers understand solutions while positioning Ksolves as a partner
- Focus on challenges businesses face and how solutions can help
- Include sections that naturally lead to positioning Ksolves as a solution provider

Topic: {topic}
Target Audience: {target_audience}
Tone: {tone} (with marketing focus - informative yet solution-oriented)
Target Word Count: {word_count}
Target Number of Sections: {sections_per_article}

IMPORTANT: Focus specifically on {topic}. Create a plan that addresses {topic} directly, not general information about the broader subject area. Include marketing angles that position challenges as opportunities for improvement and solutions.

Create a detailed blog plan with the following structure:

1. **Angle**: A unique perspective or approach to the topic that will engage the audience
2. **Thesis**: The main argument or key message of the blog post
3. **Outline**: A structured outline with {min_sections}-{max_sections} sections (target: {sections_per_article} sections), each with:
   - Section title (H2)
   - Subsection titles (H3) if needed
   - Brief description of what should be covered
4. **Section Goals**: For each section, specify:
   - What the reader should learn
   - Key points to cover
   - Desired outcome
5. **Required Facts**: List specific facts, statistics, or data points needed
6. **Search Queries**: Generate 5-10 specific search queries to gather research

Return your response as a JSON object with this exact structure:
{{
    "angle": "...",
    "thesis": "...",
    "outline": [
        {{
            "section_title": "...",
            "subsections": ["..."],
            "description": "..."
        }}
    ],
    "section_goals": {{
        "section_1": {{
            "learning_objectives": ["..."],
            "key_points": ["..."],
            "desired_outcome": "..."
        }}
    }},
    "required_facts": [
        {{
            "fact": "...",
            "type": "statistic|quote|example|definition"
        }}
    ],
    "search_queries": ["...", "..."]
}}
"""
        
        try:
            # Provide context about what we're planning
            from agents.base import _thought_callback
            if _thought_callback:
                _thought_callback("Planner", f"Analyzing target audience and creating a strategic content plan...")
                import time
                time.sleep(0.3)  # Brief pause for UI update
                _thought_callback("Planner", f"Structuring outline with 5-7 sections, defining thesis, and identifying key research areas...")
                time.sleep(0.3)
                _thought_callback("Planner", f"Generating search queries and planning content flow for maximum engagement...")
            
            response = self.call_llm(prompt, capture_thoughts=False)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to call LLM: {str(e)}",
                "error_type": type(e).__name__
            }
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(response)
            
            # Final thought after successful parsing
            from agents.base import _thought_callback
            if _thought_callback:
                outline_count = len(plan.get('outline', []))
                _thought_callback("Planner", f"Plan complete! Created outline with {outline_count} sections ready for research.")
        except json.JSONDecodeError:
            # Fallback: create a basic structure
            plan = self._create_fallback_plan(topic, target_audience, tone)
            from agents.base import _thought_callback
            if _thought_callback:
                _thought_callback("Planner", f"Plan complete! Created fallback outline ready for research.")
        
        return {
            "status": "success",
            "plan": plan,
            "topic": topic
        }
    
    def _create_fallback_plan(self, topic: str, audience: str, tone: str) -> Dict[str, Any]:
        """Create a basic plan structure if JSON parsing fails."""
        return {
            "angle": f"An in-depth exploration of {topic} for {audience}",
            "thesis": f"This article examines {topic} and its implications for modern enterprises.",
            "outline": [
                {
                    "section_title": "Introduction",
                    "subsections": [],
                    "description": "Introduce the topic and its relevance"
                },
                {
                    "section_title": "Understanding the Core Concepts",
                    "subsections": [],
                    "description": "Explain fundamental concepts"
                },
                {
                    "section_title": "Key Benefits and Applications",
                    "subsections": [],
                    "description": "Discuss practical applications"
                },
                {
                    "section_title": "Best Practices",
                    "subsections": [],
                    "description": "Provide actionable recommendations"
                },
                {
                    "section_title": "Conclusion",
                    "subsections": [],
                    "description": "Summarize key takeaways"
                }
            ],
            "section_goals": {},
            "required_facts": [],
            "search_queries": [f"{topic} statistics", f"{topic} best practices", f"{topic} enterprise"]
        }



