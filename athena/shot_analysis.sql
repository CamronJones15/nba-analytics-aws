-- shot_analysis.sql
-- Shot chart and shooting efficiency analysis
-- Run in Athena workgroup: nba-analytics-workgroup

-- Overall shooting by zone for all tracked players
SELECT
    player_name,
    shot_zone_label,
    COUNT(*)                                        AS attempts,
    SUM(shot_made_flag)                             AS makes,
    ROUND(
        SUM(shot_made_flag) * 100.0 / COUNT(*), 1
    )                                               AS fg_pct,
    season
FROM processed.shot_charts
WHERE season = '2024-25'
GROUP BY player_name, shot_zone_label, season
ORDER BY player_name, fg_pct DESC;


-- ── Hot zones — where each player shoots best ─────────────────────────────────
SELECT
    player_name,
    shot_zone_basic,
    shot_zone_area,
    COUNT(*)                                        AS attempts,
    ROUND(
        SUM(shot_made_flag) * 100.0 / COUNT(*), 1
    )                                               AS fg_pct
FROM processed.shot_charts
WHERE season = '2024-25'
  AND shot_made_flag IS NOT NULL
GROUP BY player_name, shot_zone_basic, shot_zone_area
HAVING COUNT(*) >= 10
ORDER BY player_name, fg_pct DESC;


-- ── Shot volume by distance bucket ───────────────────────────────────────────
SELECT
    player_name,
    shot_zone_label,
    COUNT(*)                                        AS total_attempts,
    SUM(shot_made_flag)                             AS total_makes,
    ROUND(
        SUM(shot_made_flag) * 100.0 / COUNT(*), 1
    )                                               AS fg_pct,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY player_name), 1
    )                                               AS pct_of_shots
FROM processed.shot_charts
WHERE season = '2024-25'
GROUP BY player_name, shot_zone_label
ORDER BY player_name, total_attempts DESC;


-- ── Clutch shots (4th quarter, under 5 minutes) ───────────────────────────────
SELECT
    player_name,
    COUNT(*)                                        AS clutch_attempts,
    SUM(shot_made_flag)                             AS clutch_makes,
    ROUND(
        SUM(shot_made_flag) * 100.0 / COUNT(*), 1
    )                                               AS clutch_fg_pct
FROM processed.shot_charts
WHERE season = '2024-25'
  AND period = 4
  AND minutes_remaining <= 5
GROUP BY player_name
HAVING COUNT(*) >= 5
ORDER BY clutch_fg_pct DESC;