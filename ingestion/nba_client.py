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
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUEST_DELAY = 1.0
CURRENT_SEASON = "2024-25"


def get_player_stats(season: str = CURRENT_SEASON) -> pd.DataFrame:
    """Pull top player stats for a given season."""
    logger.info(f"Fetching player stats for season {season}...")
    time.sleep(REQUEST_DELAY)

    response = leagueleaders.LeagueLeaders(
        season=season,
        stat_category_abbreviation="PTS",
        season_type_all_star="Regular Season",
        per_mode48="PerGame",
    )

    df = response.get_data_frames()[0]

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
    """Pull current NBA team standings."""
    logger.info(f"Fetching team standings for season {season}...")
    time.sleep(REQUEST_DELAY)

    response = leaguestandingsv3.LeagueStandingsV3(
        season=season,
        season_type="Regular Season",
    )

    df = response.get_data_frames()[0]

    # Normalize — nba_api column names change across versions
    col_map = {c.lower(): c for c in df.columns}

    def get_col(*candidates):
        for c in candidates:
            if c.lower() in col_map:
                return col_map[c.lower()]
        raise KeyError(f"None of {candidates} found. Available: {list(df.columns)}")

    selected = [
        get_col("TeamID"),
        get_col("TeamCity"),
        get_col("TeamName"),
        get_col("TeamAbbreviation", "TeamSlug"),
        get_col("Conference"),
        get_col("Division"),
        get_col("WINS", "W"),
        get_col("LOSSES", "L"),
        get_col("WinPCT", "PCT"),
        get_col("HOME"),
        get_col("ROAD", "AWAY"),
        get_col("L10"),
        get_col("PointsPG", "PPG"),
        get_col("OppPointsPG", "OppPPG"),
        get_col("DiffPointsPG", "DIFF"),
    ]

    df = df[selected].copy()
    df.columns = [
        "team_id", "team_city", "team_name", "team_abbreviation",
        "conference", "division", "wins", "losses",
        "win_pct", "home_record", "away_record", "last_10_record",
        "points_per_game", "opp_points_per_game", "point_differential",
    ]

    df["season"] = season
    logger.info(f"  -> Retrieved {len(df)} teams")
    return df


def get_shot_chart(player_id: int, season: str = CURRENT_SEASON) -> pd.DataFrame:
    """Pull shot chart data for a specific player."""
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


if __name__ == "__main__":
    print("\n--- Player Stats ---")
    players = get_player_stats()
    print(players.head())

    print("\n--- Team Standings ---")
    standings = get_team_standings()
    print(standings.head())