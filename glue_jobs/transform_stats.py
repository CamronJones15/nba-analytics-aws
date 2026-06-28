"""
transform_stats.py
AWS Glue Python Shell job — transforms raw CSV data from S3
into Parquet format for Athena querying.
Uses boto3 + pandas instead of PySpark for simplicity and reliability.
"""

import sys
import os
import logging
import boto3
import pandas as pd
from io import StringIO, BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Args (passed in as Glue job parameters) ───────────────────────────────────
args = {}
for i, arg in enumerate(sys.argv[1:], 1):
    if arg.startswith("--") and i < len(sys.argv) - 1:
        key = arg.lstrip("--")
        val = sys.argv[i + 1] if not sys.argv[i + 1].startswith("--") else ""
        args[key] = val

S3_BUCKET = args.get("S3_BUCKET", os.environ.get("S3_BUCKET", "nba-analytics-camron"))
logger.info(f"Using bucket: {S3_BUCKET}")

s3 = boto3.client("s3", region_name="us-east-1")


# ── Helpers ───────────────────────────────────────────────────────────────────
def list_s3_csvs(prefix: str) -> list:
    """List all CSV files under a given S3 prefix."""
    paginator = s3.get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".csv"):
                keys.append(obj["Key"])
    return keys


def read_csv_from_s3(key: str) -> pd.DataFrame:
    """Read a CSV file from S3 into a DataFrame."""
    obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return pd.read_csv(StringIO(obj["Body"].read().decode("utf-8")))


def write_parquet_to_s3(df: pd.DataFrame, key: str):
    """Write a DataFrame as Parquet to S3."""
    buffer = BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=buffer.getvalue())
    logger.info(f"  -> Written to s3://{S3_BUCKET}/{key}")


# ── 1. Player Stats ───────────────────────────────────────────────────────────
logger.info("Transforming player stats...")
player_keys = list_s3_csvs("raw/player_stats/")
logger.info(f"  Found {len(player_keys)} CSV files")

if player_keys:
    player_dfs = [read_csv_from_s3(k) for k in player_keys]
    player_df = pd.concat(player_dfs, ignore_index=True)

    numeric_cols = [
        "games_played", "minutes_per_game", "points_per_game",
        "assists_per_game", "rebounds_per_game", "steals_per_game",
        "blocks_per_game", "field_goal_pct", "three_point_pct",
        "free_throw_pct", "efficiency_rating"
    ]
    for col in numeric_cols:
        if col in player_df.columns:
            player_df[col] = pd.to_numeric(player_df[col], errors="coerce")

    # Derived columns
    player_df["points_per_36"] = (
        player_df["points_per_game"] / player_df["minutes_per_game"] * 36
    ).round(2)

    player_df["true_shooting_pct"] = (
        player_df["points_per_game"] / (
            2 * (player_df["field_goal_pct"] + 0.44 * player_df["free_throw_pct"])
        )
    ).round(3)

    player_df["win_pct_label"] = pd.cut(
        player_df["efficiency_rating"],
        bins=[-999, 10, 15, 20, 999],
        labels=["Bench", "Role Player", "Starter", "Star"]
    ).astype(str)

    player_df = player_df.drop_duplicates(subset=["PLAYER_ID", "season"])
    player_df = player_df[player_df["games_played"] > 0]

    write_parquet_to_s3(player_df, "processed/player_stats/player_stats.parquet")
    logger.info(f"  Player stats rows: {len(player_df)}")


# ── 2. Team Standings ─────────────────────────────────────────────────────────
logger.info("Transforming team standings...")
standings_keys = list_s3_csvs("raw/team_standings/")
logger.info(f"  Found {len(standings_keys)} CSV files")

if standings_keys:
    standings_dfs = [read_csv_from_s3(k) for k in standings_keys]
    standings_df = pd.concat(standings_dfs, ignore_index=True)

    numeric_cols = [
        "wins", "losses", "win_pct",
        "points_per_game", "opp_points_per_game", "point_differential"
    ]
    for col in numeric_cols:
        if col in standings_df.columns:
            standings_df[col] = pd.to_numeric(standings_df[col], errors="coerce")

    standings_df["total_games"] = standings_df["wins"] + standings_df["losses"]
    standings_df["net_rating"] = (
        standings_df["points_per_game"] - standings_df["opp_points_per_game"]
    ).round(2)

    def win_label(pct):
        if pct >= 0.6:   return "Elite"
        if pct >= 0.5:   return "Playoff Contender"
        if pct >= 0.4:   return "Fringe"
        return "Lottery"

    standings_df["win_pct_label"] = standings_df["win_pct"].apply(win_label)
    standings_df = standings_df.drop_duplicates(subset=["team_id", "season"])

    write_parquet_to_s3(standings_df, "processed/team_standings/team_standings.parquet")
    logger.info(f"  Team standings rows: {len(standings_df)}")


# ── 3. Shot Charts ────────────────────────────────────────────────────────────
logger.info("Transforming shot charts...")
shot_keys = list_s3_csvs("raw/shot_charts/")
logger.info(f"  Found {len(shot_keys)} CSV files")

if shot_keys:
    shot_dfs = [read_csv_from_s3(k) for k in shot_keys]
    shots_df = pd.concat(shot_dfs, ignore_index=True)

    numeric_cols = ["loc_x", "loc_y", "shot_distance", "shot_made_flag", "period"]
    for col in numeric_cols:
        if col in shots_df.columns:
            shots_df[col] = pd.to_numeric(shots_df[col], errors="coerce")

    def zone_label(dist):
        if dist <= 3:   return "At Rim"
        if dist <= 10:  return "Short Mid-Range"
        if dist <= 16:  return "Mid-Range"
        if dist <= 22:  return "Long Mid-Range"
        return "Three-Point"

    shots_df["shot_zone_label"] = shots_df["shot_distance"].apply(zone_label)
    shots_df["made_label"] = shots_df["shot_made_flag"].apply(
        lambda x: "Made" if x == 1 else "Missed"
    )
    shots_df = shots_df.drop_duplicates(
        subset=["game_id", "player_id", "loc_x", "loc_y", "period"]
    )

    write_parquet_to_s3(shots_df, "processed/shot_charts/shot_charts.parquet")
    logger.info(f"  Shot chart rows: {len(shots_df)}")


logger.info("All transforms complete.")