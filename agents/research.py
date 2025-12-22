"""Research Agent: Gathers facts, statistics, and citations."""
import os
from typing import Dict, Any, List, Optional
from .base import BaseAgent

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


class ResearchAgent(BaseAgent):
    """Agent responsible for gathering research and citations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tavily_client = None
        self.ssl_verify = os.getenv("SSL_VERIFY", "true").lower() != "false"
        
        # Configure SSL verification for requests/httpx used by Tavily
        if not self.ssl_verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Set environment variables that requests/httpx will respect
            os.environ['PYTHONHTTPSVERIFY'] = '0'
            os.environ['CURL_CA_BUNDLE'] = ''
            os.environ['REQUESTS_CA_BUNDLE'] = ''
        
        if TAVILY_AVAILABLE and os.getenv("TAVILY_API_KEY"):
            try:
                self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            except Exception as e:
                print(f"Warning: Could not initialize Tavily client: {e}")
                pass
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from agents.base import _thought_callback
        
        topic = input_data.get("topic", "")
        if _thought_callback:
            _thought_callback("Research", f"Gathering research for '{topic}': Searching web sources, analyzing citations, and matching facts to references...")
        """
        Conduct research based on search queries and required facts.
        
        Input:
            - search_queries: list of search queries
            - required_facts: list of facts to find
            - topic: str
            - max_sources: int (optional)
        
        Output:
            - citations: list of citation objects
            - fact_table: dict mapping facts to sources
            - research_summary: str
        """
        search_queries = input_data.get("search_queries", [])
        required_facts = input_data.get("required_facts", [])
        topic = input_data.get("topic", "")
        max_sources = input_data.get("max_sources", 10)
        
        citations = []
        fact_table = {}
        
        # Perform web searches
        if self.tavily_client and input_data.get("enable_web_search", True):
            # Handle SSL verification for Tavily API calls
            if not self.ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            for query in search_queries[:5]:  # Limit to 5 queries
                try:
                    # Temporarily disable SSL verification for this request if needed
                    if not self.ssl_verify:
                        import requests
                        import contextlib
                        
                        # Create a context manager to temporarily patch requests
                        @contextlib.contextmanager
                        def no_ssl_verification():
                            original_request = requests.Session.request
                            def patched_request(self, *args, **kwargs):
                                kwargs['verify'] = False
                                return original_request(self, *args, **kwargs)
                            requests.Session.request = patched_request
                            try:
                                yield
                            finally:
                                requests.Session.request = original_request
                        
                        with no_ssl_verification():
                            results = self.tavily_client.search(
                                query=query,
                                max_results=min(3, max_sources // len(search_queries) + 1)
                            )
                    else:
                        results = self.tavily_client.search(
                            query=query,
                            max_results=min(3, max_sources // len(search_queries) + 1)
                        )
                    
                    for result in results.get("results", []):
                        citation = {
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "content": result.get("content", ""),
                            "relevance_score": result.get("score", 0)
                        }
                        citations.append(citation)
                except Exception as e:
                    error_msg = str(e).lower()
                    if "ssl" in error_msg or "certificate" in error_msg:
                        print(f"⚠️  SSL error for query '{query}'. Web search may be disabled.")
                        print(f"   Ensure SSL_VERIFY=false is set in .env file")
                    else:
                        print(f"Search error for query '{query}': {e}")
        
        # Check local sources directory
        local_sources = self._load_local_sources(topic)
        citations.extend(local_sources)
        
        # Match facts to sources
        fact_table = self._match_facts_to_sources(required_facts, citations)
        
        # Generate research summary
        research_summary = self._generate_research_summary(citations, fact_table, topic)
        
        return {
            "status": "success",
            "citations": citations[:max_sources],
            "fact_table": fact_table,
            "research_summary": research_summary,
            "sources_count": len(citations)
        }
    
    def _load_local_sources(self, topic: str) -> List[Dict[str, Any]]:
        """Load sources from local sources directory."""
        sources = []
        sources_dir = os.getenv("SOURCES_DIR", "./sources")
        
        if os.path.exists(sources_dir):
            import glob
            for file_path in glob.glob(os.path.join(sources_dir, "**/*.txt"), recursive=True):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        sources.append({
                            "title": os.path.basename(file_path),
                            "url": f"file://{file_path}",
                            "content": content[:500],  # First 500 chars
                            "relevance_score": 0.5
                        })
                except Exception:
                    pass
        
        return sources
    
    def _match_facts_to_sources(self, required_facts: List[Dict], citations: List[Dict]) -> Dict[str, Any]:
        """Match required facts to relevant sources."""
        fact_table = {}
        
        for fact_obj in required_facts:
            fact_text = fact_obj.get("fact", "")
            fact_type = fact_obj.get("type", "general")
            
            # Find relevant citations
            relevant_sources = []
            for citation in citations:
                citation_text = f"{citation.get('title', '')} {citation.get('content', '')}"
                if fact_text.lower() in citation_text.lower() or fact_type in citation_text.lower():
                    relevant_sources.append({
                        "url": citation.get("url", ""),
                        "title": citation.get("title", ""),
                        "excerpt": citation.get("content", "")[:200]
                    })
            
            fact_table[fact_text] = {
                "type": fact_type,
                "sources": relevant_sources[:3],  # Top 3 sources
                "verified": len(relevant_sources) > 0
            }
        
        return fact_table
    
    def _generate_research_summary(self, citations: List[Dict], fact_table: Dict, topic: str) -> str:
        """Generate a summary of the research findings."""
        prompt = f"""Summarize the research findings for a blog post about: {topic}

Citations found: {len(citations)}
Facts verified: {sum(1 for f in fact_table.values() if f.get('verified'))} / {len(fact_table)}

Key findings:
{self._format_citations_for_summary(citations[:5])}

Provide a concise research summary (2-3 paragraphs) highlighting:
1. Key statistics and data points discovered
2. Authoritative sources found
3. Gaps in information (if any)
"""
        
        return self.call_llm(prompt)
    
    def _format_citations_for_summary(self, citations: List[Dict]) -> str:
        """Format citations for the summary prompt."""
        formatted = []
        for i, citation in enumerate(citations, 1):
            formatted.append(f"{i}. {citation.get('title', 'Unknown')} - {citation.get('url', '')}")
        return "\n".join(formatted)



