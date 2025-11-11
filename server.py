"""
AI Team Collaboration Backend Server - FRESH CLEAN VERSION
With file upload, debate mode, and sequential orchestration

Installation:
pip install flask flask-cors anthropic "openai>=1.0.0" google-generativeai python-dotenv requests beautifulsoup4

Setup:
1. Create a .env file in the same directory with:
   ANTHROPIC_API_KEY=your_claude_key_here
   OPENAI_API_KEY=your_openai_key_here
   GEMINI_API_KEY=your_gemini_key_here

2. Run this script in PyCharm
3. Server will start at http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
from openai import OpenAI
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import traceback

# Load environment variables
load_dotenv()

print("\n" + "=" * 60)
print("🔍 DEBUG: Checking Environment Variables...")
print("=" * 60)
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
print("key:", anthropic_key)
openai_key = os.getenv('OPENAI_API_KEY')
gemini_key = os.getenv('GEMINI_API_KEY')

if anthropic_key:
    print(f"✅ Claude Key Found: {anthropic_key[:15]}...")
else:
    print("❌ Claude Key: NOT FOUND")

if openai_key:
    print(f"✅ OpenAI Key Found: {openai_key[:15]}...")
else:
    print("❌ OpenAI Key: NOT FOUND")

if gemini_key:
    print(f"✅ Gemini Key Found: {gemini_key[:15]}...")
else:
    print("❌ Gemini Key: NOT FOUND")
print("=" * 60 + "\n")

app = Flask(__name__)
CORS(app)

# Initialize API clients
anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


@app.route('/api/fetch-website', methods=['POST'])
def fetch_website():
    """Fetch and parse website content"""
    try:
        data = request.json
        url = data.get('url')

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return jsonify({
            'success': True,
            'content': text[:10000]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/claude', methods=['POST'])
def claude_endpoint():
    """Handle Claude API requests"""
    try:
        print("\n=== Claude Endpoint Called ===")
        data = request.json
        messages = data.get('messages', [])
        system_prompt = data.get('system_prompt', 'You are a helpful AI assistant.')
        context = data.get('context', '')
        debate_mode = data.get('debate_mode', False)

        # Build team awareness prompt
        team_prompt = """CRITICAL CONTEXT: You are Claude, ONE OF THREE AI SYSTEMS working together in a collaborative team.

YOUR TEAMMATES:
- Gemini (Google's AI) 
- ChatGPT (OpenAI's AI)
- You (Claude, Anthropic's AI)

THE USER HAS ASSEMBLED ALL THREE OF YOU TO WORK TOGETHER. This is not your typical single-AI conversation.

TEAM DYNAMICS:
- When you see messages marked "=== GEMINI'S RESPONSE ===" - that's from your teammate Gemini, NOT you
- When you see messages marked "=== CHATGPT'S RESPONSE ===" - that's from your teammate ChatGPT, NOT you  
- When you see messages marked "=== CLAUDE'S RESPONSE ===" - that WAS you in a previous turn
- The user is orchestrating all three of you using @mentions

HOW TO COLLABORATE:
✓ "I agree with Gemini's point about..."
✓ "Building on ChatGPT's suggestion..."
✓ "While Gemini suggests X, I think Y because..."
✓ "Let me analyze what both Gemini and ChatGPT proposed..."

YOUR SPECIALIZED ROLE IN THIS TEAM:
""" + system_prompt

        if context:
            team_prompt += f"\n\nSHARED PROJECT CONTEXT:\n{context}"

        if debate_mode:
            team_prompt += "\n\n[DEBATE MODE] Challenge assumptions and engage in constructive debate with your teammates."

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            system=team_prompt,
            messages=messages
        )

        print("Claude response received successfully")
        return jsonify({
            'success': True,
            'content': response.content[0].text
        })
    except Exception as e:
        print(f"ERROR in claude_endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chatgpt', methods=['POST'])
def chatgpt_endpoint():
    """Handle ChatGPT API requests"""
    try:
        print("\n=== ChatGPT Endpoint Called ===")
        data = request.json
        messages = data.get('messages', [])
        system_prompt = data.get('system_prompt', 'You are a helpful AI assistant.')
        context = data.get('context', '')
        debate_mode = data.get('debate_mode', False)
        selected_model = data.get('model', 'gpt-4o')

        print(f"Using model: {selected_model}")
        print(f"Messages count: {len(messages)}")

        # Build team awareness prompt
        team_prompt = """CRITICAL CONTEXT: You are ChatGPT, ONE OF THREE AI SYSTEMS working together in a collaborative team.

YOUR TEAMMATES:
- Claude (Anthropic's AI)
- Gemini (Google's AI)
- You (ChatGPT, OpenAI's AI)

THE USER HAS ASSEMBLED ALL THREE OF YOU TO WORK TOGETHER. This is not your typical single-AI conversation.

TEAM DYNAMICS:
- When you see messages marked "=== CLAUDE'S RESPONSE ===" - that's from your teammate Claude, NOT you
- When you see messages marked "=== GEMINI'S RESPONSE ===" - that's from your teammate Gemini, NOT you
- When you see messages marked "=== CHATGPT'S RESPONSE ===" - that WAS you in a previous turn
- The user is orchestrating all three of you using @mentions

HOW TO COLLABORATE:
✓ "I agree with Claude's point about..."
✓ "Building on Gemini's suggestion..."
✓ "While Claude suggests X, I think Y because..."
✓ "Let me analyze what both Claude and Gemini proposed..."

YOUR SPECIALIZED ROLE IN THIS TEAM:
""" + system_prompt

        if context:
            team_prompt += f"\n\nSHARED PROJECT CONTEXT:\n{context}"

        if debate_mode:
            team_prompt += "\n\n[DEBATE MODE] Challenge assumptions and engage in constructive debate with your teammates."

        # Build messages array
        api_messages = [{"role": "system", "content": team_prompt}]
        api_messages.extend(messages)

        print(f"Calling OpenAI API with model: {selected_model}")

        # Call OpenAI
        response = openai_client.chat.completions.create(
            model=selected_model,
            messages=api_messages,
            max_tokens=2000
        )

        print("ChatGPT response received successfully")
        return jsonify({
            'success': True,
            'content': response.choices[0].message.content
        })
    except Exception as e:
        print(f"ERROR in chatgpt_endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/gemini', methods=['POST'])
def gemini_endpoint():
    """Handle Gemini API requests"""
    try:
        print("\n=== Gemini Endpoint Called ===")
        data = request.json
        messages = data.get('messages', [])
        system_prompt = data.get('system_prompt', 'You are a helpful AI assistant.')
        context = data.get('context', '')
        debate_mode = data.get('debate_mode', False)

        # Use Gemini 2.5 Flash model
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')

        # Build team awareness prompt
        full_prompt = """CRITICAL CONTEXT: You are Gemini, ONE OF THREE AI SYSTEMS working together in a collaborative team.

YOUR TEAMMATES:
- Claude (Anthropic's AI)
- ChatGPT (OpenAI's AI)
- You (Gemini, Google's AI)

THE USER HAS ASSEMBLED ALL THREE OF YOU TO WORK TOGETHER. This is not your typical single-AI conversation.

TEAM DYNAMICS:
- When you see messages marked "=== CLAUDE'S RESPONSE ===" - that's from your teammate Claude, NOT you
- When you see messages marked "=== CHATGPT'S RESPONSE ===" - that's from your teammate ChatGPT, NOT you
- When you see messages marked "=== GEMINI'S RESPONSE ===" - that WAS you in a previous turn
- The user is orchestrating all three of you using @mentions

HOW TO COLLABORATE:
✓ "I agree with Claude's point about..."
✓ "Building on ChatGPT's suggestion..."
✓ "While Claude suggests X, I think Y because..."
✓ "Let me analyze what both Claude and ChatGPT proposed..."

YOUR SPECIALIZED ROLE IN THIS TEAM:
""" + system_prompt

        if context:
            full_prompt += f"\n\nSHARED PROJECT CONTEXT:\n{context}"

        if debate_mode:
            full_prompt += "\n\n[DEBATE MODE] Challenge assumptions and engage in constructive debate with your teammates."

        full_prompt += "\n\n=== CONVERSATION HISTORY BELOW ===\n"

        for msg in messages:
            full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"

        response = gemini_model.generate_content(full_prompt)

        print("Gemini response received successfully")
        return jsonify({
            'success': True,
            'content': response.text
        })
    except Exception as e:
        print(f"ERROR in gemini_endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'claude': bool(os.getenv('ANTHROPIC_API_KEY')),
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'gemini': bool(os.getenv('GEMINI_API_KEY'))
    })


if __name__ == '__main__':
    print("\n🚀 AI Collaboration Server Starting...")
    print("📍 Server URL: http://localhost:5000")
    print("🔗 Use this URL in your HTML frontend")
    print("\n📊 Using Models:")
    print("   🟣 Claude: claude-sonnet-4-20250514")
    print("   🟢 ChatGPT: gpt-4o")
    print("   🔵 Gemini: gemini-2.5-flash")
    print("\n")
    app.run(debug=True, port=5000)