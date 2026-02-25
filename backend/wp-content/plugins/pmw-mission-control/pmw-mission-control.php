<?php
/**
 * Plugin Name: PMW Mission Control
 * Plugin URI:  https://preciousmarketwatch.com
 * Description: WordPress dashboard for PMW agent pipeline — real-time status, cost, revenue, alerts.
 * Version:     1.0.0
 * Author:      Markus Mikely
 * License:     GPL-2.0+
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'PMW_MISSION_CONTROL_VERSION', '1.0.0' );

add_action( 'admin_menu', 'pmw_mission_control_replace_dashboard', 1 );
add_action( 'admin_init', 'pmw_mission_control_init' );
add_action( 'admin_bar_menu', 'pmw_mission_control_admin_bar', 999 );
add_action( 'admin_enqueue_scripts', 'pmw_mission_control_enqueue', 5 );

function pmw_mission_control_replace_dashboard() {
    remove_action( 'welcome_panel', 'wp_welcome_panel' );
    add_action( 'load-index.php', 'pmw_mission_control_load_dashboard' );
}

function pmw_mission_control_load_dashboard() {
    remove_all_actions( 'wp_dashboard_setup' );
    add_action( 'wp_dashboard_setup', 'pmw_mission_control_dashboard_setup' );
}

function pmw_mission_control_dashboard_setup() {
    wp_add_dashboard_widget(
        'pmw_mission_control',
        '',
        'pmw_mission_control_render',
        null,
        null,
        'normal',
        'high'
    );
    remove_meta_box( 'dashboard_browser_nag', 'dashboard', 'normal' );
    remove_meta_box( 'dashboard_php_nag', 'dashboard', 'normal' );
    remove_meta_box( 'dashboard_right_now', 'dashboard', 'normal' );
    remove_meta_box( 'dashboard_activity', 'dashboard', 'normal' );
    remove_meta_box( 'dashboard_quick_press', 'dashboard', 'side' );
    remove_meta_box( 'dashboard_primary', 'dashboard', 'side' );
    remove_meta_box( 'dashboard_site_health', 'dashboard', 'normal' );
    remove_meta_box( 'dashboard_incoming_links', 'dashboard', 'normal' );
    remove_meta_box( 'dashboard_plugins', 'dashboard', 'normal' );
}

function pmw_mission_control_init() {
    pmw_mission_control_ensure_options();
}

function pmw_mission_control_ensure_options() {
    $opts = [
        'pmw_pipeline_status'   => [],
        'pmw_agent_status'      => [],
        'pmw_alerts'            => [],
        'pmw_performance_summary' => [],
        'pmw_intelligence_briefs' => [],
        'pmw_affiliate_summary' => [],
        'pmw_revenue_summary'   => [],
        'pmw_cost_summary'      => [],
        'pmw_cost_log'          => [],
        'pmw_pipeline_commands' => [],
    ];
    foreach ( $opts as $k => $v ) {
        if ( get_option( $k ) === false ) {
            add_option( $k, $v );
        }
    }
}

function pmw_mission_control_enqueue( $hook ) {
    if ( $hook !== 'index.php' ) {
        return;
    }
    $base = plugin_dir_url( __FILE__ );
    wp_enqueue_style(
        'pmw-mission-control',
        $base . 'assets/mission-control.css',
        [],
        PMW_MISSION_CONTROL_VERSION
    );
}

function pmw_mission_control_render() {
    $pipeline  = get_option( 'pmw_pipeline_status', [] );
    $agents    = get_option( 'pmw_agent_status', [] );
    $alerts    = array_filter( get_option( 'pmw_alerts', [] ), fn( $a ) => empty( $a['dismissed'] ) );
    $perf      = get_option( 'pmw_performance_summary', [] );
    $intel     = get_option( 'pmw_intelligence_briefs', [] );
    $affiliate = get_option( 'pmw_affiliate_summary', [] );
    $revenue   = get_option( 'pmw_revenue_summary', [] );
    $costs     = get_option( 'pmw_cost_summary', [] );
    require plugin_dir_path( __FILE__ ) . 'templates/dashboard.php';
}

function pmw_mission_control_admin_bar( $bar ) {
    if ( ! current_user_can( 'edit_posts' ) ) {
        return;
    }
    $alerts   = array_filter( get_option( 'pmw_alerts', [] ), fn( $a ) => empty( $a['dismissed'] ) && ( $a['priority'] ?? '' ) === 'high' );
    $agents   = get_option( 'pmw_agent_status', [] );
    $active   = count( array_filter( $agents, fn( $a ) => ( $a['status'] ?? '' ) === 'active' ) );
    $costs    = get_option( 'pmw_cost_summary', [] );
    $cost_day = $costs['today_usd'] ?? 0;

    $bar->add_node( [
        'id'    => 'pmw-mission-control',
        'title' => sprintf(
            '<span class="pmw-bar">◆ PMW &nbsp;|&nbsp; <span class="pmw-bar__agents">%d active</span>'
            . ( count( $alerts ) ? ' &nbsp;|&nbsp; <span class="pmw-bar__alerts">⚡ %d alerts</span>' : '' )
            . ' &nbsp;|&nbsp; <span class="pmw-bar__cost">$%.2f today</span></span>',
            $active,
            count( $alerts ),
            (float) $cost_day
        ),
        'href'  => admin_url(),
        'meta'  => [ 'class' => 'pmw-admin-bar-node' ],
    ] );
}

add_action( 'admin_menu', 'pmw_mission_control_agent_control_page' );

function pmw_mission_control_agent_control_page() {
    add_submenu_page(
        null,
        'Agent Control',
        'Agent Control',
        'edit_posts',
        'pmw-agent-control',
        'pmw_mission_control_agent_control_render'
    );
}

function pmw_mission_control_agent_control_render() {
    require plugin_dir_path( __FILE__ ) . 'templates/agent-control.php';
}
