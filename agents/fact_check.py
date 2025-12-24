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
        from agents.base import _thought_callback
        import time
        
        content = input_data.get("content", {})
        section_count = len(content) if isinstance(content, dict) else 0
        
        if _thought_callback:
            _thought_callback("FactCheck", f"Starting fact-check: Scanning {section_count} sections for claims requiring verification...")
            time.sleep(0.3)
            _thought_callback("FactCheck", f"Cross-referencing claims with research citations and verifying accuracy...")
            time.sleep(0.3)
            _thought_callback("FactCheck", f"Adding citation markers and safety disclaimers where needed...")
        
        content = input_data.get("content", {})
        fact_table = input_data.get("fact_table", {})
        citations = input_data.get("citations", [])
        require_citations = input_data.get("require_citations", True)
        add_disclaimers = input_data.get("add_disclaimers", False)
        disclaimer_types = input_data.get("disclaimer_types", [])
        topic = input_data.get("topic", "")
        
        # Identify claims that need verification
        if _thought_callback:
            _thought_callback("FactCheck", f"Scanning {section_count} sections for factual claims requiring verification...")
            time.sleep(0.3)
        flagged_claims = self._identify_claims(content, fact_table)
        
        # Verify claims against sources
        if _thought_callback:
            _thought_callback("FactCheck", f"Cross-referencing {len(flagged_claims)} claims with research citations...")
            time.sleep(0.3)
        citation_status = self._verify_claims(flagged_claims, fact_table, citations)
        
        # Add citation markers to content
        if _thought_callback:
            _thought_callback("FactCheck", "Adding citation markers to verified claims...")
            time.sleep(0.2)
        verified_content = self._add_citations(content, citation_status, require_citations)
        
        # Generate disclaimers if needed
        disclaimers = ""
        if add_disclaimers:
            if _thought_callback:
                _thought_callback("FactCheck", "Generating safety disclaimers...")
            disclaimers = self._generate_disclaimers(topic, disclaimer_types)
        
        verification_score = self._calculate_verification_score(citation_status)
        if _thought_callback:
            _thought_callback("FactCheck", f"Fact-checking complete! Verification score: {verification_score:.0%}")
        
        return {
            "status": "success",
            "verified_content": verified_content,
            "flagged_claims": flagged_claims,
            "disclaimers": disclaimers,
            "citation_status": citation_status,
            "verification_score": verification_score
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
            section = claim.get("section", "")
            
            # Check if claim matches any verified fact
            verified = False
            matching_sources = []
            
            # First check fact_table
            for fact, fact_data in fact_table.items():
                fact_lower = fact.lower()
                claim_lower = claim_text.lower()
                context_lower = context.lower()
                
                # More flexible matching
                if (claim_lower in fact_lower or 
                    fact_lower in context_lower or
                    any(word in fact_lower for word in claim_lower.split() if len(word) > 2)):
                    if fact_data.get("verified", False):
                        verified = True
                        matching_sources = fact_data.get("sources", [])
                        break
            
            # If not found in fact table, check citations with better matching
            if not verified:
                for citation in citations:
                    citation_text = f"{citation.get('title', '')} {citation.get('content', '')}".lower()
                    citation_lower = citation_text.lower()
                    
                    # Extract key terms from claim and context
                    claim_terms = set(claim_text.lower().split())
                    context_terms = set(context.lower().split()[:20])  # First 20 words
                    all_terms = claim_terms | context_terms
                    
                    # Remove common words
                    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
                    relevant_terms = {t for t in all_terms if len(t) > 2 and t not in common_words}
                    
                    # Check if citation contains relevant terms and claim
                    term_matches = sum(1 for term in relevant_terms if term in citation_lower)
                    
                    # For percentage/numeric claims, check if citation mentions related concepts
                    if '%' in claim_text or any(char.isdigit() for char in claim_text):
                        # Extract context keywords (what the percentage is about)
                        # Extract relevant keywords from context dynamically
                        context_words = context_lower.split()
                        # Filter out common words and keep meaningful terms
                        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their'}
                        context_keywords = [w for w in context_words if len(w) > 3 and w not in common_words][:10]  # Top 10 relevant words
                        
                        # Check if citation contains the claim number OR context keywords
                        citation_has_number = any(char.isdigit() for char in citation_text)  # Citation has some numbers
                        keyword_matches = sum(1 for kw in context_keywords if kw in citation_lower)
                        
                        if (claim_text in citation_text or  # Exact match
                            (citation_has_number and keyword_matches >= 2) or  # Has numbers + relevant keywords
                            term_matches >= 2 or  # At least 2 relevant terms match
                            (len(context_keywords) > 0 and keyword_matches >= len(context_keywords) * 0.5)):  # 50% keyword match
                            verified = True
                            matching_sources.append({
                                "title": citation.get("title", ""),
                                "url": citation.get("url", "")
                            })
                            break
                    else:
                        # For non-numeric claims, check for phrase matches
                        if (claim_text.lower() in citation_lower or
                            term_matches >= 3 or  # At least 3 relevant terms
                            (len(relevant_terms) > 0 and term_matches / len(relevant_terms) >= 0.4)):  # 40% term match
                            verified = True
                            matching_sources.append({
                                "title": citation.get("title", ""),
                                "url": citation.get("url", "")
                            })
                            break
            
            # If still not verified, use LLM to check if citations support the claim
            if not verified and citations and len(claims) <= 5:  # Only for reasonable number of claims
                verified, sources = self._llm_verify_claim(claim_text, context, citations[:5], section)
                if verified:
                    matching_sources = sources
            
            citation_status[claim.get("claim", "")] = {
                "verified": verified,
                "sources": matching_sources[:3],
                "needs_citation": not verified and claim.get("needs_citation", True)
            }
        
        return citation_status
    
    def _llm_verify_claim(self, claim: str, context: str, citations: List[Dict], section: str):
        """Use LLM to verify if citations support the claim."""
        try:
            citations_text = "\n".join([
                f"{i+1}. {c.get('title', '')}: {c.get('content', '')[:300]}"
                for i, c in enumerate(citations)
            ])
            
            prompt = f"""Check if any of the following citations support or verify this claim:

Claim: {claim}
Context: {context}
Section: {section}

Citations:
{citations_text}

Respond with ONLY "YES" or "NO" followed by the citation number(s) that support the claim (e.g., "YES 1,3" or "NO").
If the claim is a statistic or percentage, check if the citations mention similar numbers or support the general claim even if not exact."""
            
            response = self.call_llm(prompt).strip().upper()
            
            if response.startswith("YES"):
                # Extract citation numbers
                parts = response.split()
                citation_nums = []
                for part in parts[1:]:
                    try:
                        num = int(part.replace(',', ''))
                        if 1 <= num <= len(citations):
                            citation_nums.append(num - 1)  # Convert to 0-based index
                    except ValueError:
                        pass
                
                if citation_nums:
                    sources = [{
                        "title": citations[i].get("title", ""),
                        "url": citations[i].get("url", "")
                    } for i in citation_nums]
                    return True, sources
            
            return False, []
        except Exception as e:
            # If LLM verification fails, return False
            return False, []
    
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


