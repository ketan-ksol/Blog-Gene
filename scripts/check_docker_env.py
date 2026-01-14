"""Script to check if environment variables are properly set for Docker."""
import os
from dotenv import load_dotenv

print("=" * 60)
print("Docker Environment Variables Check")
print("=" * 60)
print()

# Load .env file
load_dotenv()

# Check if .env file exists
env_file_exists = os.path.exists(".env")
print(f"📄 .env file exists: {'✅ Yes' if env_file_exists else '❌ No'}")
print()

# Check required variables
print("🔍 Checking Environment Variables:")
print()

# OpenAI API Key
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print(f"✅ OPENAI_API_KEY: Found (length: {len(openai_key)}, starts with: {openai_key[:3]}...)")
else:
    print("❌ OPENAI_API_KEY: NOT FOUND")

# Tavily API Key
tavily_key = os.getenv("TAVILY_API_KEY")
if tavily_key:
    print(f"✅ TAVILY_API_KEY: Found (length: {len(tavily_key)}, starts with: {tavily_key[:5]}...)")
else:
    print("❌ TAVILY_API_KEY: NOT FOUND")
    print("   ⚠️  This is why you're getting 0 sources!")

# SSL Verify
ssl_verify = os.getenv("SSL_VERIFY", "true")
print(f"ℹ️  SSL_VERIFY: {ssl_verify}")

print()
print("=" * 60)
print("Docker Compose Configuration Check")
print("=" * 60)
print()

# Check docker-compose.yml syntax
print("📋 docker-compose.yml uses:")
print("   - OPENAI_API_KEY=${OPENAI_API_KEY}")
print("   - TAVILY_API_KEY=${TAVILY_API_KEY:-}")
print()
print("💡 This means:")
print("   • Docker Compose will read .env file from the same directory")
print("   • If TAVILY_API_KEY is not in .env, it will be empty string")
print("   • Empty string = False in Python, so Tavily won't initialize")
print()

if not tavily_key:
    print("🔧 SOLUTION:")
    print("   1. Make sure .env file exists in the same directory as docker-compose.yml")
    print("   2. Add this line to .env:")
    print("      TAVILY_API_KEY=your_tavily_api_key_here")
    print("   3. Restart Docker container:")
    print("      docker-compose down")
    print("      docker-compose up -d")
    print()

print("=" * 60)

