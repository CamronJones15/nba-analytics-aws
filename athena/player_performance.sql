-- player_performance.sql
-- Top player stats for a given season
-- Run in Athena workgroup: nba-analytics-workgroup

-- Top 20 scorers with full stat line
SELECT
    player_name,
    team_abbreviation,
    games_played,
    ROUND(points_per_game, 1)   AS ppg,
    ROUND(assists_per_game, 1)  AS apg,
    ROUND(rebounds_per_game, 1) AS rpg,
    ROUND(steals_per_game, 1)   AS spg,
    ROUND(blocks_per_game, 1)   AS bpg,
    ROUND(field_goal_pct * 100, 1)   AS fg_pct,
    ROUND(three_point_pct * 100, 1)  AS three_pct,
    ROUND(free_throw_pct * 100, 1)   AS ft_pct,
    ROUND(true_shooting_pct * 100, 1) AS ts_pct,
    ROUND(efficiency_rating, 1) AS efficiency,
    season
FROM processed.player_stats
WHERE season = '2024-25'
  AND games_played >= 20
ORDER BY points_per_game DESC
LIMIT 20;


-- ── Players averaging a 20-5-5 triple threat ─────────────────────────────────
SELECT
    player_name,
    team_abbreviation,
    ROUND(points_per_game, 1)   AS ppg,
    ROUND(assists_per_game, 1)  AS apg,
    ROUND(rebounds_per_game, 1) AS rpg,
    ROUND(efficiency_rating, 1) AS efficiency
FROM processed.player_stats
WHERE season = '2024-25'
  AND points_per_game  >= 20
  AND assists_per_game >= 5
  AND rebounds_per_game >= 5
ORDER BY points_per_game DESC;


-- ── Efficiency leaders (min 20 games) ────────────────────────────────────────
SELECT
    player_name,
    team_abbreviation,
    games_played,
    ROUND(efficiency_rating, 1)      AS efficiency,
    ROUND(true_shooting_pct * 100, 1) AS ts_pct,
    ROUND(points_per_game, 1)        AS ppg
FROM processed.player_stats
WHERE season = '2024-25'
  AND games_played >= 20
ORDER BY efficiency_rating DESC
LIMIT 15;


-- ── Best three-point shooters (min 20 games) ──────────────────────────────────
SELECT
    player_name,
    team_abbreviation,
    ROUND(three_point_pct * 100, 1) AS three_pct,
    ROUND(points_per_game, 1)       AS ppg,
    games_played
FROM processed.player_stats
WHERE season = '2024-25'
  AND games_played >= 20
  AND three_point_pct IS NOT NULL
ORDER BY three_point_pct DESC
LIMIT 15;