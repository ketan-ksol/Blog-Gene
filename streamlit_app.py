"""Streamlit UI for Enterprise Blog Generator"""
import streamlit as st
import sys
import os
import time
import threading
from pathlib import Path
from datetime import datetime
import json
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from blog_generator import BlogGenerator
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="Enterprise Blog Generator",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
        background-color: #f0f2f6;
    }
    .step-complete {
        border-left-color: #28a745;
        background-color: #d4edda;
    }
    .step-error {
        border-left-color: #dc3545;
        background-color: #f8d7da;
    }
    .blog-preview {
        padding: 1.5rem;
        background-color: #ffffff;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'blog_result' not in st.session_state:
    st.session_state.blog_result = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = None
if 'step_messages' not in st.session_state:
    st.session_state.step_messages = []

# Custom stream handler to capture print statements
class StreamlitHandler:
    def __init__(self, container):
        self.container = container
        self.messages = []
    
    def write(self, text):
        if text.strip():
            self.messages.append(text)
            # Update the container with latest messages
            with self.container:
                for msg in self.messages[-20:]:  # Show last 20 messages
                    if "Step" in msg or "✓" in msg or "⚠️" in msg or "🔍" in msg or "📷" in msg or "✅" in msg:
                        st.text(msg)

# Header
st.markdown('<h1 class="main-header">✍️ Enterprise Blog Generator</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.1rem;">AI-powered blog creation with agentic workflow</p>', unsafe_allow_html=True)

# Load configuration
def load_config_values():
    """Load configuration from config.yaml and environment variables."""
    config_path = Path("config.yaml")
    default_config = {
        "tone": "professional",
        "reading_level": "college",
        "target_audience": "enterprise professionals",
        "min_word_count": 1000,
        "max_word_count": 1500,
        "sections_per_article": 5,
        "target_keywords": [],
        "include_faq": True,
        "include_meta_tags": True,
        "require_citations": True,
        "add_disclaimers": False,
        "disclaimer_types": [],
        "enable_web_search": True,
        "max_research_sources": 10,
        "fact_check_enabled": True,
        "model_name": "gpt-4o",
        "temperature": 0.7
    }
    
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f) or {}
                default_config.update(file_config)
        except Exception as e:
            st.sidebar.warning(f"Could not load config.yaml: {e}")
    
    # Override with environment variables if present
    if os.getenv("MODEL_NAME"):
        default_config["model_name"] = os.getenv("MODEL_NAME")
    if os.getenv("TEMPERATURE"):
        default_config["temperature"] = float(os.getenv("TEMPERATURE"))
    
    return default_config

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Load and display configuration values
    config = load_config_values()
    
    # Configuration display with expanders
    with st.expander("📝 Content Settings", expanded=True):
        st.markdown(f"**Tone:** `{config.get('tone', 'professional')}`")
        st.markdown(f"**Reading Level:** `{config.get('reading_level', 'college')}`")
        st.markdown(f"**Target Audience:** `{config.get('target_audience', 'enterprise professionals')}`")
        st.markdown(f"**Min Word Count:** `{config.get('min_word_count', 1000)}`")
        st.markdown(f"**Max Word Count:** `{config.get('max_word_count', 1500)}`")
        st.markdown(f"**Sections per Article:** `{config.get('sections_per_article', 5)}`")
    
    with st.expander("🔍 SEO Settings", expanded=False):
        st.markdown(f"**Include FAQ:** `{config.get('include_faq', True)}`")
        st.markdown(f"**Include Meta Tags:** `{config.get('include_meta_tags', True)}`")
        keywords = config.get('target_keywords', [])
        if keywords:
            st.markdown(f"**Target Keywords:** `{', '.join(keywords)}`")
        else:
            st.markdown(f"**Target Keywords:** `[]` (none)")
    
    with st.expander("🤖 Model Settings", expanded=False):
        st.markdown(f"**Model Name:** `{config.get('model_name', 'gpt-4o')}`")
        st.markdown(f"**Temperature:** `{config.get('temperature', 0.7)}`")
    
    with st.expander("🔒 Safety & Compliance", expanded=False):
        st.markdown(f"**Require Citations:** `{config.get('require_citations', True)}`")
        st.markdown(f"**Add Disclaimers:** `{config.get('add_disclaimers', False)}`")
        disclaimer_types = config.get('disclaimer_types', [])
        if disclaimer_types:
            st.markdown(f"**Disclaimer Types:** `{', '.join(disclaimer_types)}`")
        else:
            st.markdown(f"**Disclaimer Types:** `[]` (none)")
    
    with st.expander("🔬 Agent Settings", expanded=False):
        st.markdown(f"**Enable Web Search:** `{config.get('enable_web_search', True)}`")
        st.markdown(f"**Max Research Sources:** `{config.get('max_research_sources', 10)}`")
        st.markdown(f"**Fact Check Enabled:** `{config.get('fact_check_enabled', True)}`")
    
    st.divider()
    
    # Topic input
    topic = st.text_input(
        "Blog Topic",
        placeholder="e.g., AI Evolution in 2025",
        help="Enter the topic for your blog post"
    )
    
    # Optional keywords
    keywords_input = st.text_input(
        "SEO Keywords (optional)",
        placeholder="keyword1, keyword2, keyword3",
        help="Comma-separated keywords for SEO optimization"
    )
    
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()] if keywords_input else None
    
    # Generate button
    generate_button = st.button("🚀 Generate Blog", type="primary", use_container_width=True)
    
    st.divider()
    
    # Display current status
    if st.session_state.current_step:
        st.info(f"**Current Step:** {st.session_state.current_step}")
    
    if st.session_state.blog_result:
        st.success("✅ Blog Generated Successfully!")

# Main content area
if generate_button and topic:
    # Initialize generator
    with st.spinner("Initializing blog generator..."):
        generator = BlogGenerator()
    
    # Create containers for different sections
    progress_container = st.container()
    steps_container = st.container()
    result_container = st.container()
    
    with progress_container:
        st.header("📊 Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    with steps_container:
        st.header("🔄 Generation Steps")
        steps_display = st.empty()
    
    # Track steps
    steps = [
        ("Planning blog structure", "📋", "Step 1/6"),
        ("Conducting research", "🔍", "Step 2/6"),
        ("Writing content", "✍️", "Step 3/6"),
        ("Editing and refining", "✏️", "Step 4/6"),
        ("Optimizing for SEO", "🔎", "Step 5/6"),
        ("Fact-checking and safety review", "✅", "Step 6/6")
    ]
    
    # Create a placeholder for step-by-step updates
    step_placeholders = {}
    step_messages = {}  # Store messages for each step
    step_thoughts = {}  # Store AI thoughts for each step
    
    with steps_display.container():
        for i, (step_name, icon, step_label) in enumerate(steps):
            step_placeholders[i] = st.empty()
            step_messages[i] = []
            step_thoughts[i] = []
            # Initialize all steps as pending
            step_placeholders[i].markdown(f"""
                <div class="step-box">
                    <strong>{icon} {step_label}:</strong> {step_name}
                    <div style="margin-top: 0.5rem; color: #999; font-size: 0.9rem;">⏸️ Pending</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Generate blog with real-time updates
    try:
        import sys
        import re
        from io import StringIO
        
        # Track current step - use a list to allow modification in nested function
        step_state = {"current": -1, "completed": set()}
        
        # Map agent names to step indices
        agent_to_step = {
            "Planner": 0,
            "Research": 1,
            "Writer": 2,
            "Editor": 3,
            "SEO": 4,
            "FactCheck": 5
        }
        
        # Set up thought callback
        from agents.base import set_thought_callback
        def capture_thought(agent_name: str, thought: str):
            """Capture AI thoughts and associate with the current step."""
            step_idx = agent_to_step.get(agent_name, -1)
            if step_idx >= 0 and step_idx < len(steps):
                if step_idx not in step_thoughts:
                    step_thoughts[step_idx] = []
                step_thoughts[step_idx].append(thought)
                # Update the step display with thoughts
                _update_step_with_thoughts(step_idx)
        
        set_thought_callback(capture_thought)
        
        def _update_step_with_thoughts(step_idx: int):
            """Update step display to include AI thoughts."""
            import html
            step_name, icon, step_label = steps[step_idx]
            thoughts_html = ""
            if step_idx in step_thoughts and step_thoughts[step_idx]:
                latest_thought = step_thoughts[step_idx][-1]
                # Escape HTML in the thought text to prevent injection
                escaped_thought = html.escape(str(latest_thought))
                thoughts_html = f'<div class="ai-thinking"><div class="ai-thinking-label">🤔 AI Thinking:</div><div class="ai-thinking-text">{escaped_thought}</div></div>'
            
            if step_idx in step_state["completed"]:
                status_html = '<div style="margin-top: 0.5rem; color: #28a745; font-size: 0.9rem;">✓ Complete</div>'
            elif step_idx == step_state["current"]:
                status_html = '<div style="margin-top: 0.5rem; color: #856404; font-size: 0.9rem;">⏳ In progress...</div>'
            else:
                status_html = '<div style="margin-top: 0.5rem; color: #999; font-size: 0.9rem;">⏸️ Pending</div>'
            
            step_placeholders[step_idx].markdown(f"""
                <div class="step-box" style="{'border-left-color: #28a745; background-color: #d4edda;' if step_idx in step_state['completed'] else ('border-left-color: #ffc107; background-color: #fff3cd;' if step_idx == step_state['current'] else '')}">
                    <strong>{icon} {step_label}:</strong> {step_name}
                    {status_html}
                    {thoughts_html}
                </div>
            """, unsafe_allow_html=True)
        
        # Create a custom stream to capture print statements
        class StreamlitStream:
            def __init__(self, step_state_ref, step_placeholders_ref, steps_ref, progress_bar_ref, status_text_ref):
                self.buffer = []
                self.step_state = step_state_ref
                self.step_placeholders = step_placeholders_ref
                self.steps = steps_ref
                self.progress_bar = progress_bar_ref
                self.status_text = status_text_ref
            
            def write(self, text):
                try:
                    # Convert bytes to string if needed
                    if isinstance(text, bytes):
                        text = text.decode('utf-8', errors='ignore')
                    
                    # Convert to string if not already
                    text = str(text) if text else ""
                    
                    # Skip if empty after conversion
                    if not text or not text.strip():
                        return
                    
                    text = text.strip()
                    self.buffer.append(text)
                    # Parse step number from print statements
                    
                    # Check for step indicators - ensure text is string
                    if not isinstance(text, str):
                        return
                    try:
                        step_match = re.search(r'Step (\d+)/6', text)
                    except (TypeError, AttributeError):
                        return
                    if step_match:
                        step_num = int(step_match.group(1)) - 1  # Convert to 0-based index
                        if step_num < len(self.steps):
                            # Mark previous step as complete
                            if self.step_state["current"] >= 0 and self.step_state["current"] < step_num:
                                self.step_state["completed"].add(self.step_state["current"])
                            
                            self.step_state["current"] = step_num
                            # Update progress
                            progress = (step_num + 1) / len(self.steps)
                            self.progress_bar.progress(progress)
                            self.status_text.text(f"Step {step_num + 1}/{len(self.steps)}: {self.steps[step_num][0]}")
                            
                            # Update step displays
                            self._update_steps()
                    
                    # Check for completion indicators
                    if "✓" in text or "complete" in text.lower():
                        if self.step_state["current"] >= 0:
                            self.step_state["completed"].add(self.step_state["current"])
                            self._update_steps()
                except Exception:
                    # Silently ignore errors during shutdown or invalid input
                    pass
            
            def _update_steps(self):
                """Update all step displays based on current state"""
                import html
                for i, (step_name, icon, step_label) in enumerate(self.steps):
                    # Get thoughts for this step
                    thoughts_html = ""
                    if i in step_thoughts and step_thoughts[i]:
                        latest_thought = step_thoughts[i][-1]
                        # Escape HTML in the thought text to prevent injection
                        escaped_thought = html.escape(str(latest_thought))
                        thoughts_html = f'<div class="ai-thinking"><div class="ai-thinking-label">🤔 AI Thinking:</div><div class="ai-thinking-text">{escaped_thought}</div></div>'
                    
                    if i in self.step_state["completed"]:
                        # Step is complete
                        self.step_placeholders[i].markdown(f"""
                            <div class="step-box step-complete">
                                <strong>{icon} {step_label}:</strong> {step_name}
                                <div style="margin-top: 0.5rem; color: #28a745; font-size: 0.9rem;">✓ Complete</div>
                                {thoughts_html}
                            </div>
                        """, unsafe_allow_html=True)
                    elif i == self.step_state["current"]:
                        # Step is in progress
                        self.step_placeholders[i].markdown(f"""
                            <div class="step-box" style="border-left-color: #ffc107; background-color: #fff3cd;">
                                <strong>{icon} {step_label}:</strong> {step_name}
                                <div style="margin-top: 0.5rem; color: #856404; font-size: 0.9rem;">⏳ In progress...</div>
                                {thoughts_html}
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Step is pending
                        self.step_placeholders[i].markdown(f"""
                            <div class="step-box">
                                <strong>{icon} {step_label}:</strong> {step_name}
                                <div style="margin-top: 0.5rem; color: #999; font-size: 0.9rem;">⏸️ Pending</div>
                            </div>
                        """, unsafe_allow_html=True)
            
            def flush(self):
                pass
        
        # Set up thought callback before generation
        from agents.base import set_thought_callback
        set_thought_callback(capture_thought)
        
        # Redirect stdout to capture print statements
        old_stdout = sys.stdout
        stream_capture = StreamlitStream(step_state, step_placeholders, steps, progress_bar, status_text)
        sys.stdout = stream_capture
        
        try:
            # Generate blog (this will print step updates)
            # Note: Streamlit updates UI at script completion, so steps will update
            # when print statements are captured and processed
            result = generator.generate(
                topic=topic,
                target_keywords=keywords
            )
            
            # Mark all remaining steps as complete
            for i in range(len(steps)):
                if i not in step_state["completed"]:
                    step_state["completed"].add(i)
            
            # Final update of all steps
            stream_capture._update_steps()
            
            # Update final progress
            progress_bar.progress(1.0)
            status_text.text("✅ Blog generation complete!")
            
        finally:
            sys.stdout = old_stdout
            # Clear thought callback after generation
            set_thought_callback(None)
        
        # Update final progress
        progress_bar.progress(1.0)
        status_text.text("✅ Blog generation complete!")
        
        # Store result
        st.session_state.blog_result = result
        
        # Display result
        with result_container:
            st.header("📄 Generated Blog")
            
            if result.get("status") == "success":
                blog = result.get("blog", {})
                metadata = result.get("metadata", {})
                
                # Display metadata
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Word Count", metadata.get("word_count", 0))
                with col2:
                    st.metric("Sections", metadata.get("sections", 0))
                with col3:
                    st.metric("Verification Score", f"{metadata.get('verification_score', 0):.1%}")
                with col4:
                    st.metric("Output File", "✅ Saved")
                
                st.divider()
                
                # Display blog content
                st.subheader(blog.get("title", "Blog Post"))
                
                # Display meta description if available
                seo_data = blog.get("seo", {})
                if seo_data.get("meta_description"):
                    st.info(f"**Meta Description:** {seo_data.get('meta_description')}")
                
                # Display sections
                sections = blog.get("sections", [])
                for section in sections:
                    section_title = section.get("title", "")
                    section_content = section.get("content", "")
                    
                    # Skip empty sections
                    if not section_content or not section_title:
                        continue
                    
                    # Skip planning metadata sections
                    if section_title in ["Thesis", "Angle"]:
                        continue
                    
                    # Remove heading from content if it matches section title (to avoid duplication)
                    content_lines = section_content.split("\n")
                    cleaned_content = []
                    for line in content_lines:
                        # Skip lines that are exactly the section heading
                        if line.strip() == f"## {section_title}":
                            continue
                        # Skip if it's just the heading with extra spaces
                        if line.strip().replace(" ", "") == f"##{section_title}":
                            continue
                        cleaned_content.append(line)
                    
                    cleaned_content_text = "\n".join(cleaned_content).strip()
                    
                    # Only display if there's content after cleaning
                    if cleaned_content_text:
                        st.markdown(f"## {section_title}")
                        st.markdown(cleaned_content_text)
                        st.divider()
                
                # Display references if available
                citations = blog.get("citations", [])
                if citations:
                    st.markdown("## References")
                    for i, citation in enumerate(citations[:10], 1):
                        title = citation.get("title", "Unknown")
                        url = citation.get("url", "")
                        st.markdown(f"{i}. [{title}]({url})")
                
                # Download buttons
                st.divider()
                col1, col2 = st.columns(2)
                
                with col1:
                    # Download markdown
                    output_file = result.get("output_file", "")
                    if output_file and Path(output_file).exists():
                        with open(output_file, 'r', encoding='utf-8') as f:
                            md_content = f.read()
                        st.download_button(
                            label="📥 Download Markdown",
                            data=md_content,
                            file_name=Path(output_file).name,
                            mime="text/markdown"
                        )
                
                with col2:
                    # Download JSON
                    json_file = output_file.replace('.md', '.json')
                    if json_file and Path(json_file).exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_content = f.read()
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_content,
                            file_name=Path(json_file).name,
                            mime="application/json"
                        )
                
            else:
                st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
                if result.get("step"):
                    st.warning(f"Failed at step: {result.get('step')}")
    
    except Exception as e:
        st.error(f"❌ Error generating blog: {str(e)}")
        st.exception(e)

elif generate_button and not topic:
    st.warning("⚠️ Please enter a blog topic")

# Display previous result if available
elif st.session_state.blog_result:
    result = st.session_state.blog_result
    
    with st.container():
        st.header("📄 Previous Blog Result")
        
        if result.get("status") == "success":
            blog = result.get("blog", {})
            metadata = result.get("metadata", {})
            
            # Display metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Word Count", metadata.get("word_count", 0))
            with col2:
                st.metric("Sections", metadata.get("sections", 0))
            with col3:
                st.metric("Verification Score", f"{metadata.get('verification_score', 0):.1%}")
            
            st.info("💡 Enter a new topic and click 'Generate Blog' to create another blog post.")

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Enterprise Blog Generator | AI-powered content creation</p>
    </div>
""", unsafe_allow_html=True)

