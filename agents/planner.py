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
        
        prompt = f"""You are an expert content strategist creating a comprehensive blog plan for an enterprise audience.

Topic: {topic}
Target Audience: {target_audience}
Tone: {tone}
Target Word Count: {word_count}

IMPORTANT: Focus specifically on {topic}. Create a plan that addresses {topic} directly, not general information about the broader subject area.

Create a detailed blog plan with the following structure:

1. **Angle**: A unique perspective or approach to the topic that will engage the audience
2. **Thesis**: The main argument or key message of the blog post
3. **Outline**: A structured outline with 5-7 sections, each with:
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
            response = self.call_llm(prompt)
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
        except json.JSONDecodeError:
            # Fallback: create a basic structure
            plan = self._create_fallback_plan(topic, target_audience, tone)
        
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



