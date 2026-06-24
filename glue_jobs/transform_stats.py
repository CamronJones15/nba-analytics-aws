"""
transform_stats.py
AWS Glue ETL job — transforms raw CSV data from S3 into
optimized Parquet format for Athena querying.

Deployed to: s3://<bucket>/glue_scripts/transform_stats.py
"""

import sys
import logging
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, IntegerType, StringType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Job args ──────────────────────────────────────────────────────────────────
args = getResolvedOptions(sys.argv, ["JOB_NAME", "S3_BUCKET", "DATABASE_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

S3_BUCKET = args["S3_BUCKET"]
RAW_BASE = f"s3://{S3_BUCKET}/raw"
PROCESSED_BASE = f"s3://{S3_BUCKET}/processed"


# ── Helper ────────────────────────────────────────────────────────────────────
def write_parquet(df, output_path: str, partition_cols: list = None):
    """Write a Spark DataFrame to S3 as Parquet, optionally partitioned."""
    writer = df.write.mode("overwrite").format("parquet")
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    writer.save(output_path)
    logger.info(f"Written to {output_path}")


# ── 1. Player Stats ───────────────────────────────────────────────────────────
logger.info("Transforming player stats...")

player_df = spark.read.option("header", "true").csv(
    f"{RAW_BASE}/player_stats/"
)

player_df = (
    player_df
    .withColumn("games_played",       F.col("games_played").cast(IntegerType()))
    .withColumn("minutes_per_game",   F.col("minutes_per_game").cast(DoubleType()))
    .withColumn("points_per_game",    F.col("points_per_game").cast(DoubleType()))
    .withColumn("assists_per_game",   F.col("assists_per_game").cast(DoubleType()))
    .withColumn("rebounds_per_game",  F.col("rebounds_per_game").cast(DoubleType()))
    .withColumn("steals_per_game",    F.col("steals_per_game").cast(DoubleType()))
    .withColumn("blocks_per_game",    F.col("blocks_per_game").cast(DoubleType()))
    .withColumn("field_goal_pct",     F.col("field_goal_pct").cast(DoubleType()))
    .withColumn("three_point_pct",    F.col("three_point_pct").cast(DoubleType()))
    .withColumn("free_throw_pct",     F.col("free_throw_pct").cast(DoubleType()))
    .withColumn("efficiency_rating",  F.col("efficiency_rating").cast(DoubleType()))
    # Derived columns
    .withColumn("points_per_36",
        F.round(F.col("points_per_game") / F.col("minutes_per_game") * 36, 2))
    .withColumn("assist_to_rebound_ratio",
        F.round(F.col("assists_per_game") / F.col("rebounds_per_game"), 2))
    .withColumn("true_shooting_pct",
        F.round(
            F.col("points_per_game") / (
                2 * (F.col("field_goal_pct") + 0.44 * F.col("free_throw_pct"))
            ), 3
        )
    )
    .withColumn("ingested_at", F.current_timestamp())
    .dropDuplicates(["PLAYER_ID", "season"])
    .filter(F.col("games_played") > 0)
)

write_parquet(player_df, f"{PROCESSED_BASE}/player_stats/", partition_cols=["season"])
logger.info(f"Player stats rows: {player_df.count()}")


# ── 2. Team Standings ─────────────────────────────────────────────────────────
logger.info("Transforming team standings...")

standings_df = spark.read.option("header", "true").csv(
    f"{RAW_BASE}/team_standings/"
)

standings_df = (
    standings_df
    .withColumn("wins",               F.col("wins").cast(IntegerType()))
    .withColumn("losses",             F.col("losses").cast(IntegerType()))
    .withColumn("win_pct",            F.col("win_pct").cast(DoubleType()))
    .withColumn("points_per_game",    F.col("points_per_game").cast(DoubleType()))
    .withColumn("opp_points_per_game",F.col("opp_points_per_game").cast(DoubleType()))
    .withColumn("point_differential", F.col("point_differential").cast(DoubleType()))
    # Derived columns
    .withColumn("total_games",
        F.col("wins") + F.col("losses"))
    .withColumn("win_pct_label",
        F.when(F.col("win_pct") >= 0.6, "Elite")
         .when(F.col("win_pct") >= 0.5, "Playoff Contender")
         .when(F.col("win_pct") >= 0.4, "Fringe")
         .otherwise("Lottery"))
    .withColumn("net_rating",
        F.round(F.col("points_per_game") - F.col("opp_points_per_game"), 2))
    .withColumn("ingested_at", F.current_timestamp())
    .dropDuplicates(["team_id", "season"])
)

write_parquet(standings_df, f"{PROCESSED_BASE}/team_standings/", partition_cols=["season"])
logger.info(f"Team standings rows: {standings_df.count()}")


# ── 3. Shot Charts ────────────────────────────────────────────────────────────
logger.info("Transforming shot chart data...")

shots_df = spark.read.option("header", "true").csv(
    f"{RAW_BASE}/shot_charts/"
)

shots_df = (
    shots_df
    .withColumn("loc_x",          F.col("loc_x").cast(IntegerType()))
    .withColumn("loc_y",          F.col("loc_y").cast(IntegerType()))
    .withColumn("shot_distance",  F.col("shot_distance").cast(IntegerType()))
    .withColumn("shot_made_flag", F.col("shot_made_flag").cast(IntegerType()))
    # Classify shot zones
    .withColumn("shot_zone_label",
        F.when(F.col("shot_distance") <= 3,  "At Rim")
         .when(F.col("shot_distance") <= 10, "Short Mid-Range")
         .when(F.col("shot_distance") <= 16, "Mid-Range")
         .when(F.col("shot_distance") <= 22, "Long Mid-Range")
         .otherwise("Three-Point"))
    # Flag whether shot was made as boolean label
    .withColumn("made_label",
        F.when(F.col("shot_made_flag") == 1, "Made").otherwise("Missed"))
    .withColumn("ingested_at", F.current_timestamp())
    .dropDuplicates(["game_id", "player_id", "loc_x", "loc_y", "period"])
)

write_parquet(shots_df, f"{PROCESSED_BASE}/shot_charts/", partition_cols=["season", "player_id"])
logger.info(f"Shot chart rows: {shots_df.count()}")


# ── Done ──────────────────────────────────────────────────────────────────────
logger.info("All transforms complete.")
job.commit()