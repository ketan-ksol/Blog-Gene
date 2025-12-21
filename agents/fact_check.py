"""Fact-check & Safety Agent: Validates claims and adds disclaimers."""
from typing import Dict, Any, List
from .base import BaseAgent
import re


class FactCheckAgent(BaseAgent):
    """Agent responsible for fact-checking and safety compliance."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fact-check content and add safety disclaimers.
        
        Input:
            - content: dict mapping section titles to content
            - fact_table: dict
            - citations: list
            - require_citations: bool
            - add_disclaimers: bool
            - disclaimer_types: list
            - topic: str
        
        Output:
            - verified_content: dict
            - flagged_claims: list
            - disclaimers: str
            - citation_status: dict
        """
        content = input_data.get("content", {})
        fact_table = input_data.get("fact_table", {})
        citations = input_data.get("citations", [])
        require_citations = input_data.get("require_citations", True)
        add_disclaimers = input_data.get("add_disclaimers", False)
        disclaimer_types = input_data.get("disclaimer_types", [])
        topic = input_data.get("topic", "")
        
        # Identify claims that need verification
        flagged_claims = self._identify_claims(content, fact_table)
        
        # Verify claims against sources
        citation_status = self._verify_claims(flagged_claims, fact_table, citations)
        
        # Add citation markers to content
        verified_content = self._add_citations(content, citation_status, require_citations)
        
        # Generate disclaimers if needed
        disclaimers = ""
        if add_disclaimers:
            disclaimers = self._generate_disclaimers(topic, disclaimer_types)
        
        return {
            "status": "success",
            "verified_content": verified_content,
            "flagged_claims": flagged_claims,
            "disclaimers": disclaimers,
            "citation_status": citation_status,
            "verification_score": self._calculate_verification_score(citation_status)
        }
    
    def _identify_claims(self, content: Dict[str, str], fact_table: Dict) -> List[Dict[str, Any]]:
        """Identify factual claims in content that need verification."""
        claims = []
        
        # Patterns that indicate factual claims
        claim_patterns = [
            r'\d+%',  # Statistics
            r'\d+\s+(million|billion|thousand)',  # Large numbers
            r'studies?\s+(show|indicate|suggest|prove)',  # Study references
            r'according\s+to',  # Attribution
            r'research\s+(shows|indicates)',  # Research claims
            r'data\s+(shows|indicates)',  # Data claims
        ]
        
        for section_title, section_content in content.items():
            for pattern in claim_patterns:
                matches = re.finditer(pattern, section_content, re.IGNORECASE)
                for match in matches:
                    # Extract context around the claim
                    start = max(0, match.start() - 50)
                    end = min(len(section_content), match.end() + 50)
                    context = section_content[start:end]
                    
                    claims.append({
                        "claim": match.group(),
                        "context": context,
                        "section": section_title,
                        "position": match.start(),
                        "needs_citation": True
                    })
        
        return claims
    
    def _verify_claims(self, claims: List[Dict], fact_table: Dict, citations: List[Dict]) -> Dict[str, Any]:
        """Verify claims against available sources."""
        citation_status = {}
        
        for claim in claims:
            claim_text = claim.get("claim", "")
            context = claim.get("context", "")
            
            # Check if claim matches any verified fact
            verified = False
            matching_sources = []
            
            for fact, fact_data in fact_table.items():
                if claim_text.lower() in fact.lower() or fact.lower() in context.lower():
                    if fact_data.get("verified", False):
                        verified = True
                        matching_sources = fact_data.get("sources", [])
                        break
            
            # If not found in fact table, check citations
            if not verified:
                for citation in citations:
                    citation_text = f"{citation.get('title', '')} {citation.get('content', '')}"
                    if claim_text.lower() in citation_text.lower():
                        verified = True
                        matching_sources.append({
                            "title": citation.get("title", ""),
                            "url": citation.get("url", "")
                        })
                        break
            
            citation_status[claim.get("claim", "")] = {
                "verified": verified,
                "sources": matching_sources[:3],
                "needs_citation": not verified and claim.get("needs_citation", True)
            }
        
        return citation_status
    
    def _add_citations(self, content: Dict[str, str], citation_status: Dict, require_citations: bool) -> Dict[str, str]:
        """Add citation markers to content."""
        verified_content = {}
        
        for section_title, section_content in content.items():
            # Find claims in this section
            section_claims = [
                claim for claim, status in citation_status.items()
                if status.get("needs_citation", False)
            ]
            
            if section_claims and require_citations:
                # Add citation note at the end of section
                citation_note = "\n\n*Note: Some claims in this section may require additional citations.*"
                section_content += citation_note
            
            verified_content[section_title] = section_content
        
        return verified_content
    
    def _generate_disclaimers(self, topic: str, disclaimer_types: List[str]) -> str:
        """Generate appropriate disclaimers based on topic and types."""
        if not disclaimer_types:
            return ""
        
        disclaimer_templates = {
            "medical": "**Medical Disclaimer**: This article is for informational purposes only and does not constitute medical advice. Consult a healthcare professional for medical concerns.",
            "legal": "**Legal Disclaimer**: This article is for informational purposes only and does not constitute legal advice. Consult a qualified attorney for legal matters.",
            "financial": "**Financial Disclaimer**: This article is for informational purposes only and does not constitute financial advice. Consult a financial advisor before making investment decisions.",
            "general": f"**Disclaimer**: The information in this article about {topic} is provided for informational purposes only. Always verify information and consult professionals when making important decisions."
        }
        
        disclaimers = []
        for dis_type in disclaimer_types:
            if dis_type.lower() in disclaimer_templates:
                disclaimers.append(disclaimer_templates[dis_type.lower()])
            else:
                disclaimers.append(disclaimer_templates["general"])
        
        return "\n\n".join(disclaimers)
    
    def _calculate_verification_score(self, citation_status: Dict) -> float:
        """Calculate overall verification score."""
        if not citation_status:
            return 1.0
        
        verified_count = sum(1 for status in citation_status.values() if status.get("verified", False))
        total_count = len(citation_status)
        
        return verified_count / total_count if total_count > 0 else 1.0


