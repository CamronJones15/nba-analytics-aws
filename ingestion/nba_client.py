"""
nba_client.py
Wrapper around nba_api to pull player stats, team standings, and shot chart data.
"""

import time
import logging
import pandas as pd
from nba_api.stats.endpoints import (
    leagueleaders,
    leaguestandingsv3,
    shotchartdetail,
    commonallplayers,
)
from nba_api.stats.static import teams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# nba_api requires a delay between requests to avoid rate limiting
REQUEST_DELAY = 1.0
CURRENT_SEASON = "2024-25"


def get_player_stats(season: str = CURRENT_SEASON) -> pd.DataFrame:
    """
    Pull top player stats for a given season (points, assists, rebounds, etc.)
    Returns a cleaned DataFrame.
    """
    logger.info(f"Fetching player stats for season {season}...")
    time.sleep(REQUEST_DELAY)

    response = leagueleaders.LeagueLeaders(
        season=season,
        stat_category_abbreviation="PTS",
        season_type_all_star="Regular Season",
        per_mode48="PerGame",
    )

    df = response.get_data_frames()[0]

    # Select and rename key columns
    df = df[[
        "PLAYER_ID", "PLAYER", "TEAM", "GP", "MIN",
        "PTS", "AST", "REB", "STL", "BLK",
        "FG_PCT", "FG3_PCT", "FT_PCT", "EFF"
    ]].copy()

    df.rename(columns={
        "PLAYER": "player_name",
        "TEAM": "team_abbreviation",
        "GP": "games_played",
        "MIN": "minutes_per_game",
        "PTS": "points_per_game",
        "AST": "assists_per_game",
        "REB": "rebounds_per_game",
        "STL": "steals_per_game",
        "BLK": "blocks_per_game",
        "FG_PCT": "field_goal_pct",
        "FG3_PCT": "three_point_pct",
        "FT_PCT": "free_throw_pct",
        "EFF": "efficiency_rating",
    }, inplace=True)

    df["season"] = season
    logger.info(f"  -> Retrieved {len(df)} players")
    return df


def get_team_standings(season: str = CURRENT_SEASON) -> pd.DataFrame:
    """
    Pull current NBA team standings.
    Returns a cleaned DataFrame with wins, losses, and conference info.
    """
    logger.info(f"Fetching team standings for season {season}...")
    time.sleep(REQUEST_DELAY)

    response = leaguestandingsv3.LeagueStandingsV3(
        season=season,
        season_type="Regular Season",
    )

    df = response.get_data_frames()[0]

    df = df[[
        "TeamID", "TeamCity", "TeamName", "TeamAbbreviation",
        "Conference", "Division", "WINS", "LOSSES",
        "WinPCT", "HOME", "ROAD", "L10",
        "PointsPG", "OppPointsPG", "DiffPointsPG"
    ]].copy()

    df.rename(columns={
        "TeamID": "team_id",
        "TeamCity": "team_city",
        "TeamName": "team_name",
        "TeamAbbreviation": "team_abbreviation",
        "Conference": "conference",
        "Division": "division",
        "WINS": "wins",
        "LOSSES": "losses",
        "WinPCT": "win_pct",
        "HOME": "home_record",
        "ROAD": "away_record",
        "L10": "last_10_record",
        "PointsPG": "points_per_game",
        "OppPointsPG": "opp_points_per_game",
        "DiffPointsPG": "point_differential",
    }, inplace=True)

    df["season"] = season
    logger.info(f"  -> Retrieved {len(df)} teams")
    return df


def get_shot_chart(player_id: int, season: str = CURRENT_SEASON) -> pd.DataFrame:
    """
    Pull shot chart data for a specific player.
    Returns a DataFrame with shot location (x, y), result, and shot type.
    """
    logger.info(f"Fetching shot chart for player_id={player_id}, season={season}...")
    time.sleep(REQUEST_DELAY)

    response = shotchartdetail.ShotChartDetail(
        team_id=0,
        player_id=player_id,
        season_nullable=season,
        season_type_all_star="Regular Season",
        context_measure_simple="FGA",
    )

    df = response.get_data_frames()[0]

    if df.empty:
        logger.warning(f"  -> No shot data found for player_id={player_id}")
        return df

    df = df[[
        "GAME_ID", "PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_NAME",
        "PERIOD", "MINUTES_REMAINING", "SECONDS_REMAINING",
        "EVENT_TYPE", "ACTION_TYPE", "SHOT_TYPE", "SHOT_ZONE_BASIC",
        "SHOT_ZONE_AREA", "SHOT_DISTANCE", "LOC_X", "LOC_Y", "SHOT_MADE_FLAG"
    ]].copy()

    df.columns = [c.lower() for c in df.columns]
    df["season"] = season
    logger.info(f"  -> Retrieved {len(df)} shot attempts")
    return df


def get_top_player_ids(n: int = 10, season: str = CURRENT_SEASON) -> list:
    """
    Returns the player IDs of the top N scorers — used to pull shot charts.
    """
    df = get_player_stats(season)
    return df.head(n)["PLAYER_ID"].tolist() if "PLAYER_ID" in df.columns else []


if __name__ == "__main__":
    # Quick smoke test — run locally with: python ingestion/nba_client.py
    print("\n--- Player Stats ---")
    players = get_player_stats()
    print(players.head())

    print("\n--- Team Standings ---")
    standings = get_team_standings()
    print(standings.head())