"""Example usage of the blog generator."""
from blog_generator import BlogGenerator

def main():
    """Example: Generate a blog post about enterprise AI adoption."""
    
    # Initialize the generator
    generator = BlogGenerator()
    
    # Generate a blog post
    result = generator.generate(
        topic="Enterprise AI Adoption: Strategies for Success",
        target_keywords=["AI", "enterprise", "artificial intelligence", "automation", "digital transformation"],
        custom_config={
            "tone": "professional",
            "word_count": 2000,
            "include_faq": True
        }
    )
    
    # Check results
    if result["status"] == "success":
        print("\n" + "="*60)
        print("Blog Generation Successful!")
        print("="*60)
        print(f"\nTopic: {result['metadata']['topic']}")
        print(f"Word Count: {result['metadata']['word_count']}")
        print(f"Sections: {result['metadata']['sections']}")
        print(f"Verification Score: {result['metadata']['verification_score']:.2%}")
        print(f"\nOutput saved to: {result['output_file']}")
        
        # Display SEO info
        seo = result['blog'].get('seo', {})
        if seo:
            print(f"\nSEO Meta Title: {seo.get('meta_title', 'N/A')}")
            print(f"Target Keywords: {', '.join(seo.get('target_keywords', []))}")
    else:
        print(f"\nError: {result.get('message', 'Unknown error')}")
        print(f"Failed at step: {result.get('step', 'unknown')}")

if __name__ == "__main__":
    main()



