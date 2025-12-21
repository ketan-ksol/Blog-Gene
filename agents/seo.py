"""SEO Agent: Optimizes content for search engines."""
from typing import Dict, Any, List
from .base import BaseAgent
import re


class SEOAgent(BaseAgent):
    """Agent responsible for SEO optimization."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize content for SEO.
        
        Input:
            - content: dict mapping section titles to content
            - topic: str
            - target_keywords: list (optional)
            - include_faq: bool
            - include_meta_tags: bool
        
        Output:
            - optimized_content: dict
            - meta_title: str
            - meta_description: str
            - faq_section: str
            - internal_link_suggestions: list
            - keyword_density: dict
        """
        content = input_data.get("content", {})
        topic = input_data.get("topic", "")
        target_keywords = input_data.get("target_keywords", [])
        include_faq = input_data.get("include_faq", True)
        include_meta_tags = input_data.get("include_meta_tags", True)
        
        # Extract keywords if not provided
        if not target_keywords:
            target_keywords = self._extract_keywords(topic, content)
        
        # Optimize H1/H2 structure
        optimized_content = self._optimize_headings(content, target_keywords)
        
        # Improve keyword placement
        optimized_content = self._optimize_keyword_placement(optimized_content, target_keywords)
        
        # Generate meta tags
        meta_title = ""
        meta_description = ""
        if include_meta_tags:
            meta_title = self._generate_meta_title(topic, target_keywords)
            meta_description = self._generate_meta_description(topic, content, target_keywords)
        
        # Generate FAQ section
        faq_section = ""
        if include_faq:
            faq_section = self._generate_faq(topic, content, target_keywords)
        
        # Suggest internal links
        internal_link_suggestions = self._suggest_internal_links(content, topic)
        
        # Calculate keyword density
        keyword_density = self._calculate_keyword_density(optimized_content, target_keywords)
        
        return {
            "status": "success",
            "optimized_content": optimized_content,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "faq_section": faq_section,
            "internal_link_suggestions": internal_link_suggestions,
            "keyword_density": keyword_density,
            "target_keywords": target_keywords
        }
    
    def _extract_keywords(self, topic: str, content: Dict[str, str]) -> List[str]:
        """Extract relevant keywords from topic and content."""
        # Basic keyword extraction
        keywords = [topic]
        
        # Extract from content
        full_text = " ".join(content.values()).lower()
        words = re.findall(r'\b\w{4,}\b', full_text)
        
        # Simple frequency-based extraction (can be improved)
        from collections import Counter
        common_words = Counter(words).most_common(10)
        keywords.extend([word for word, count in common_words if count > 2])
        
        return list(set(keywords))[:5]  # Top 5 unique keywords
    
    def _optimize_headings(self, content: Dict[str, str], keywords: List[str]) -> Dict[str, str]:
        """Optimize H1/H2 structure with keywords."""
        optimized = {}
        
        for section_title, section_content in content.items():
            # Ensure H2 headings include keywords naturally
            optimized_title = self._optimize_heading(section_title, keywords)
            
            # Ensure content has proper heading structure
            if not section_content.startswith("##"):
                section_content = f"## {optimized_title}\n\n{section_content}"
            
            optimized[optimized_title] = section_content
        
        return optimized
    
    def _optimize_heading(self, heading: str, keywords: List[str]) -> str:
        """Optimize a single heading with keywords."""
        heading_lower = heading.lower()
        
        # Check if heading already contains keywords
        for keyword in keywords:
            if keyword.lower() not in heading_lower:
                # Try to naturally incorporate keyword
                if len(heading) < 60:  # Keep headings concise
                    # Simple optimization: add keyword if it fits naturally
                    pass  # For now, keep original heading
        
        return heading
    
    def _optimize_keyword_placement(self, content: Dict[str, str], keywords: List[str]) -> Dict[str, str]:
        """Optimize keyword placement throughout content."""
        optimized = {}
        
        for section_title, section_content in content.items():
            # Ensure keywords appear naturally in first paragraph
            optimized_content = self._ensure_keyword_in_intro(section_content, keywords)
            optimized[section_title] = optimized_content
        
        return optimized
    
    def _ensure_keyword_in_intro(self, content: str, keywords: List[str]) -> str:
        """Ensure at least one keyword appears in the first paragraph."""
        if not content:
            return content
        
        paragraphs = content.split("\n\n")
        if not paragraphs:
            return content
        
        first_para = paragraphs[0].lower()
        has_keyword = any(keyword.lower() in first_para for keyword in keywords)
        
        if not has_keyword and keywords:
            # Add keyword naturally to first paragraph
            primary_keyword = keywords[0]
            # Simple approach: prepend if it makes sense
            # In production, use LLM to rewrite naturally
            pass  # Keep original for now
        
        return content
    
    def _generate_meta_title(self, topic: str, keywords: List[str]) -> str:
        """Generate SEO-optimized meta title."""
        prompt = f"""Generate an SEO-optimized meta title for a blog post.

Topic: {topic}
Target Keywords: {', '.join(keywords)}

Requirements:
- 50-60 characters
- Include primary keyword naturally
- Compelling and click-worthy
- Clear value proposition

Return only the title, no quotes or extra text."""
        
        title = self.call_llm(prompt).strip()
        # Remove quotes if present
        title = title.strip('"\'')
        # Ensure length
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title
    
    def _generate_meta_description(self, topic: str, content: Dict[str, str], keywords: List[str]) -> str:
        """Generate SEO-optimized meta description."""
        # Extract summary from content
        summary = self._extract_summary(content)
        
        prompt = f"""Generate an SEO-optimized meta description for a blog post.

Topic: {topic}
Content Summary: {summary[:200]}
Target Keywords: {', '.join(keywords)}

Requirements:
- 150-160 characters
- Include primary keyword
- Compelling call to action
- Clear value proposition
- Encourage clicks

Return only the description, no quotes or extra text."""
        
        description = self.call_llm(prompt).strip()
        # Remove quotes if present
        description = description.strip('"\'')
        # Ensure length
        if len(description) > 160:
            description = description[:157] + "..."
        
        return description
    
    def _extract_summary(self, content: Dict[str, str]) -> str:
        """Extract a summary from content."""
        # Get introduction or first section
        intro = content.get("Introduction", "")
        if not intro:
            intro = list(content.values())[0] if content else ""
        
        # Get first 300 words
        words = intro.split()[:300]
        return " ".join(words)
    
    def _generate_faq(self, topic: str, content: Dict[str, str], keywords: List[str]) -> str:
        """Generate FAQ section."""
        prompt = f"""Generate exactly 5 relevant FAQ questions and answers for a blog post.

Topic: {topic}
Content Summary: {self._extract_summary(content)[:500]}
Target Keywords: {', '.join(keywords)}

Requirements:
- Generate EXACTLY 5 questions (no more, no less)
- Questions should be natural and search-friendly, specifically about {topic}
- Answers should be concise (50-100 words each) and focused on {topic}
- Cover common questions specifically about {topic}, not general questions
- Include target keywords naturally
- Format as markdown with ## FAQ section and Q/A pairs using ### for questions
- Focus on {topic} - avoid generic FAQ answers

Return the FAQ section in markdown format with exactly 5 Q/A pairs."""
        
        return self.call_llm(prompt)
    
    def _suggest_internal_links(self, content: Dict[str, str], topic: str) -> List[Dict[str, str]]:
        """Suggest internal linking opportunities."""
        suggestions = []
        
        # Analyze content for linkable phrases
        full_text = " ".join(content.values())
        
        # Simple approach: suggest linking key terms
        # In production, this would analyze existing content library
        key_terms = self._extract_key_terms(full_text)
        
        for term in key_terms[:5]:
            suggestions.append({
                "anchor_text": term,
                "suggested_link": f"/blog/{term.lower().replace(' ', '-')}",
                "context": "Related topic that could benefit from internal linking"
            })
        
        return suggestions
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms that could be linked."""
        # Simple extraction - in production, use NLP
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(words))[:10]
    
    def _calculate_keyword_density(self, content: Dict[str, str], keywords: List[str]) -> Dict[str, float]:
        """Calculate keyword density for each keyword."""
        full_text = " ".join(content.values()).lower()
        total_words = len(full_text.split())
        
        density = {}
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = full_text.count(keyword_lower)
            density[keyword] = (count / total_words * 100) if total_words > 0 else 0
        
        return density



