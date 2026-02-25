<?php
if ( ! defined( 'ABSPATH' ) ) exit;

$pipeline   = $pipeline ?? [];
$agents     = $agents ?? [];
$alerts     = $alerts ?? [];
$perf       = $perf ?? [];
$intel      = $intel ?? [];
$affiliate  = $affiliate ?? [];
$revenue    = $revenue ?? [];
$costs      = $costs ?? [];

// Mock data when options are empty (works without bridge connection)
$active_count  = count( array_filter( $agents, fn( $a ) => ( $a['status'] ?? '' ) === 'active' ) ) ?: 0;
$cost_today    = $costs['today_usd'] ?? 0;
$cost_month    = $costs['month_usd'] ?? 18.40;
$rev_month     = $revenue['confirmed'] ?? 1240;
$sessions_7d   = $perf['week_sessions'] ?? 4821;
$aff_clicks    = $affiliate['clicks_mtd'] ?? 342;

// Mock pipeline stages
$stages = [
    [ 'name' => 'Brief', 'done' => 4, 'active' => 0, 'queued' => 0, 'err' => 0 ],
    [ 'name' => 'Research', 'done' => 3, 'active' => 0, 'queued' => 0, 'err' => 1 ],
    [ 'name' => 'Writing', 'done' => 0, 'active' => 2, 'queued' => 0, 'err' => 0 ],
    [ 'name' => 'Fact Check', 'done' => 0, 'active' => 0, 'queued' => 2, 'err' => 0 ],
    [ 'name' => 'Review', 'done' => 0, 'active' => 0, 'queued' => 2, 'err' => 0 ],
    [ 'name' => 'Publish', 'done' => 12, 'active' => 0, 'queued' => 0, 'err' => 0 ],
];

// Mock active tasks
$active_tasks = [
    [ 'title' => 'Gold Hits 3-Month High After Fed Comments', 'stage' => 'Writing', 'agent' => 'The Market Writer', 'eta' => '11:44', 'cost' => 0.14, 'tokens' => 8200 ],
    [ 'title' => "Beginner's Guide to Silver Bullion", 'stage' => 'Writing', 'agent' => 'The Feature Writer', 'eta' => '11:22', 'cost' => 0.22, 'tokens' => 12400 ],
];

// Mock agent tiers (18 agents)
$tiers = [
    'EXECUTIVE' => [ [ 'name' => 'The Director', 'status' => 'active', 'detail' => 'Assigning tasks • 14:28' ] ],
    'EDITORIAL' => [
        [ 'name' => 'Editor-in-Chief', 'status' => 'active', 'detail' => 'Reviewing: "Silver Supply..."' ],
        [ 'name' => 'Research Director', 'status' => 'idle', 'detail' => 'Last: 13:55' ],
        [ 'name' => 'SEO Strategist', 'status' => 'idle', 'detail' => '' ],
    ],
    'INTELLIGENCE' => [
        [ 'name' => 'Trend Analyst', 'status' => 'active', 'detail' => 'Fetching Reddit signals' ],
        [ 'name' => 'Content Gap Analyst', 'status' => 'queued', 'detail' => 'Next run: Mon 09:00' ],
        [ 'name' => 'Performance Intelligence', 'status' => 'active', 'detail' => 'Processing GA4 report' ],
        [ 'name' => 'Financial Intelligence', 'status' => 'active', 'detail' => 'Alert queued: Gold +2.1%' ],
        [ 'name' => 'Affiliate Intelligence', 'status' => 'queued', 'detail' => 'Next run: 18:00' ],
    ],
    'PRODUCTION' => [
        [ 'name' => 'Metals Analyst', 'status' => 'active', 'detail' => 'Researching: Fed impact' ],
        [ 'name' => 'Gemstone Analyst', 'status' => 'idle', 'detail' => '' ],
        [ 'name' => 'Market Writer', 'status' => 'active', 'detail' => 'Writing: Gold 3-Month High' ],
        [ 'name' => 'Feature Writer', 'status' => 'active', 'detail' => 'Writing: Silver Guide' ],
        [ 'name' => 'Fact Checker', 'status' => 'queued', 'detail' => '2 articles' ],
        [ 'name' => 'Publisher', 'status' => 'idle', 'detail' => '' ],
    ],
    'SUPPORT' => [
        [ 'name' => 'Newsletter Curator', 'status' => 'queued', 'detail' => 'Next run: Fri 07:00' ],
        [ 'name' => 'Social Scribe', 'status' => 'idle', 'detail' => '' ],
        [ 'name' => 'Quality Monitor', 'status' => 'queued', 'detail' => 'Next run: 03:00' ],
    ],
];

// Mock content queue
$awaiting = [
    [ 'title' => 'Palladium: Why 2025 Could Be the Year', 'seo' => 87, 'words' => 1840, 'rev' => 45 ],
    [ 'title' => 'Diamond Price Index Q1 2026', 'seo' => 91, 'words' => 2100, 'rev' => 80 ],
];
$in_production = [
    [ 'title' => 'Gold 3-Month High', 'stage' => 'Writing', 'agent' => 'Market Writer', 'eta' => '11:44' ],
    [ 'title' => 'Silver Beginner Guide', 'stage' => 'Writing', 'agent' => 'Feature Writer', 'eta' => '11:22' ],
];
$published_today = [ 'Silver Price Live UK', 'Palladium 2025 Q1', 'Ruby vs Garnet' ];
?>
<div class="pmw-mc" id="pmw-mission-control">

    <div class="pmw-mc__header">
        <div class="pmw-mc__brand">
            <span class="pmw-mc__logo">◆ PMW</span>
            <span class="pmw-mc__title">Mission Control</span>
        </div>
        <div class="pmw-mc__status-bar">
            <span class="pmw-connection-indicator" id="pmw-ws-indicator">Connecting…</span>
            <span class="pmw-mc__updated">Updated: <span id="pmw-last-updated"><?php echo esc_html( current_time( 'H:i' ) ); ?></span></span>
        </div>
    </div>

    <div class="pmw-mc__metrics-strip">
        <div class="pmw-metric">
            <div class="pmw-metric__value">3</div>
            <div class="pmw-metric__label">Pipeline active</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value">2</div>
            <div class="pmw-metric__label">Queued</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value"><?php echo count( $alerts ) ?: '0'; ?></div>
            <div class="pmw-metric__label">Alerts</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value">3</div>
            <div class="pmw-metric__label">Published today</div>
        </div>
        <div class="pmw-metric pmw-metric--gold">
            <div class="pmw-metric__value"><?php echo $rev_month ? '£' . number_format( $rev_month ) : '—'; ?></div>
            <div class="pmw-metric__label">Est. revenue MTD</div>
        </div>
        <div class="pmw-metric pmw-metric--gold">
            <div class="pmw-metric__value"><?php echo $cost_today ? sprintf( '$%.2f', $cost_today ) : '$0.84'; ?></div>
            <div class="pmw-metric__label">LLM cost today</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value"><?php echo number_format( $sessions_7d ); ?> <span class="pmw-metric__delta pmw-metric__delta--up">▲12%</span></div>
            <div class="pmw-metric__label">Sessions 7d</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value"><?php echo $aff_clicks; ?> <span class="pmw-metric__delta pmw-metric__delta--up">▲19%</span></div>
            <div class="pmw-metric__label">Affiliate clicks</div>
        </div>
        <div class="pmw-metric">
            <div class="pmw-metric__value">5/18</div>
            <div class="pmw-metric__label">Agents active</div>
        </div>
    </div>

    <div class="pmw-mc__row pmw-mc__row--thirds">
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Pipeline Status</h3>
            <div class="pmw-pipeline-stages">
                <?php foreach ( $stages as $s ) : ?>
                <div class="pmw-stage">
                    <span class="pmw-stage__name"><?php echo esc_html( $s['name'] ); ?></span>
                    <span class="pmw-stage__vals">
                        <?php if ( $s['done'] ) : ?><span class="pmw-dot pmw-dot--active"></span> <?php echo (int) $s['done']; ?><?php endif; ?>
                        <?php if ( $s['active'] ) : ?><span class="pmw-dot pmw-dot--bg"></span> <?php echo (int) $s['active']; ?> ●<?php endif; ?>
                        <?php if ( $s['queued'] ) : ?><span class="pmw-dot pmw-dot--queued"></span> <?php echo (int) $s['queued']; ?><?php endif; ?>
                        <?php if ( $s['err'] ) : ?><span class="pmw-dot pmw-dot--error"></span> <?php echo (int) $s['err']; ?> err<?php endif; ?>
                    </span>
                </div>
                <?php endforeach; ?>
            </div>
            <div class="pmw-active-tasks pmw-scroll-list">
                <?php foreach ( $active_tasks as $t ) : ?>
                <div class="pmw-task">
                    <div class="pmw-task__title">⟳ <?php echo esc_html( $t['title'] ); ?></div>
                    <div class="pmw-task__meta"><?php echo esc_html( $t['stage'] ); ?> • <?php echo esc_html( $t['agent'] ); ?> • Est. <?php echo esc_html( $t['eta'] ); ?></div>
                    <div class="pmw-task__cost">Cost so far: $<?php echo esc_html( number_format( $t['cost'], 2 ) ); ?> • Tokens: <?php echo esc_html( number_format( $t['tokens'] ) ); ?></div>
                    <div class="pmw-task__actions">
                        <button type="button" class="pmw-btn pmw-btn--ghost" style="font-size:11px;">View Draft</button>
                        <button type="button" class="pmw-btn pmw-btn--ghost" style="font-size:11px;">Pause</button>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Agent Status Board</h3>
            <div class="pmw-agent-board pmw-scroll-list">
                <?php foreach ( $tiers as $tier => $list ) : ?>
                <div class="pmw-agent-tier">
                    <div class="pmw-agent-tier__name"><?php echo esc_html( $tier ); ?></div>
                    <?php foreach ( $list as $a ) : ?>
                    <div class="pmw-agent-row">
                        <span class="pmw-dot pmw-dot--<?php echo $a['status'] === 'active' ? 'active' : ( $a['status'] === 'queued' ? 'queued' : 'idle' ); ?>"></span>
                        <span class="pmw-agent-row__name"><?php echo esc_html( $a['name'] ); ?></span>
                        <span class="pmw-agent-row__detail"><?php echo esc_html( $a['detail'] ); ?></span>
                    </div>
                    <?php endforeach; ?>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Alerts <?php echo count( $alerts ) ? '(' . count( $alerts ) . ' unread)' : ''; ?></h3>
            <?php if ( empty( $alerts ) ) : ?>
            <p class="pmw-text-muted" style="font-size: 13px; color: var(--mc-text-muted);">No unread alerts.</p>
            <?php else : ?>
            <div class="pmw-scroll-list">
                <?php foreach ( $alerts as $a ) : ?>
                <div class="pmw-alert">
                    <span class="pmw-alert__priority"><?php echo esc_html( $a['priority'] ?? 'MEDIUM' ); ?></span>
                    <?php echo esc_html( $a['message'] ?? '' ); ?>
                </div>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
        </div>
    </div>

    <div class="pmw-mc__row pmw-mc__row--4060">
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Content Queue — 8 items</h3>
            <div class="pmw-queue-section">
                <h4 class="pmw-queue-section__title">Awaiting Your Approval (<?php echo count( $awaiting ); ?>)</h4>
                <?php foreach ( $awaiting as $a ) : ?>
                <div class="pmw-queue-item">
                    <div class="pmw-queue-item__title"><?php echo esc_html( $a['title'] ); ?></div>
                    <div class="pmw-queue-item__meta">SEO <?php echo (int) $a['seo']; ?> • <?php echo (int) $a['words']; ?> words • Fact checked ✓</div>
                    <div class="pmw-queue-item__rev">Est. revenue: £<?php echo (int) $a['rev']; ?>/mo</div>
                    <div class="pmw-queue-item__actions">
                        <button type="button" class="pmw-btn pmw-btn--ghost" style="font-size:11px;">Preview</button>
                        <button type="button" class="pmw-btn pmw-btn--primary" style="font-size:11px;">Approve & Publish</button>
                        <button type="button" class="pmw-btn pmw-btn--ghost" style="font-size:11px;">Request Changes</button>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
            <div class="pmw-queue-section">
                <h4 class="pmw-queue-section__title">Published Today (<?php echo count( $published_today ); ?>)</h4>
                <?php foreach ( $published_today as $t ) : ?>
                <div class="pmw-queue-item pmw-queue-item--published"><?php echo esc_html( $t ); ?></div>
                <?php endforeach; ?>
            </div>
        </div>
        <div class="pmw-mc__col pmw-mc__col--right">
            <div class="pmw-panel">
                <h3 class="pmw-panel-title">Performance Intelligence</h3>
                <div class="pmw-perf-metrics">
                    <div class="pmw-perf-row">
                        <span>Sessions 7d:</span>
                        <span><strong><?php echo number_format( $sessions_7d ); ?></strong> <span class="pmw-metric__delta pmw-metric__delta--up">▲ 12%</span></span>
                    </div>
                    <div class="pmw-perf-row">
                        <span>Affiliate clicks:</span>
                        <span><strong><?php echo $aff_clicks; ?></strong> <span class="pmw-metric__delta pmw-metric__delta--up">▲ 19%</span></span>
                    </div>
                </div>
                <p class="pmw-text-muted" style="font-size: 12px; margin-top: 12px;">GA4 + Clarity. Connect bridge for live data.</p>
            </div>
            <div class="pmw-panel">
                <h3 class="pmw-panel-title">Intelligence Briefs</h3>
                <p class="pmw-text-muted" style="font-size: 13px;">Trend Analyst, Content Gap, Financial Intel. Connect bridge for live briefs.</p>
            </div>
        </div>
    </div>

    <div class="pmw-mc__row pmw-mc__row--thirds">
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">LLM Cost Summary</h3>
            <div class="pmw-cost-row">
                <span>TODAY</span>
                <span><strong><?php echo $cost_today ? sprintf( '$%.2f', $cost_today ) : '$0.84'; ?></strong></span>
            </div>
            <div class="pmw-cost-row">
                <span>THIS MONTH</span>
                <span><strong><?php echo $cost_month ? sprintf( '$%.2f', $cost_month ) : '$18.40'; ?></strong></span>
            </div>
            <div class="pmw-cost-row">
                <span>Revenue/Cost</span>
                <span class="pmw-metric__delta pmw-metric__delta--up"><?php echo $cost_month ? round( $rev_month / ( $cost_month * 0.8 ), 0 ) . ':1 ✓' : '—'; ?></span>
            </div>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Affiliate Performance</h3>
            <div class="pmw-cost-row">
                <span>MTD Clicks</span>
                <span><strong><?php echo $aff_clicks; ?></strong></span>
            </div>
            <div class="pmw-cost-row">
                <span>Est. commission</span>
                <span><strong>£<?php echo number_format( $rev_month ); ?></strong></span>
            </div>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Revenue Tracker — <?php echo esc_html( gmdate( 'F Y' ) ); ?></h3>
            <div class="pmw-cost-row">
                <span>Target</span>
                <span>£5,000</span>
            </div>
            <div class="pmw-cost-row">
                <span>Confirmed</span>
                <span><strong>£<?php echo number_format( $rev_month ); ?></strong></span>
            </div>
            <div class="pmw-progress" style="margin-top: 12px;">
                <div class="pmw-progress__fill" style="width: <?php echo min( 100, ( $rev_month / 5000 ) * 100 ); ?>%;"></div>
            </div>
        </div>
    </div>

    <p style="margin-top: 24px;">
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=pmw-agent-control' ) ); ?>" class="pmw-btn pmw-btn--ghost">Agent Control →</a>
    </p>
</div>
