import json
from storage import get_team_mapping, save_team_mapping
from ai_processor import shorten_and_emoji

# Load emoji icons for leagues
with open("leagues.json", encoding="utf-8") as f:
    LEAGUES = json.load(f)

# Load grouped league aliases and flatten
with open("league_aliases_grouped.json", encoding="utf-8") as f:
    grouped_aliases = json.load(f)

LEAGUE_ALIASES = {
    alias: name
    for group in grouped_aliases.values()
    for alias, name in group.items()
}

# Load league priority
with open("league_priority.json", encoding="utf-8") as f:
    league_priority = json.load(f)

def score_to_emoji(score):
    score_map = {
        0: '0️⃣', 1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣',
        6: '6️⃣', 7: '7️⃣', 8: '8️⃣', 9: '9️⃣', 10: '🔟'
    }
    return score_map.get(score, str(score))

def get_short_team_info(team_name):
    if not team_name:
        return ("◽", team_name)
    
    mapping = get_team_mapping(team_name)
    if mapping:
        return (mapping.get("emoji", "◽"), mapping.get("short_name", team_name))
    
    ai_result = shorten_and_emoji(team_name)
    short_name = ai_result.get("short_name", team_name)
    emoji = ai_result.get("emoji", "◽")
    
    save_team_mapping(team_name, short_name, emoji)
    
    return (emoji, short_name)

def _escape(text: str) -> str:
    # Escape MarkdownV2 special characters
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return (text.replace("\\", "\\\\")
                .replace("_", "\\_")
                .replace("*", "\\*")
                .replace("`", "\\`")
                .replace("[", "\")
                .replace("]", "\")
                .replace("(", "\")
                .replace(")", "\"))

def format_fixtures(matches):
    if not matches:
        return "⚠️ No matches scheduled for today."

    def sort_key(m):
        raw = m.get("league", "")
        alias = LEAGUE_ALIASES.get(raw, raw)
        return league_priority.index(alias) if alias in league_priority else len(league_priority)

    matches.sort(key=sort_key)

    message = "📌 𝗧𝗼𝗱𝗮𝘆'𝘀 𝗠𝗮𝘁𝗰𝗵𝗲𝘀\n\n"
    last_league = None

    for match in matches:
        raw_league = match.get("league", "Unknown League")
        league_name = LEAGUE_ALIASES.get(raw_league, raw_league)
        league_icon = LEAGUES.get(league_name, "🔰")

        if league_name != last_league:
            message += f"\n{league_icon} *{_escape(league_name)}*\n"

        home_emoji, home_short = get_short_team_info(match.get("home", ""))
        away_emoji, away_short = get_short_team_info(match.get("away", ""))

        home_short_esc = _escape(home_short)
        away_short_esc = _escape(away_short)

        match_text = (
            f"{home_emoji} *{home_short_esc}* 🆚 *{away_short_esc}* {away_emoji}\n"
            f"🕡 {match.get('local_time', '')} Local | {match.get('utc_time', match.get('utc_datetime',''))} UTC 🌐\n\n"
        )
        message += match_text
        last_league = league_name

    return message.strip()

def format_match_result(match):
    raw_league = match.get("league", "Unknown League")
    league_name = LEAGUE_ALIASES.get(raw_league, raw_league)
    league_icon = LEAGUES.get(league_name, "🔰")

    home_emoji, home_short = get_short_team_info(match.get("home", ""))
    away_emoji, away_short = get_short_team_info(match.get("away", ""))

    home_short_esc = _escape(home_short)
    away_short_esc = _escape(away_short)

    home_score = score_to_emoji(match.get('home_score', 0))
    away_score = score_to_emoji(match.get('away_score', 0))

    league_hashtag = f"#{league_name.replace(' ', '').lower()}"

    return (
        f"📌 𝗠𝗮𝘁𝗰𝗵 𝗘𝗻𝗱𝗲𝗱 | 𝗙𝗧\n\n"
        f"{league_icon} *{_escape(league_name)}*\n"
        f"{home_emoji} *{home_short_esc}* {home_score} - {away_score} *{away_short_esc}* {away_emoji}\n\n"
        f"{_escape(league_hashtag)}"
    )
