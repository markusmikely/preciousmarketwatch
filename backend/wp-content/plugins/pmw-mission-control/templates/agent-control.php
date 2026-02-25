<?php
if ( ! defined( 'ABSPATH' ) ) exit;

$commands = get_option( 'pmw_pipeline_commands', [] );
$commands = is_array( $commands ) ? array_slice( array_reverse( $commands ), 0, 20 ) : [];
?>
<div class="wrap pmw-mc">
    <h1 class="wp-heading-inline">Agent Control</h1>

    <div class="pmw-mc__row pmw-mc__row--thirds" style="margin-top: 24px;">
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Pipeline Approval Mode</h3>
            <p style="font-size: 13px; color: var(--mc-text-muted); margin: 0 0 12px;">
                Per-stage toggles: Auto-advance vs Hold for human approval. Recommended: hold before Publish only.
            </p>
            <p style="font-size: 12px; color: var(--mc-text-dim);">Configure in WP Options (pmw_approval_mode)</p>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Agent Schedules</h3>
            <p style="font-size: 13px; color: var(--mc-text-muted); margin: 0 0 12px;">
                Trend Analyst: every 4h. Content Gap: every 3 days. Quality Monitor: daily 03:00 UTC. Performance Intel: daily 06:00 UTC.
            </p>
        </div>
        <div class="pmw-panel">
            <h3 class="pmw-panel-title">Model Selection</h3>
            <p style="font-size: 13px; color: var(--mc-text-muted); margin: 0 0 12px;">
                Per agent: claude-opus-4 / claude-sonnet-4 / gpt-4o. Recommend: opus for Editor/Director, sonnet for writers.
            </p>
        </div>
    </div>

    <div class="pmw-panel" style="margin-top: 24px;">
        <h3 class="pmw-panel-title">Commands</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;">
            <button type="button" class="pmw-btn pmw-btn--primary">Generate Today's Brief</button>
            <button type="button" class="pmw-btn pmw-btn--ghost">Run Quality Audit Now</button>
            <button type="button" class="pmw-btn pmw-btn--ghost">Force Intelligence Refresh</button>
            <button type="button" class="pmw-btn pmw-btn--ghost">Pause All Agents</button>
            <button type="button" class="pmw-btn pmw-btn--ghost">Resume All Agents</button>
        </div>
        <p style="font-size: 12px; color: var(--mc-text-dim);">Connect bridge + LangGraph engine for commands to execute.</p>
    </div>

    <div class="pmw-panel" style="margin-top: 24px;">
        <h3 class="pmw-panel-title">Command Log</h3>
        <div class="pmw-scroll-list">
            <?php if ( empty( $commands ) ) : ?>
                <p style="font-size: 13px; color: var(--mc-text-muted);">No commands yet.</p>
            <?php else : ?>
                <table class="widefat striped" style="font-size: 12px;">
                    <thead>
                        <tr>
                            <th>Command</th>
                            <th>Status</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ( $commands as $c ) : ?>
                        <tr>
                            <td><?php echo esc_html( $c['command'] ?? '' ); ?></td>
                            <td><?php echo esc_html( $c['status'] ?? 'pending' ); ?></td>
                            <td><?php echo esc_html( $c['ts'] ?? '' ); ?></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>
    </div>
</div>
