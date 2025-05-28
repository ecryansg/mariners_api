from flask import Flask, jsonify
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

def get_mariners_data():
    team_id = 136  # Seattle Mariners
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate=2025-01-01&endDate=2025-12-31&hydrate=probablePitcher(note)"

    response = requests.get(url, verify=False)
    data = response.json()

    # Filter for games that are either in progress or completed
    relevant_games = [
        game for date in data['dates']
        for game in date['games']
        if game['status']['detailedState'] in ['Final', 'In Progress']
    ]

    if not relevant_games:
        return {"error": "No relevant games found."}

    # Prioritize in-progress games, otherwise get the latest completed game
    in_progress_games = [game for game in relevant_games if game['status']['detailedState'] == 'In Progress']
    latest_game = in_progress_games[-1] if in_progress_games else relevant_games[-1]

    game_status = latest_game['status']['detailedState']
    home_team = latest_game['teams']['home']['team']['name']
    away_team = latest_game['teams']['away']['team']['name']
    mariners_home = home_team == "Seattle Mariners"

    mariners_score = latest_game['teams']['home'].get('score', 'N/A') if mariners_home else latest_game['teams']['away'].get('score', 'N/A')
    opponent_score = latest_game['teams']['away'].get('score', 'N/A') if mariners_home else latest_game['teams']['home'].get('score', 'N/A')
    opponent = away_team if mariners_home else home_team

    latest_game_date_utc = datetime.fromisoformat(latest_game['gameDate'].replace('Z', '+00:00'))
    latest_game_date_pacific = latest_game_date_utc.astimezone(ZoneInfo('America/Los_Angeles'))

    # Get the next scheduled game
    next_game = [
        game for date in data['dates']
        for game in date['games']
        if game['status']['detailedState'] == 'Scheduled'
    ][0]

    next_game_date_utc = datetime.fromisoformat(next_game['gameDate'].replace('Z', '+00:00'))
    next_game_date_pacific = next_game_date_utc.astimezone(ZoneInfo('America/Los_Angeles'))

    next_game_home_team = next_game['teams']['home']['team']['name']
    next_game_away_team = next_game['teams']['away']['team']['name']
    next_game_opponent = next_game_away_team if next_game_home_team == "Seattle Mariners" else next_game_home_team

    probable_home_pitcher = next_game['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')
    probable_away_pitcher = next_game['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD')

    return {
        "lastGameDate": latest_game_date_pacific.strftime('%Y-%m-%d %H:%M:%S %Z'),
        "lastGameStatus": game_status,
        "lastOpponent": opponent,
        "lastScore": f"SEA {mariners_score} - {opponent} {opponent_score}",
        "nextGameDate": next_game_date_pacific.strftime('%Y-%m-%d %H:%M:%S %Z'),
        "nextOpponent": next_game_opponent,
        "probableHomePitcher": probable_home_pitcher,
        "probableAwayPitcher": probable_away_pitcher
    }

@app.route('/')
def mariners_data():
    data = get_mariners_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)

