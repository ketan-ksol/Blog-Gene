"""Writer Agent: Writes blog content section by section."""
from typing import Dict, Any, List
from .base import BaseAgent


class WriterAgent(BaseAgent):
    """Agent responsible for writing blog content."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write blog content based on outline and research.
        
        Input:
            - outline: list of sections
            - thesis: str
            - angle: str
            - fact_table: dict
            - citations: list
            - tone: str
            - reading_level: str
            - section_goals: dict
        
        Output:
            - content: dict mapping section titles to content
            - word_count: int
        """
        outline = input_data.get("outline", [])
        thesis = input_data.get("thesis", "")
        angle = input_data.get("angle", "")
        fact_table = input_data.get("fact_table", {})
        citations = input_data.get("citations", [])
        tone = input_data.get("tone", "professional")
        reading_level = input_data.get("reading_level", "college")
        section_goals = input_data.get("section_goals", {})
        
        content = {}
        total_word_count = 0
        
        # Get topic for focused writing
        topic = input_data.get("topic", "")
        target_word_count = input_data.get("target_word_count", 1500)
        min_word_count = input_data.get("min_word_count", 1000)
        
        # Calculate words per section (distribute evenly)
        words_per_section = max(200, (target_word_count - 200) // (len(outline) + 2))  # +2 for intro and conclusion
        
        # Write introduction first
        intro_content = self._write_introduction(thesis, angle, tone, reading_level, topic, min(200, words_per_section))
        content["Introduction"] = intro_content
        total_word_count += len(intro_content.split())
        
        # Write each section
        for i, section in enumerate(outline, 1):
            section_title = section.get("section_title", f"Section {i}")
            section_desc = section.get("description", "")
            subsections = section.get("subsections", [])
            goals = section_goals.get(f"section_{i}", {})
            
            section_content = self._write_section(
                section_title=section_title,
                description=section_desc,
                subsections=subsections,
                goals=goals,
                fact_table=fact_table,
                citations=citations,
                tone=tone,
                reading_level=reading_level,
                section_number=i,
                total_sections=len(outline),
                topic=topic,
                target_words=words_per_section
            )
            
            # Validate section has content
            if section_content and len(section_content.strip()) > 50:
                content[section_title] = section_content
                total_word_count += len(section_content.split())
            else:
                # Retry if content is too short
                print(f"⚠️  Section '{section_title}' has insufficient content. Retrying...")
                section_content = self._write_section(
                    section_title=section_title,
                    description=section_desc,
                    subsections=subsections,
                    goals=goals,
                    fact_table=fact_table,
                    citations=citations,
                    tone=tone,
                    reading_level=reading_level,
                    section_number=i,
                    total_sections=len(outline),
                    topic=topic,
                    target_words=words_per_section
                )
                if section_content and len(section_content.strip()) > 50:
                    content[section_title] = section_content
                    total_word_count += len(section_content.split())
                else:
                    print(f"⚠️  Warning: Section '{section_title}' still has minimal content")
                    content[section_title] = section_content or f"Content for {section_title} is being generated..."
        
        # Write conclusion
        conclusion = self._write_conclusion(thesis, tone, reading_level, topic, min(150, words_per_section))
        content["Conclusion"] = conclusion
        total_word_count += len(conclusion.split())
        
        # Check if we need to adjust content to meet word count requirements
        if total_word_count < min_word_count:
            # Need more content - expand sections
            print(f"⚠️  Word count ({total_word_count}) below minimum ({min_word_count}). Expanding content...")
            for section_title in list(content.keys()):
                if section_title not in ["Introduction", "Conclusion"]:
                    current_words = len(content[section_title].split())
                    if current_words < words_per_section:
                        # Expand this section
                        expanded = self._expand_section(
                            content[section_title],
                            section_title,
                            topic,
                            words_per_section - current_words
                        )
                        content[section_title] = expanded
                        total_word_count += len(expanded.split()) - current_words
        
        return {
            "status": "success",
            "content": content,
            "word_count": total_word_count,
            "sections_written": len(content)
        }
    
    def _write_introduction(self, thesis: str, angle: str, tone: str, reading_level: str, topic: str, target_words: int = 200) -> str:
        """Write the introduction section."""
        prompt = f"""Write a compelling, focused introduction for a blog post about: {topic}

Thesis: {thesis}
Angle: {angle}
Tone: {tone}
Reading Level: {reading_level}

Requirements:
- Hook the reader in the first sentence with a specific, relevant point about {topic}
- Start with context about why {topic} is important (mention real-world impact, scale, or consequences)
- Focus specifically on {topic} - avoid generic information
- Establish the problem or challenge related to {topic}
- Present the thesis clearly in relation to {topic}
- Preview what the article will cover about {topic} (mention the specific mistakes/solutions)
- Length: {target_words} words MINIMUM
- Use {tone} tone appropriate for {reading_level} reading level
- Be specific and topic-focused, not generic
- Write in an engaging, conversational style that draws readers in
- Include a transition sentence that leads into the main content

Structure:
1. Opening hook about {topic} and its importance/impact
2. Context about the challenges/problems
3. Thesis statement
4. Preview of what's coming

Write the introduction content. DO NOT include any markdown headers.
Write substantial, focused content about {topic} that hooks the reader and sets up the article."""
        
        return self.call_llm(prompt)
    
    def _write_section(
        self,
        section_title: str,
        description: str,
        subsections: List[str],
        goals: Dict[str, Any],
        fact_table: Dict,
        citations: List[Dict],
        tone: str,
        reading_level: str,
        section_number: int,
        total_sections: int,
        topic: str = "",
        target_words: int = 300
    ) -> str:
        """Write a single section of the blog."""
        
        # Prepare relevant facts for this section
        relevant_facts = self._extract_relevant_facts(section_title, fact_table)
        relevant_citations = self._extract_relevant_citations(section_title, citations)
        
        topic_context = f" This section is part of a blog post specifically about: {topic}. Focus on {topic} and avoid generic information." if topic else ""
        
        prompt = f"""Write section {section_number} of {total_sections} for a blog post about {topic}.{topic_context}

Section Title: {section_title}
Description: {description}
Subsections to cover: {', '.join(subsections) if subsections else 'None specified'}

Learning Objectives: {goals.get('learning_objectives', [])}
Key Points: {goals.get('key_points', [])}
Desired Outcome: {goals.get('desired_outcome', '')}

Relevant Facts and Data:
{self._format_facts_for_prompt(relevant_facts)}

Relevant Citations:
{self._format_citations_for_prompt(relevant_citations)}

Requirements:
- Tone: {tone}
- Reading Level: {reading_level}
- Length: {target_words} words MINIMUM - write comprehensive, detailed, actionable content
- FOCUS SPECIFICALLY ON {topic.upper()} - avoid generic information about the broader topic

Content Structure (follow this pattern for mistake/problem sections):
1. Start with a clear explanation of the mistake/problem
2. Include a "Where Developers Make Mistakes" or "Common Mistakes" subsection with specific examples
3. Add "Real-World Impact" or "Symptoms" subsection showing consequences
4. Provide detailed "How to Fix" or "Best Practices" subsection with actionable solutions
5. Include specific configuration examples, code snippets, or step-by-step guidance when relevant

For other sections:
- Use clear H3 subsections (###) to organize content
- Include specific examples, case studies, and data directly related to {topic}
- Use citations naturally (e.g., "According to [Source]...")
- Write engaging, informative content with actionable insights about {topic}
- Provide real value - explain concepts deeply, give concrete examples, offer detailed solutions
- Include relevant image suggestions in markdown format: ![Alt text](image-url) when appropriate
- Write in a conversational yet professional style
- Use bullet points and lists for clarity
- Include specific numbers, metrics, or technical details when relevant

CRITICAL: 
- Write the section content. DO NOT include the section title "## {section_title}" as a header.
- Start directly with the content. Use ### for H3 subsections.
- Write AT LEAST {target_words} words of substantial, detailed, topic-focused content.
- Do not write generic or superficial content - be specific, detailed, and actionable.
- Make it comprehensive enough that readers get real value."""
        
        return self.call_llm(prompt)
    
    def _write_conclusion(self, thesis: str, tone: str, reading_level: str, topic: str, target_words: int = 150) -> str:
        """Write the conclusion section."""
        prompt = f"""Write a strong, focused conclusion for a blog post about: {topic}

Thesis: {thesis}
Tone: {tone}
Reading Level: {reading_level}

Requirements:
- Reinforce the main thesis specifically in relation to {topic}
- Summarize key takeaways about {topic}
- Provide a call to action or forward-looking statement related to {topic}
- Length: {target_words} words
- Use {tone} tone appropriate for {reading_level} reading level
- Focus on {topic} - avoid generic conclusions

Write the conclusion content. DO NOT include any markdown headers.
Write substantial, topic-focused content ({target_words} words) that reinforces key points about {topic}."""
        
        return self.call_llm(prompt)
    
    def _extract_relevant_facts(self, section_title: str, fact_table: Dict) -> List[Dict]:
        """Extract facts relevant to a section."""
        relevant = []
        section_keywords = section_title.lower().split()
        
        for fact, fact_data in fact_table.items():
            fact_lower = fact.lower()
            if any(keyword in fact_lower for keyword in section_keywords if len(keyword) > 3):
                relevant.append({"fact": fact, **fact_data})
        
        return relevant[:5]  # Top 5 relevant facts
    
    def _extract_relevant_citations(self, section_title: str, citations: List[Dict]) -> List[Dict]:
        """Extract citations relevant to a section."""
        relevant = []
        section_keywords = section_title.lower().split()
        
        for citation in citations:
            citation_text = f"{citation.get('title', '')} {citation.get('content', '')}".lower()
            if any(keyword in citation_text for keyword in section_keywords if len(keyword) > 3):
                relevant.append(citation)
        
        return relevant[:3]  # Top 3 relevant citations
    
    def _format_facts_for_prompt(self, facts: List[Dict]) -> str:
        """Format facts for the writing prompt."""
        if not facts:
            return "No specific facts provided for this section."
        
        formatted = []
        for fact in facts:
            fact_text = fact.get("fact", "")
            fact_type = fact.get("type", "general")
            sources = fact.get("sources", [])
            verified = fact.get("verified", False)
            
            source_info = ""
            if sources:
                source_info = f" (Sources: {', '.join([s.get('title', 'Unknown') for s in sources[:2]])})"
            
            formatted.append(f"- {fact_text} [{fact_type}]{' ✓' if verified else ''}{source_info}")
        
        return "\n".join(formatted)
    
    def _format_citations_for_prompt(self, citations: List[Dict]) -> str:
        """Format citations for the writing prompt."""
        if not citations:
            return "No specific citations provided for this section."
        
        formatted = []
        for i, citation in enumerate(citations, 1):
            title = citation.get("title", "Unknown Source")
            url = citation.get("url", "")
            excerpt = citation.get("content", "")[:150]
            formatted.append(f"{i}. {title} ({url})\n   Excerpt: {excerpt}...")
        
        return "\n".join(formatted)
    
    def _expand_section(self, current_content: str, section_title: str, topic: str, additional_words: int) -> str:
        """Expand a section with more content."""
        prompt = f"""Expand the following section content about {topic}. Add approximately {additional_words} more words of detailed, actionable content.

Current content:
{current_content}

Requirements:
- Add more depth and detail specifically about {topic}
- Include additional examples, case studies, real-world scenarios, or technical details
- Add subsections with H3 headers (###) if appropriate (e.g., "Real-World Impact", "Best Practices", "Common Pitfalls")
- Include specific configuration examples, code snippets, or step-by-step guidance when relevant
- Maintain the same tone and style as the existing content
- Focus on {topic} - avoid generic information
- Include relevant image suggestions if appropriate: ![Alt text](image-url)
- Use bullet points and lists for clarity
- Make it comprehensive and actionable

Write the expanded content, maintaining ALL existing content and adding substantial new detail. Do not remove or summarize existing content."""
        
        return self.call_llm(prompt)


