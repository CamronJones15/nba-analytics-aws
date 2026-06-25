-- team_standings.sql
-- Team performance and standings analysis
-- Run in Athena workgroup: nba-analytics-workgroup

-- Full standings sorted by win percentage
SELECT
    team_city || ' ' || team_name   AS team,
    team_abbreviation,
    conference,
    division,
    wins,
    losses,
    total_games,
    ROUND(win_pct * 100, 1)         AS win_pct,
    win_pct_label,
    home_record,
    away_record,
    last_10_record,
    ROUND(points_per_game, 1)       AS off_ppg,
    ROUND(opp_points_per_game, 1)   AS def_ppg,
    ROUND(net_rating, 1)            AS net_rating,
    season
FROM processed.team_standings
WHERE season = '2024-25'
ORDER BY win_pct DESC;


-- ── Conference breakdown ──────────────────────────────────────────────────────
SELECT
    conference,
    COUNT(*)                        AS teams,
    SUM(wins)                       AS total_wins,
    ROUND(AVG(win_pct) * 100, 1)    AS avg_win_pct,
    ROUND(AVG(points_per_game), 1)  AS avg_off_ppg,
    ROUND(AVG(opp_points_per_game), 1) AS avg_def_ppg,
    ROUND(AVG(net_rating), 1)       AS avg_net_rating
FROM processed.team_standings
WHERE season = '2024-25'
GROUP BY conference
ORDER BY avg_win_pct DESC;


-- ── Best offensive teams ──────────────────────────────────────────────────────
SELECT
    team_city || ' ' || team_name   AS team,
    conference,
    ROUND(points_per_game, 1)       AS ppg,
    ROUND(net_rating, 1)            AS net_rating,
    wins,
    losses
FROM processed.team_standings
WHERE season = '2024-25'
ORDER BY points_per_game DESC
LIMIT 10;


-- ── Best defensive teams (lowest opponent PPG) ────────────────────────────────
SELECT
    team_city || ' ' || team_name   AS team,
    conference,
    ROUND(opp_points_per_game, 1)   AS opp_ppg,
    ROUND(net_rating, 1)            AS net_rating,
    wins,
    losses
FROM processed.team_standings
WHERE season = '2024-25'
ORDER BY opp_points_per_game ASC
LIMIT 10;


-- ── Playoff picture (top 6 per conference + play-in spots) ───────────────────
SELECT
    conference,
    team_city || ' ' || team_name   AS team,
    wins,
    losses,
    ROUND(win_pct * 100, 1)         AS win_pct,
    ROW_NUMBER() OVER (
        PARTITION BY conference
        ORDER BY win_pct DESC
    )                               AS conference_seed
FROM processed.team_standings
WHERE season = '2024-25'
QUALIFY conference_seed <= 10
ORDER BY conference, conference_seed;