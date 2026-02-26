# agents/nodes/performance_intel.py

async def run_scoring_correlation_analysis(db_conn):
    """
    Correlate original content scores with real-world affiliate conversion data.
    Runs weekly after 6+ weeks of data.
    Surfaces in performance report as 'Scoring Model Health'.
    """
    async with db_conn.cursor() as cur:
        await cur.execute("""
            SELECT
                wr.final_score,
                ap.affiliate_clicks,
                ap.conversions,
                ap.avg_position,
                ap.sessions
            FROM workflow_runs wr
            JOIN article_performance ap ON wr.wp_post_id = ap.wp_post_id
            WHERE wr.completed_at > NOW() - INTERVAL '90 days'
              AND wr.status = 'complete'
              AND ap.date > CURRENT_DATE - 30
        """)
        rows = await cur.fetchall()

    if len(rows) < 10:
        return {"status": "insufficient_data", "min_samples": 10}

    scores      = [r["final_score"]      for r in rows]
    conv_rates  = [
        r["conversions"] / max(r["sessions"], 1) for r in rows
    ]

    # Pearson correlation
    correlation = compute_pearson(scores, conv_rates)

    analysis = {
        "sample_size":      len(rows),
        "score_conv_correlation": round(correlation, 3),
        "interpretation":   interpret_correlation(correlation),
        "threshold_recommendation": recommend_threshold(scores, conv_rates),
    }

    # Alert if correlation is weak (< 0.3) — scoring model needs recalibration
    if correlation < 0.3:
        await publish_event("performance.scoring_alert", {
            "correlation":     correlation,
            "recommendation":  "Review Judge Agent prompts and criteria weights",
        })

    return analysis