"""Writer Agent: Writes blog content section by section."""
from typing import Dict, Any, List, Optional
from .base import BaseAgent
import os
import requests
from urllib.parse import quote, urljoin, urlparse
import urllib3
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WriterAgent(BaseAgent):
    """Agent responsible for writing blog content."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from agents.base import _thought_callback
        import time
        
        topic = input_data.get("topic", "")
        outline = input_data.get("outline", [])
        section_count = len(outline) if isinstance(outline, list) else 0
        
        if _thought_callback:
            _thought_callback("Writer", f"Starting content creation: Crafting engaging introduction...")
            time.sleep(0.3)
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
        if _thought_callback:
            _thought_callback("Writer", f"Writing compelling introduction that hooks readers and introduces the topic...")
        
        intro_content = self._write_introduction(thesis, angle, tone, reading_level, topic, min(200, words_per_section))
        content["Introduction"] = intro_content
        total_word_count += len(intro_content.split())
        
        if _thought_callback:
            _thought_callback("Writer", f"Introduction complete! Now writing {section_count} main sections with detailed content...")
            time.sleep(0.3)
        
        # Write each section (skip Introduction and Conclusion if they're in the outline - we write them separately)
        section_index = 0
        for section in outline:
            section_title = section.get("section_title", f"Section {section_index + 1}")
            
            # Skip Introduction and Conclusion from outline - we write them separately
            if section_title in ["Introduction", "Conclusion"]:
                continue
            
            section_index += 1
            
            if _thought_callback:
                _thought_callback("Writer", f"Writing section {section_index}/{section_count}: '{section_title}' - Developing key points and examples...")
                time.sleep(0.2)
            section_desc = section.get("description", "")
            subsections = section.get("subsections", [])
            goals = section_goals.get(f"section_{section_index}", {})
            
            section_content = self._write_section(
                section_title=section_title,
                description=section_desc,
                subsections=subsections,
                goals=goals,
                fact_table=fact_table,
                citations=citations,
                tone=tone,
                reading_level=reading_level,
                section_number=section_index,
                total_sections=section_count,
                topic=topic,
                target_words=words_per_section
            )
            
            # Validate section has content
            if section_content and len(section_content.strip()) > 50:
                content[section_title] = section_content
                word_count = len(section_content.split())
                total_word_count += word_count
                if _thought_callback:
                    _thought_callback("Writer", f"Section {section_index}/{section_count} complete! ({word_count} words) Moving to next section...")
                    time.sleep(0.2)
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
                    section_number=section_index,
                    total_sections=section_count,
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
        if _thought_callback:
            _thought_callback("Writer", f"All sections complete! Writing powerful conclusion that summarizes key points...")
            time.sleep(0.2)
        
        conclusion = self._write_conclusion(thesis, tone, reading_level, topic, min(150, words_per_section))
        content["Conclusion"] = conclusion
        total_word_count += len(conclusion.split())
        
        # Add image descriptions to relevant sections (at least 1 per document)
        if _thought_callback:
            _thought_callback("Writer", f"Adding image descriptions to enhance visual appeal...")
        
        # Note: Image search is disabled - only descriptions are added
        content = self._add_images_to_content(content, topic, outline)
        
        if _thought_callback:
            _thought_callback("Writer", f"Content writing complete! Generated {total_word_count} words across {len(content)} sections (including introduction and conclusion). Ready for editing.")
        
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
            "sections_written": len(content)  # Count all sections including Introduction and Conclusion
        }
    
    def _write_introduction(self, thesis: str, angle: str, tone: str, reading_level: str, topic: str, target_words: int = 200) -> str:
        """Write the introduction section."""
        # Check if this is a technical topic
        is_technical = self._is_technical_topic(topic)
        technical_note = ""
        if is_technical:
            technical_note = "\n- Note: This is a technical topic - code examples may be included in relevant sections where they add practical value (e.g., implementation guides, configuration steps, troubleshooting)."
        
        prompt = f"""Write a compelling, marketing-focused introduction for a blog post about: {topic}

Thesis: {thesis}
Angle: {angle}
Tone: {tone} (with marketing focus)
Reading Level: {reading_level}

MARKETING CONTEXT:
- This blog is written by Ksolves, a company specializing in enterprise solutions
- Ksolves helps businesses with implementation, migration, consulting, and modernization
- The tone should be informative yet marketing-oriented - helping readers understand solutions while positioning Ksolves as a partner
- Naturally mention Ksolves where it makes sense, but don't force it - focus on value first

Requirements:
- Hook the reader in the first sentence with a specific, relevant point about {topic}
- Start with context about why {topic} is important (mention real-world impact, scale, or consequences)
- Focus specifically on {topic} - avoid generic information
- Establish the problem or challenge related to {topic}
- Present the thesis clearly in relation to {topic}
- Preview what the article will cover about {topic} (mention the specific mistakes/solutions){technical_note}
- Length: {target_words} words MINIMUM
- Use {tone} tone with marketing focus appropriate for {reading_level} reading level
- Be specific and topic-focused, not generic
- Write in an engaging, conversational marketing style that draws readers in
- Include a transition sentence that leads into the main content

Structure:
1. Opening hook about {topic} and its importance/impact (marketing angle)
2. Context about the challenges/problems businesses face
3. Thesis statement
4. Preview of what's coming

Write the introduction content. DO NOT include any markdown headers.
Write substantial, focused content about {topic} that hooks the reader and sets up the article.

WRITING STYLE - MARKETING + HUMAN:
- Write naturally and conversationally - as if you're telling a story or explaining to a friend
- Vary your sentence structure - mix short impactful sentences with longer explanatory ones
- Use natural language - avoid overly formal or robotic phrasing
- Start with a hook that feels authentic, not formulaic
- Don't use AI-sounding phrases like "In today's world" or "In the realm of"
- Write with personality and voice - make it engaging and human
- Use marketing language naturally - focus on benefits, solutions, and value
- Position challenges as opportunities for improvement"""
        
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
        
        # Check if this is a technical topic and if code examples would be relevant
        is_technical = self._is_technical_topic(topic)
        code_examples_instruction = ""
        if is_technical:
            # Check if this section would benefit from code examples
            section_lower = section_title.lower()
            description_lower = description.lower() if description else ""
            subsections_lower = ' '.join(subsections).lower() if subsections else ""
            combined_text = f"{section_lower} {description_lower} {subsections_lower}"
            
            # Only suggest code examples for sections that would actually need them
            code_relevant_keywords = [
                'how to', 'fix', 'implement', 'configure', 'setup', 'install', 'troubleshoot',
                'example', 'code', 'snippet', 'configuration', 'command', 'script',
                'mistake', 'error', 'solution', 'best practice', 'pattern', 'api',
                'sdk', 'integration', 'deployment', 'migration', 'optimization'
            ]
            
            needs_code = any(keyword in combined_text for keyword in code_relevant_keywords)
            
            if needs_code:
                code_examples_instruction = """
CODE EXAMPLES (ONLY when truly needed):
- Include code examples ONLY if they directly help explain or demonstrate the concept
- DO NOT add code examples just for the sake of having them - they must add real value
- Code examples should be:
  * Real, working examples (not pseudocode)
  * Properly formatted in markdown code blocks with appropriate language tags (e.g., ```python, ```javascript, ```yaml, ```bash, ```json)
  * Contextual - explain what the code does and why it's relevant
  * Include comments in code when helpful
  * Show both "wrong" and "right" approaches when demonstrating mistakes/fixes
- Include code examples ONLY in these cases:
  * "How to Fix" or "Best Practices" subsections that show actual implementation
  * When explaining specific configuration or setup steps
  * When demonstrating implementation patterns that readers can copy
  * When showing troubleshooting steps with actual commands/code
- DO NOT include code examples if:
  * The section is conceptual or theoretical
  * The section discusses general principles without specific implementation
  * Code would not add clarity or practical value
- Format: Use triple backticks with language identifier, e.g.:
  ```python
  # Example code here
  ```
- Make code examples practical and directly applicable to {topic}
"""
        
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

MARKETING CONTEXT:
- This blog is written by Ksolves, a company specializing in enterprise solutions, implementation, migration, and consulting
- Naturally position Ksolves as a solution provider where relevant (e.g., "Ksolves specializes in...", "With Ksolves' expertise...", "Partnering with Ksolves can help...")
- Focus on value, solutions, and benefits - marketing-oriented but informative
- Include calls to action naturally where appropriate
- Don't over-promote - mention Ksolves organically when discussing solutions or services

Requirements:
- Tone: {tone} (with marketing focus - informative yet solution-oriented)
- Reading Level: {reading_level}
- Length: {target_words} words MINIMUM - write comprehensive, detailed, actionable content
- FOCUS SPECIFICALLY ON {topic.upper()} - avoid generic information about the broader topic
- Marketing angle: Position challenges as opportunities, emphasize solutions and benefits
{code_examples_instruction}
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
- DO NOT include image markdown syntax in your response - images will be added automatically where appropriate
- Write in a conversational yet professional style
- Use bullet points and lists for clarity
- Include specific numbers, metrics, or technical details when relevant

WRITING STYLE - MAKE IT SOUND HUMAN:
- Write naturally, as if you're explaining to a colleague or friend
- Vary sentence length - mix short punchy sentences with longer explanatory ones
- Use natural transitions - avoid formulaic phrases like "Furthermore", "In conclusion", "It is important to note", "Additionally"
- Start paragraphs with varied openings - don't always start with "The", "This", "It"
- Use contractions where appropriate (e.g., "don't", "can't", "it's") to sound more conversational
- Include occasional rhetorical questions to engage readers
- Use active voice primarily, but mix in passive voice naturally when it flows better
- Avoid repetitive sentence structures - vary how you present information
- Write with personality and voice - don't sound robotic or overly formal
- Use specific, concrete language instead of vague generalizations
- Include occasional asides or parenthetical thoughts that feel natural
- Don't overuse bullet points - use them strategically, but also write flowing paragraphs

AVOID AI-SOUNDING PATTERNS:
- Don't start every paragraph with "The" or "This"
- Avoid phrases like "In today's digital landscape", "In the realm of", "It is worth noting"
- Don't use excessive qualifiers like "very", "extremely", "significantly" in every sentence
- Avoid formulaic structures like "First... Second... Third..." unless truly necessary
- Don't overuse transition words - let ideas flow naturally
- Avoid repetitive patterns - if you used a structure once, vary it next time

CRITICAL: 
- Write the section content. DO NOT include the section title "## {section_title}" as a header.
- Start directly with the content. Use ### for H3 subsections.
- Write AT LEAST {target_words} words of substantial, detailed, topic-focused content.
- Do not write generic or superficial content - be specific, detailed, and actionable.
- Make it comprehensive enough that readers get real value.
- MOST IMPORTANTLY: Write as a human expert would - naturally, conversationally, with personality and flow."""
        
        return self.call_llm(prompt)
    
    def _write_conclusion(self, thesis: str, tone: str, reading_level: str, topic: str, target_words: int = 150) -> str:
        """Write the conclusion section."""
        prompt = f"""Write a strong, marketing-focused conclusion for a blog post about: {topic}

Thesis: {thesis}
Tone: {tone} (with marketing focus)
Reading Level: {reading_level}

MARKETING CONTEXT:
- This blog is written by Ksolves, a company specializing in enterprise solutions
- Include a natural call to action mentioning Ksolves as a partner
- Position Ksolves as the solution provider who can help with implementation, migration, or consulting
- Reference the example style: "Ksolves: Your Partner in [topic area]" or similar positioning
- Make it feel like a natural conclusion that invites partnership, not a hard sell

Requirements:
- Reinforce the main thesis specifically in relation to {topic}
- Summarize key takeaways about {topic}
- Include a strong call to action naturally mentioning Ksolves as a solution partner
- Position Ksolves as offering: architecture assessment, migration planning, implementation, consulting, modernization, performance tuning, etc.
- Length: {target_words} words
- Use {tone} tone with marketing focus appropriate for {reading_level} reading level
- Focus on {topic} - avoid generic conclusions
- End with value proposition and partnership invitation

Example style reference:
"Ksolves: Your Partner in [topic area]. Are you considering [relevant action]? Ksolves is here to make your journey smooth, scalable, and cost-effective. We specialize in [relevant services]. Our goal? Help you [benefit] with our deep expertise."

Write the conclusion content. DO NOT include any markdown headers.
Write substantial, topic-focused content ({target_words} words) that reinforces key points and includes a natural call to action with Ksolves.

WRITING STYLE - MARKETING + HUMAN:
- Write naturally - avoid formulaic conclusions like "In conclusion" or "To summarize"
- Vary sentence structure and length for natural flow
- Use conversational marketing language while maintaining professionalism
- End with a strong, memorable closing that includes Ksolves as a partner
- Don't sound robotic or overly structured - let it flow naturally
- Make the call to action feel helpful and consultative, not pushy"""
        
        return self.call_llm(prompt)
    
    def _is_technical_topic(self, topic: str) -> bool:
        """Detect if a topic is technical/IT-related."""
        if not topic:
            return False
        
        topic_lower = topic.lower()
        
        # Technical keywords and patterns
        technical_indicators = [
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin',
            # Technologies and frameworks
            'api', 'sdk', 'framework', 'library', 'database', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql',
            'docker', 'kubernetes', 'k8s', 'container', 'microservice', 'aws', 'azure', 'gcp', 'cloud',
            'kafka', 'redis', 'elasticsearch', 'rabbitmq', 'nginx', 'apache', 'server', 'backend', 'frontend',
            'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring', 'laravel',
            'devops', 'ci/cd', 'jenkins', 'git', 'github', 'gitlab', 'terraform', 'ansible',
            'machine learning', 'ai', 'ml', 'data science', 'analytics', 'big data',
            'security', 'authentication', 'authorization', 'encryption', 'ssl', 'tls', 'oauth',
            'rest', 'graphql', 'soap', 'http', 'https', 'tcp', 'udp', 'protocol',
            'algorithm', 'data structure', 'architecture', 'design pattern', 'refactoring',
            'testing', 'unit test', 'integration test', 'qa', 'debugging', 'logging',
            'performance', 'optimization', 'scalability', 'monitoring', 'observability',
            # IT infrastructure
            'server', 'network', 'infrastructure', 'deployment', 'configuration', 'setup', 'installation',
            'troubleshooting', 'error', 'exception', 'bug', 'fix', 'patch', 'update', 'migration',
            # Code-related terms
            'code', 'programming', 'development', 'software', 'application', 'system', 'platform',
            'implementation', 'integration', 'deployment', 'configuration', 'setup'
        ]
        
        # Check if topic contains technical indicators
        for indicator in technical_indicators:
            if indicator in topic_lower:
                return True
        
        return False
    
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
- DO NOT include image markdown syntax - images are added automatically
- Use bullet points and lists for clarity
- Make it comprehensive and actionable

Write the expanded content, maintaining ALL existing content and adding substantial new detail. Do not remove or summarize existing content."""
        
        return self.call_llm(prompt)
    
    def _add_images_to_content(self, content: Dict[str, str], topic: str, outline: List[Dict], citations: List[Dict] = None) -> Dict[str, str]:
        """Add 2-line image descriptions to relevant sections. Ensure at least 1 image description per document."""
        enhanced_content = content.copy()
        images_added = 0
        
        # Determine which sections would benefit from images
        image_candidates = []
        
        for section_title, section_content in content.items():
            # Skip introduction and conclusion for images (usually not needed)
            if section_title in ["Introduction", "Conclusion"]:
                continue
            
            # Check if section would benefit from an image
            if self._section_needs_image(section_title, section_content, topic):
                image_candidates.append(section_title)
        
        # If no candidates found, add at least one to the most relevant section
        if not image_candidates and outline:
            # Find the first substantial section (not intro/conclusion)
            for section in outline:
                section_title = section.get("section_title", "")
                if section_title in content and section_title not in ["Introduction", "Conclusion"]:
                    image_candidates.append(section_title)
                    break
        
        # Add image descriptions to candidate sections (max 3 to keep focused)
        for section_title in image_candidates[:3]:
            if section_title in enhanced_content:
                section_content = enhanced_content[section_title]
                image_markdown = self._generate_image_url(section_title, topic, None, section_content)
                enhanced_content[section_title] = self._insert_image_in_section(
                    enhanced_content[section_title],
                    image_markdown
                )
                images_added += 1
        
        # Ensure at least 1 image description if none were added
        if images_added == 0 and content:
            # Add to first substantial section
            for section_title in content.keys():
                if section_title not in ["Introduction", "Conclusion"]:
                    section_content = content[section_title]
                    image_markdown = self._generate_image_url(section_title, topic, None, section_content)
                    enhanced_content[section_title] = self._insert_image_in_section(
                        enhanced_content[section_title],
                        image_markdown
                    )
                    images_added += 1
                    break
        
        if images_added > 0:
            print(f"📷 Added {images_added} image(s) to relevant sections")
        
        return enhanced_content
    
    def _section_needs_image(self, section_title: str, section_content: str, topic: str) -> bool:
        """Determine if a section would benefit from an image."""
        title_lower = section_title.lower()
        content_lower = section_content.lower()
        
        # Keywords that suggest an image would be helpful
        image_keywords = [
            "architecture", "diagram", "flowchart", "process", "workflow",
            "comparison", "before and after", "versus", "vs", "difference",
            "structure", "components", "system", "pipeline", "flow",
            "configuration", "setup", "installation", "steps",
            "mistake", "error", "problem", "solution", "fix",
            "example", "screenshot", "visual", "illustration"
        ]
        
        # Check title
        if any(keyword in title_lower for keyword in image_keywords):
            return True
        
        # Check content for image-worthy concepts
        if any(keyword in content_lower for keyword in image_keywords):
            # Only if content is substantial (not just a mention)
            if len(section_content.split()) > 100:
                return True
        
        # Technical sections often benefit from diagrams
        # Generic technical indicators that suggest visual content would be helpful
        technical_indicators = ["system", "cluster", "migration", "cost", "customization", "implementation", "deployment", "integration", "infrastructure", "platform", "service", "api", "database", "network", "cloud"]
        if any(indicator in title_lower or indicator in content_lower[:200] for indicator in technical_indicators):
            if len(section_content.split()) > 150:
                return True
        
        # If section is substantial (200+ words), it likely benefits from an image
        if len(section_content.split()) > 200:
            return True
        
        return False
    
    def _generate_image_url(self, section_title: str, topic: str, citations: List[Dict] = None, section_content: str = "") -> str:
        """Generate a 2-line image description where images are needed."""
        # Generate appropriate image description using LLM based on section context
        image_description = self._get_image_description(section_title, topic, section_content)
        
        # Create a concise 2-line description from the detailed one
        short_description = self._create_short_image_description(section_title, topic, image_description)
        
        # Return only HTML comment format (cleaner, doesn't show in rendered markdown)
        return f"\n<!-- Image needed: {short_description} -->\n"
    
    def _extract_image_from_citations(self, section_title: str, topic: str, citations: List[Dict], section_content: str = "", image_description: str = "") -> Optional[str]:
        """Extract image URLs by fetching and parsing web pages from citations. Checks all citations and returns the best image."""
        all_candidate_images = []
        
        # Search through ALL citations - fetch actual web pages
        for i, citation in enumerate(citations[:5], 1):  # Limit to first 5 to avoid too many requests
            url = citation.get("url", "")
            title = citation.get("title", "Unknown")
            
            if not url or not url.startswith(('http://', 'https://')):
                continue
            
            print(f"      📄 Citation {i}/{min(5, len(citations))}: {title[:60]}...")
            print(f"         URL: {url[:80]}...")
            print(f"         🔍 Fetching webpage to extract images...")
            
            # Fetch all candidate images from this webpage
            candidates = self._fetch_images_from_webpage(url, section_title, topic, section_content, image_description)
            
            if candidates:
                print(f"         ✅ Found {len(candidates)} candidate image(s) on this page")
                all_candidate_images.extend(candidates)
            else:
                print(f"         ℹ️  No suitable images found on this page")
        
        if not all_candidate_images:
            print(f"      ℹ️  No image URLs found in any citations")
            return None
        
        # Sort all candidates from all citations by relevance score
        all_candidate_images.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Filter by minimum relevance threshold (only consider images with score >= 5.0)
        relevant_images = [img for img in all_candidate_images if img['relevance'] >= 5.0]
        
        if not relevant_images:
            best_score = all_candidate_images[0]['relevance'] if all_candidate_images else 0
            print(f"      ⚠️  No images met minimum relevance threshold (5.0) across all citations. Best score: {best_score:.2f}")
            return None
        
        # Return the best image across all citations
        best_image = relevant_images[0]
        print(f"      ✅ Selected best image across all citations (relevance: {best_image['relevance']:.2f}): {best_image['alt'][:50] if best_image['alt'] else 'No alt text'}")
        print(f"         Source: {best_image.get('source', 'Unknown')[:60]}...")
        
        return best_image['url']
    
    def _fetch_images_from_webpage(self, url: str, section_title: str, topic: str, section_content: str = "", image_description: str = "") -> List[Dict]:
        """Fetch a webpage and extract relevant image URLs. Returns list of candidate images with relevance scores."""
        if not BS4_AVAILABLE:
            print(f"         ⚠️  BeautifulSoup4 not available. Install with: pip install beautifulsoup4 lxml")
            return []
        
        try:
            # Handle SSL verification
            ssl_verify = os.getenv("SSL_VERIFY", "true").lower() == "true"
            if not ssl_verify:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Set headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            # Fetch the webpage with timeout
            response = requests.get(url, headers=headers, timeout=10, verify=ssl_verify, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"         ⚠️  HTTP {response.status_code} - Could not fetch page")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find all image tags
            images = soup.find_all('img')
            
            if not images:
                return []
            
            print(f"         📷 Found {len(images)} image(s) on page, analyzing...")
            
            # Extract and filter image URLs
            candidate_images = []
            
            for img in images:
                # Get image source
                img_src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if not img_src:
                    continue
                
                # Convert relative URLs to absolute
                img_url = urljoin(url, img_src)
                
                # Get image attributes for filtering
                img_alt = (img.get('alt') or '').lower()
                img_class = (img.get('class') or [])
                img_id = (img.get('id') or '').lower()
                img_width = img.get('width')
                img_height = img.get('height')
                
                # Skip obvious icons/logos/favicons
                skip_keywords = ['icon', 'logo', 'favicon', 'avatar', 'thumbnail', 'thumb', 'button', 'badge']
                if any(keyword in img_url.lower() or keyword in img_alt or keyword in img_id for keyword in skip_keywords):
                    continue
                
                # Skip very small images (likely icons)
                if img_width and img_height:
                    try:
                        width = int(img_width)
                        height = int(img_height)
                        if width < 200 or height < 200:
                            continue
                    except (ValueError, TypeError):
                        pass
                
                # Quick keyword-based relevance check first
                quick_score = self._calculate_image_relevance_keywords(img_url, img_alt, section_title, topic)
                
                candidate_images.append({
                    'url': img_url,
                    'alt': img_alt,
                    'quick_score': quick_score,
                    'width': img_width,
                    'height': img_height
                })
            
            if not candidate_images:
                return []
            
            # Sort by quick keyword score and take top 5 candidates for LLM evaluation
            candidate_images.sort(key=lambda x: x['quick_score'], reverse=True)
            top_candidates = candidate_images[:5]
            
            print(f"         🤖 Evaluating top {len(top_candidates)} candidate(s) with LLM for relevance...")
            
            # Use LLM to evaluate top candidates
            for candidate in top_candidates:
                candidate['relevance'] = self._calculate_image_relevance_llm(
                    candidate['url'], candidate['alt'], section_title, topic, 
                    section_content, image_description
                )
            
            # Sort by LLM relevance score
            top_candidates.sort(key=lambda x: x['relevance'], reverse=True)
            
            # Add source information to each candidate
            for candidate in top_candidates:
                candidate['source'] = url
            
            # Return all candidates (not just the best one) - let caller decide
            return top_candidates
            
        except requests.exceptions.RequestException as e:
            print(f"         ⚠️  Network error fetching page: {str(e)[:100]}")
            return []
        except Exception as e:
            print(f"         ⚠️  Error parsing webpage: {str(e)[:100]}")
            return []
    
    def _calculate_image_relevance_llm(self, img_url: str, img_alt: str, section_title: str, topic: str, 
                                      section_content: str = "", image_description: str = "") -> float:
        """Calculate relevance score using LLM to evaluate semantic relevance."""
        # First do quick keyword-based filtering
        url_lower = img_url.lower()
        alt_lower = (img_alt or "").lower()
        
        # Quick rejections for obviously irrelevant images
        non_content_keywords = ['ad', 'advertisement', 'banner', 'promo', 'social-share', 'share-button', 
                               'cookie', 'privacy', 'newsletter', 'subscribe']
        if any(keyword in url_lower or keyword in alt_lower for keyword in non_content_keywords):
            return 0.0
        
        # Use LLM to evaluate relevance
        try:
            # Truncate content for prompt
            content_preview = " ".join(section_content.split()[:500]) if section_content else ""
            desc_preview = image_description[:500] if image_description else ""
            
            prompt = f"""Evaluate how relevant an image is to a blog section. Rate from 0-10 where:
- 0-3: Not relevant (generic, unrelated, or decorative)
- 4-6: Somewhat relevant (related topic but not specific to section)
- 7-8: Relevant (matches section topic and content well)
- 9-10: Highly relevant (perfectly matches section content and image description)

Blog Topic: {topic}
Section Title: {section_title}
Section Content Preview: {content_preview}
Desired Image Description: {desc_preview}

Image URL: {img_url[:200]}
Image Alt Text: {img_alt[:200] if img_alt else "No alt text"}

Respond with ONLY a number from 0-10, nothing else."""
            
            response = self.call_llm(prompt).strip()
            
            # Extract number from response
            import re
            match = re.search(r'\b([0-9]|10)\b', response)
            if match:
                score = float(match.group(1))
                return score
            else:
                # Fallback to keyword-based scoring
                return self._calculate_image_relevance_keywords(img_url, img_alt, section_title, topic)
                
        except Exception as e:
            print(f"         ⚠️  LLM relevance check failed: {str(e)[:50]}. Using keyword-based scoring.")
            return self._calculate_image_relevance_keywords(img_url, img_alt, section_title, topic)
    
    def _calculate_image_relevance_keywords(self, img_url: str, img_alt: str, section_title: str, topic: str) -> float:
        """Fallback keyword-based relevance calculation."""
        score = 0.0
        
        # Extract keywords from section title and topic
        section_keywords = set(section_title.lower().split())
        topic_keywords = set(topic.lower().split())
        all_keywords = section_keywords.union(topic_keywords)
        
        # Check URL for relevant keywords
        url_lower = img_url.lower()
        for keyword in all_keywords:
            if len(keyword) > 3 and keyword in url_lower:
                score += 2.0
        
        # Check alt text for relevant keywords
        if img_alt:
            for keyword in all_keywords:
                if len(keyword) > 3 and keyword in img_alt.lower():
                    score += 3.0
        
        # Boost score for common image types that are usually relevant
        image_type_keywords = ['diagram', 'chart', 'graph', 'illustration', 'infographic', 'visualization', 
                              'architecture', 'flow', 'process', 'workflow', 'comparison', 'analysis']
        for keyword in image_type_keywords:
            if keyword in url_lower or (img_alt and keyword in img_alt.lower()):
                score += 1.5
        
        # Normalize to 0-10 scale (rough approximation)
        return min(10.0, score)
    
    def _create_short_image_description(self, section_title: str, topic: str, full_description: str = "") -> str:
        """Create a concise 2-line image description from the full description."""
        # Extract key information: what type of image and what it should show
        if not full_description:
            return f"Visual illustration or diagram related to {section_title} in the context of {topic}"
        
        # Try to extract the first 2 sentences or create a summary
        sentences = full_description.split('. ')
        if len(sentences) >= 2:
            # Take first 2 sentences
            short_desc = '. '.join(sentences[:2])
            if not short_desc.endswith('.'):
                short_desc += '.'
            return short_desc
        elif len(sentences) == 1:
            # If only one sentence, try to split it or use first part
            words = full_description.split()
            if len(words) > 30:
                # Take first 30 words
                short_desc = ' '.join(words[:30])
                if not short_desc.endswith('.'):
                    short_desc += '...'
                return short_desc
            else:
                return full_description
        else:
            # Fallback
            return f"Visual illustration or diagram related to {section_title} in the context of {topic}"
    
    def _fetch_wikimedia_image(self, image_description: str, topic: str) -> Optional[str]:
        """Fetch a technical diagram from Wikimedia Commons API."""
        try:
            # Build search query for technical topics
            search_query = f"{topic} {image_description}".strip()[:100]
            print(f"      🔎 Wikimedia Commons search query: '{search_query}'")
            
            # Wikimedia Commons API endpoint (no API key required)
            url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": search_query,
                "srnamespace": 6,  # File namespace (images)
                "srlimit": 5,
                "srprop": "size|timestamp"
            }
            
            # Handle SSL verification
            ssl_verify = os.getenv("SSL_VERIFY", "true").lower() == "true"
            if not ssl_verify:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                os.environ["REQUESTS_CA_BUNDLE"] = ""
                os.environ["CURL_CA_BUNDLE"] = ""
                os.environ["PYTHONHTTPSVERIFY"] = "0"
            
            # Make API request
            response = requests.get(url, params=params, timeout=10, verify=ssl_verify)
            
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                
                if search_results:
                    print(f"      📊 Found {len(search_results)} result(s) in Wikimedia Commons:")
                    for idx, result in enumerate(search_results[:5], 1):
                        file_title = result.get("title", "")
                        size = result.get("size", 0)
                        print(f"         {idx}. {file_title[:70]}... (size: {size} bytes)")
                    
                    # Get the first result
                    file_title = search_results[0].get("title", "")
                    print(f"      🔗 Fetching URL for: {file_title[:70]}...")
                    
                    # Get image URL for this file
                    image_url = self._get_wikimedia_file_url(file_title, ssl_verify)
                    
                    if image_url:
                        print(f"      ✅ Retrieved image URL: {image_url[:80]}...")
                        return image_url
                    else:
                        print(f"      ⚠️  Could not retrieve image URL for file")
                else:
                    print(f"      ℹ️  No results found in Wikimedia Commons")
            else:
                print(f"      ⚠️  Wikimedia Commons API returned status {response.status_code}")
            
            return None
            
        except Exception as e:
            print(f"      ❌ Wikimedia Commons API error: {e}")
            return None
        finally:
            # Clean up env vars if we disabled verification
            if not os.getenv("SSL_VERIFY", "true").lower() == "true":
                for var in ["REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "PYTHONHTTPSVERIFY"]:
                    if var in os.environ:
                        del os.environ[var]
    
    def _get_wikimedia_file_url(self, file_title: str, ssl_verify: bool) -> Optional[str]:
        """Get the direct image URL for a Wikimedia Commons file."""
        try:
            url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "titles": file_title,
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": 800  # Prefer 800px width
            }
            
            response = requests.get(url, params=params, timeout=10, verify=ssl_verify)
            
            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                
                for page_id, page_data in pages.items():
                    imageinfo = page_data.get("imageinfo", [])
                    if imageinfo:
                        # Get the URL (prefer thumbnail if available, otherwise original)
                        image_url = imageinfo[0].get("thumburl") or imageinfo[0].get("url")
                        if image_url:
                            url_type = "thumbnail" if imageinfo[0].get("thumburl") else "original"
                            print(f"         ✅ Retrieved {url_type} URL")
                            return image_url
                    else:
                        print(f"         ⚠️  No imageinfo found for file")
            
            return None
        except Exception as e:
            print(f"         ❌ Error retrieving file URL: {e}")
            return None
    
    def _get_image_description(self, section_title: str, topic: str, section_content: str = "") -> str:
        """Generate detailed image description using LLM based on section context."""
        # Truncate section content to avoid token limits (keep first 1000 words)
        content_preview = " ".join(section_content.split()[:1000]) if section_content else ""
        
        prompt = f"""Generate a detailed, specific image description for a blog post section.

Blog Topic: {topic}
Section Title: {section_title}
Section Content Preview: {content_preview[:2000] if content_preview else "No content preview available"}

Requirements:
1. Create a detailed description (2-4 sentences) of what image would best support this section
2. Explain what the image should show, including key visual elements
3. Describe why this image is relevant to the section content
4. Specify what type of visualization would be most helpful (diagram, chart, flowchart, illustration, etc.)
5. Include specific details about what should be visible in the image based on the section content
6. Make it actionable - someone should be able to find or create an appropriate image based on this description

The description should be professional, specific, and contextual to the section content. Focus on what would help readers better understand the concepts discussed in this section.

Generate ONLY the image description text, nothing else."""
        
        try:
            description = self.call_llm(prompt).strip()
            # Clean up any markdown or formatting that LLM might add
            description = description.replace("**", "").replace("*", "").replace("#", "").strip()
            # Ensure it's not empty
            if not description or len(description) < 20:
                # Fallback to a basic description
                return f"Visual illustration or diagram related to {section_title} in the context of {topic}. The image should support and enhance the content of this section by providing visual context that helps readers better understand the concepts discussed."
            return description
        except Exception as e:
            print(f"      ⚠️  Error generating image description with LLM: {e}. Using fallback description.")
            # Fallback description
            return f"Visual illustration or diagram related to {section_title} in the context of {topic}. The image should support and enhance the content of this section by providing visual context that helps readers better understand the concepts discussed."
    
    def _get_short_alt_text(self, section_title: str, topic: str) -> str:
        """Generate short alt text for markdown image syntax."""
        title_lower = section_title.lower()
        
        # Short, descriptive alt text
        if "architecture" in title_lower or "structure" in title_lower:
            return f"{topic} Architecture Diagram"
        elif "mistake" in title_lower or "error" in title_lower or "problem" in title_lower:
            return f"Common {topic} Mistakes"
        elif "comparison" in title_lower or "versus" in title_lower or "vs" in title_lower:
            return f"{topic} Comparison Chart"
        elif "process" in title_lower or "workflow" in title_lower or "flow" in title_lower:
            return f"{topic} Process Flowchart"
        elif "configuration" in title_lower or "setup" in title_lower:
            return f"{topic} Configuration"
        elif "monitoring" in title_lower or "logging" in title_lower:
            return f"{topic} Monitoring Dashboard"
        elif "security" in title_lower:
            return f"{topic} Security"
        elif "performance" in title_lower or "optimization" in title_lower:
            return f"{topic} Performance Metrics"
        else:
            return f"{topic} - {section_title}"
    
    def _insert_image_in_section(self, content: str, image_markdown: str) -> str:
        """Insert image at appropriate location in section content."""
        lines = content.split("\n")
        
        # Find the best place to insert image
        # Strategy: After first substantial paragraph or after first subsection header
        
        insert_position = 0
        
        # Look for first H3 subsection header
        for i, line in enumerate(lines):
            if line.startswith("### "):
                insert_position = i + 1
                break
        
        # If no H3 found, insert after first substantial paragraph (3+ sentences)
        if insert_position == 0:
            paragraph_end = 0
            sentence_count = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith("#"):
                    # Count sentences (rough estimate)
                    sentence_count += line.count('.') + line.count('!') + line.count('?')
                    if sentence_count >= 3:
                        insert_position = i + 1
                        break
        
        # If still no good position, insert after first non-header line
        if insert_position == 0:
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith("#"):
                    insert_position = i + 1
                    break
        
        # Insert image
        lines.insert(insert_position, image_markdown)
        
        return "\n".join(lines)


