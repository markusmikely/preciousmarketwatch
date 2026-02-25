<?php
if ( ! defined( 'ABSPATH' ) ) exit;

$pipeline = $pipeline ?? [];
$agents   = $agents ?? [];
$alerts   = $alerts ?? [];
$perf     = $perf ?? [];
$intel    = $intel ?? [];
$affiliate = $affiliate ?? [];
$revenue  = $revenue ?? [];
$costs    = $costs ?? [];

$active_count = count( array_filter( $agents, fn( $a ) => ( $a['status'] ?? '' ) === 'active' ) );
$cost_today   = $costs['today_usd'] ?? 0;
$cost_month   = $costs['month_usd'] ?? 0;
$rev_month    = $revenue['confirmed'] ?? 0;
?>
<div class="pmw-mc" id="pmw-mission-control">

    <div class="pmw-mc__header">
        <div class="pmw-mc__brand">
            <span class="pmw-mc__logo">◆ PMW</span>
            <span class="pmw-mc__title">Mission Control</span>
        </div>
        <div class="pmw-mc__status-bar">
            <span class="pmw-connection-indicator" id="pmw-ws-indicator">Connecting…</span>
            <span class="pmw-mc__updated">Updated: <span id="pmw-last-updated">—</span></span>
        </div>
    </div>

    <div class="pmw-mc__metrics-strip">
        <div class="pmw-metric">
            <div class="pmw-metric__value"><?php echo esc_html( $active_count ); ?>/18</div>
            <div class="pmw-metric__label">Agents active</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value"><?php echo esc_html( count( $alerts ) ); ?></div>
            <div class="pmw-metric__label">Alerts</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value"><?php echo esc_html( $cost_today ? sprintf( '$%.2f', $cost_today ) : '—' ); ?></div>
            <div class="pmw-metric__label">LLM cost today</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value"><?php echo esc_html( $rev_month ? '£' . number_format( $rev_month ) : '—' ); ?></div>
            <div class="pmw-metric__label">Est. revenue MTD</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value"><?php echo esc_html( $cost_month ? sprintf( '$%.2f', $cost_month ) : '—' ); ?></div>
            <div class="pmw-metric__label">Cost this month</div>
        </div>
    </div>

    <div class="pmw-mc__row pmw-mc__row--thirds">
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Pipeline Status</h3>
            <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                Stage breakdown and active tasks. Connect the bridge to see live data.
            </p>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Agent Status Board</h3>
            <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                All 18 agents. Filter and search. Connect the bridge for real-time updates.
            </p>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Alerts</h3>
            <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                Escalations from intelligence agents. No unread alerts.
            </p>
        </div>
    </div>

    <div class="pmw-mc__row pmw-mc__row--4060">
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Content Queue</h3>
            <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                Awaiting approval, in production, scheduled. Approve & Publish from here.
            </p>
        </div>
        <div class="pmw-mc__col pmw-mc__col--right">
            <div class="pmw-panel">
                <h3 class="pmw-panel-title">Performance Intelligence</h3>
                <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                    GA4 + Clarity. Top performers, needs attention.
                </p>
            </div>
            <div class="pmw-panel">
                <h3 class="pmw-panel-title">Intelligence Briefs</h3>
                <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                    Trend Analyst, Content Gap, Financial Intel.
                </p>
            </div>
        </div>
    </div>

    <div class="pmw-mc__row pmw-mc__row--thirds">
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">LLM Cost Summary</h3>
            <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                By model, by agent. Revenue/cost ratio.
            </p>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Affiliate Performance</h3>
            <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                Clicks, CVR, revenue by partner.
            </p>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Revenue Tracker</h3>
            <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">
                MTD, pace, 6-month trend.
            </p>
        </div>
    </div>

    <p style="margin-top: 24px;">
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=pmw-agent-control' ) ); ?>" class="pmw-btn pmw-btn--ghost">
            Agent Control →
        </a>
    </p>
</div>
