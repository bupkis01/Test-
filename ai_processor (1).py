import google.generativeai as genai
import os
import json

# Pre-flight check for API key
API_KEY = os.getenv("GOOGLE_AI_KEY")
if not API_KEY:
    raise ValueError("❌ Error: Missing GOOGLE_AI_KEY for AI processing")
genai.configure(api_key=API_KEY)

def shorten_and_emoji(team_name):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")

        prompt = f"""
You are a football assistant bot.
Given a full football club name, you must:
- Return a short name (maximum 2 words).
- Suggest 1 emoji related to the team (colors, theme, nickname).

Example:
- Manchester United -> 🔴 Man United
- Borussia Dortmund -> 🟡 B-Dortmund
- Real Madrid -> ⚪ Real Madrid
- Brazil -> 🇧🇷 Brazil
- Argentina -> 🇦🇷 Argentina 
- England -> 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England 

Club: {team_name}
Respond in JSON format like:
{{"short_name": "Short Version", "emoji": "Emoji Here"}}
"""

        response = model.generate_content(prompt)
        result = response.text.strip()

        # Attempt to parse JSON; fall back if malformed
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print("❌ JSON Parsing Error in AI response")
            return {"short_name": team_name, "emoji": "◽"}

    except Exception as e:
        print(f"❌ AI Processing Error: {e}")
        return {"short_name": team_name, "emoji": "◽"}
