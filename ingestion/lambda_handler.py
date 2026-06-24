"""
lambda_handler.py
AWS Lambda entry point — pulls NBA data and uploads to S3.
Can also be run locally for testing.
"""

import os
import json
import logging
import boto3
from datetime import datetime
from io import StringIO

import pandas as pd
from dotenv import load_dotenv

from nba_client import (
    get_player_stats,
    get_team_standings,
    get_shot_chart,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "nba-analytics-bucket")
CURRENT_SEASON = "2024-25"

# Top players to pull shot charts for (by player_id)
# LeBron James, Stephen Curry, Kevin Durant, Giannis, Luka Doncic
TOP_PLAYER_IDS = [2544, 201939, 201142, 203507, 1629029]


def upload_df_to_s3(df: pd.DataFrame, s3_key: str, s3_client) -> None:
    """Convert DataFrame to CSV and upload to S3."""
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=csv_buffer.getvalue(),
        ContentType="text/csv",
    )
    logger.info(f"  -> Uploaded to s3://{S3_BUCKET}/{s3_key}")


def handler(event: dict, context) -> dict:
    """
    Lambda handler — entry point when deployed to AWS.
    Also callable directly for local testing.
    """
    logger.info("NBA Analytics ingestion job started")

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    s3 = boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )

    results = {}

    # ── 1. Player Stats ───────────────────────────────────────────────────────
    try:
        player_df = get_player_stats(season=CURRENT_SEASON)
        s3_key = f"raw/player_stats/season={CURRENT_SEASON}/date={date_str}/player_stats.csv"
        upload_df_to_s3(player_df, s3_key, s3)
        results["player_stats"] = {
            "status": "success",
            "rows": len(player_df),
            "s3_key": s3_key,
        }
    except Exception as e:
        logger.error(f"Player stats failed: {e}")
        results["player_stats"] = {"status": "error", "message": str(e)}

    # ── 2. Team Standings ─────────────────────────────────────────────────────
    try:
        standings_df = get_team_standings(season=CURRENT_SEASON)
        s3_key = f"raw/team_standings/season={CURRENT_SEASON}/date={date_str}/standings.csv"
        upload_df_to_s3(standings_df, s3_key, s3)
        results["team_standings"] = {
            "status": "success",
            "rows": len(standings_df),
            "s3_key": s3_key,
        }
    except Exception as e:
        logger.error(f"Team standings failed: {e}")
        results["team_standings"] = {"status": "error", "message": str(e)}

    # ── 3. Shot Charts ────────────────────────────────────────────────────────
    shot_results = []
    for player_id in TOP_PLAYER_IDS:
        try:
            shot_df = get_shot_chart(player_id=player_id, season=CURRENT_SEASON)
            if not shot_df.empty:
                s3_key = (
                    f"raw/shot_charts/season={CURRENT_SEASON}"
                    f"/date={date_str}/player_{player_id}.csv"
                )
                upload_df_to_s3(shot_df, s3_key, s3)
                shot_results.append({
                    "player_id": player_id,
                    "status": "success",
                    "rows": len(shot_df),
                })
        except Exception as e:
            logger.error(f"Shot chart failed for player {player_id}: {e}")
            shot_results.append({
                "player_id": player_id,
                "status": "error",
                "message": str(e),
            })

    results["shot_charts"] = shot_results

    response = {
        "statusCode": 200,
        "date": date_str,
        "season": CURRENT_SEASON,
        "results": results,
    }

    logger.info("Ingestion complete")
    logger.info(json.dumps(response, indent=2))
    return response


if __name__ == "__main__":
    # Run locally: python ingestion/lambda_handler.py
    result = handler({}, None)
    print(json.dumps(result, indent=2))