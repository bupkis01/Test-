# 24/7 Football Bot ⚽🤖

- **Platform:** Koyeb (Free Tier)  
- **Run Command:** `python main.py`  

## Environment Variables

The following environment variables **must** be set:

- `BOT_TOKEN`  
  Your Telegram bot token from BotFather.

- `CHANNEL_ID`  
  The ID of the Telegram channel where the bot will post updates.

- `GOOGLE_AI_KEY`  
  API key for Google AI services.

- `PERSONAL_CHAT_ID`  
  Your personal Telegram chat ID for direct alerts and messages.

- `FIREBASE_KEY_B64`  
  Base64-encoded JSON credentials for Firebase.  
  The script will decode this and write `config/firebase-key.json`.

---

## Description

This bot fetches football fixtures and posts them to your specified Telegram channel 24/7.

## Deployment

1. Clone the repository.  
2. Add all environment variables to your deployment settings on Koyeb.  
3. Run with:
   ```bash
   python main.py
