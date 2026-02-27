<?php
/**
 * Plugin Name: PMW Core
 * Plugin URI:  https://preciousmarketwatch.com
 * Description: Core plugin for Precious Market Watch. Registers all custom post types, taxonomies, ACF field groups, and seeds default terms.
 * Version:     1.0.0
 * Author:      Markus Mikely
 * License:     GPL-2.0+
 */

if ( ! defined( 'ABSPATH' ) ) exit;

// Add this near the top of your plugin file for debugging
add_action('admin_init', function() {
    if ( current_user_can('manage_options') ) {
        $acf_pro_active = class_exists('acf_pro');
        $flexible_exists = function_exists('acf_get_field_type') && acf_get_field_type('flexible_content');
        
        if ( ! $acf_pro_active || ! $flexible_exists ) {
            add_action('admin_notices', function() use ($acf_pro_active, $flexible_exists) {
                echo '<div class="notice notice-warning"><p><strong>PMW Core Debug:</strong> ';
                echo 'ACF Pro active: ' . ($acf_pro_active ? '✅' : '❌') . ' | ';
                echo 'Flexible content available: ' . ($flexible_exists ? '✅' : '❌');
                echo '</p></div>';
            });
        }
    }
});

// ── CORS for REST API (Fix D: allow React frontend to call pmw/v1 from browser) ──
add_action( 'rest_api_init', function() {
    remove_filter( 'rest_pre_serve_request', 'rest_send_cors_headers' );
    add_filter( 'rest_pre_serve_request', function( $value ) {
        $origin  = function_exists( 'get_http_origin' ) ? get_http_origin() : '';
        $allowed = [
            'https://preciousmarketwatch.com',
            'https://www.preciousmarketwatch.com',
            'http://localhost:3000',
            'http://localhost:5173',
        ];
        if ( $origin && in_array( $origin, $allowed, true ) ) {
            header( 'Access-Control-Allow-Origin: ' . $origin );
        }
        header( 'Access-Control-Allow-Methods: POST, GET, OPTIONS' );
        header( 'Access-Control-Allow-Credentials: true' );
        header( 'Access-Control-Allow-Headers: Authorization, Content-Type' );
        return $value;
    } );
}, 15 );

// ─────────────────────────────────────────────
// 1. CUSTOM POST TYPES
// ─────────────────────────────────────────────

add_action( 'init', 'pmw_register_post_types' );
add_action( 'init', 'pmw_register_agent_meta', 20 );
add_action( 'init', 'pmw_register_tool_meta', 20 );
add_action( 'init', 'pmw_register_topic_meta', 20 );
add_action( 'init', 'pmw_register_article_topic_link_meta', 20 );
add_action( 'init', 'pmw_maybe_seed_agents', 20 );

function pmw_register_post_types() {

    // ── Market Insight (legacy; keep until migration complete) ──────────────────────
    register_post_type( 'market-insight', [
        'labels' => [
            'name'               => 'Market Insights',
            'singular_name'      => 'Market Insight',
            'add_new_item'       => 'Add New Market Insight',
            'edit_item'          => 'Edit Market Insight',
            'new_item'           => 'New Market Insight',
            'view_item'          => 'View Market Insight',
            'search_items'       => 'Search Market Insights',
            'not_found'          => 'No Market Insights found',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'market-insights' ],
        'supports'            => [ 'title', 'editor', 'excerpt', 'thumbnail', 'author', 'custom-fields' ],
        'menu_icon'           => 'dashicons-chart-line',
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'marketInsight',
        'graphql_plural_name' => 'marketInsights',
    ] );

    // ── News & Analysis (v2.0; replaces Market Insights after migration) ─────────
    register_post_type( 'pmw_news_analysis', [
        'labels'              => [
            'name'               => 'News & Analysis',
            'singular_name'      => 'Article',
            'add_new'            => 'Add New Article',
            'add_new_item'       => 'Add New Article',
            'edit_item'          => 'Edit Article',
            'new_item'           => 'New Article',
            'view_item'          => 'View Article',
            'search_items'       => 'Search Articles',
            'not_found'          => 'No articles found',
            'not_found_in_trash' => 'No articles found in trash',
            'menu_name'          => 'News & Analysis',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'news-analysis', 'with_front' => false ],
        'supports'            => [ 'title', 'editor', 'thumbnail', 'excerpt', 'author', 'custom-fields', 'revisions' ],
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'newsArticle',
        'graphql_plural_name' => 'newsArticles',
        'menu_icon'           => 'dashicons-analytics',
        'menu_position'       => 5,
        'show_in_nav_menus'   => true,
    ] );

    // ── Tools (v2.0; embed + custom React tools) ─────────────────────────────────
    register_post_type( 'pmw_tools', [
        'labels'              => [
            'name'               => 'Tools',
            'singular_name'      => 'Tool',
            'add_new'            => 'Add New Tool',
            'add_new_item'       => 'Add New Tool',
            'edit_item'          => 'Edit Tool',
            'view_item'          => 'View Tool',
            'search_items'       => 'Search Tools',
            'not_found'          => 'No tools found',
            'not_found_in_trash' => 'No tools found in trash',
            'menu_name'          => 'Tools',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'tools', 'with_front' => false ],
        'supports'            => [ 'title', 'editor', 'thumbnail', 'excerpt', 'custom-fields', 'revisions' ],
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'tool',
        'graphql_plural_name' => 'tools',
        'menu_icon'           => 'dashicons-hammer',
        'menu_position'       => 6,
        'show_in_nav_menus'   => true,
    ] );

    // ── Dealer ──────────────────────────────
    register_post_type( 'dealer', [
        'labels' => [
            'name'          => 'Dealers',
            'singular_name' => 'Dealer',
            'add_new_item'  => 'Add New Dealer',
            'edit_item'     => 'Edit Dealer',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'dealers' ],
        'supports'            => [ 'title', 'editor', 'excerpt', 'thumbnail', 'custom-fields' ],
        'menu_icon'           => 'dashicons-store',
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'dealer',
        'graphql_plural_name' => 'dealers',
    ] );

    // ── Affiliate Product ───────────────────
    register_post_type( 'affiliate-product', [
        'labels' => [
            'name'          => 'Affiliate Products',
            'singular_name' => 'Affiliate Product',
            'add_new_item'  => 'Add New Affiliate Product',
            'edit_item'     => 'Edit Affiliate Product',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'products' ],
        'supports'            => [ 'title', 'editor', 'excerpt', 'thumbnail', 'custom-fields' ],
        'menu_icon'           => 'dashicons-tag',
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'affiliateProduct',
        'graphql_plural_name' => 'affiliateProducts',
    ] );

    // ── Gem Index ───────────────────────────
    register_post_type( 'gem_index', [
        'labels' => [
            'name'               => 'Gem Index',
            'singular_name'      => 'Gem Index',
            'add_new_item'       => 'Add New Gem Index',
            'edit_item'          => 'Edit Gem Index',
            'new_item'           => 'New Gem Index',
            'view_item'          => 'View Gem Index',
            'search_items'       => 'Search Gem Indices',
            'not_found'          => 'No Gem Indices found',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'gem-index' ],
        'supports'            => [ 'title', 'editor', 'thumbnail' ],
        'menu_icon'           => 'dashicons-gem',
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'gemIndex',
        'graphql_plural_name' => 'gemIndices',
    ] );

    // ── Form Submission (contact form, etc.) ──
    register_post_type( 'form_submission', [
        'labels' => [
            'name'               => 'Form Submissions',
            'singular_name'      => 'Form Submission',
            'add_new_item'       => 'Add New Submission',
            'edit_item'          => 'Edit Submission',
            'search_items'       => 'Search Submissions',
            'not_found'          => 'No submissions found',
        ],
        'public'              => false,
        'show_ui'             => true,
        'show_in_menu'        => true,
        'menu_icon'           => 'dashicons-email-alt',
        'capability_type'     => 'post',
        'supports'            => [ 'title', 'custom-fields' ],
        'has_archive'        => false,
        'rewrite'             => false,
    ] );

    // ── PMW Agent (AI agent identity & display; workflow runs separately) ──
    register_post_type( 'pmw_agent', [
        'labels' => [
            'name'               => 'Agents',
            'singular_name'      => 'Agent',
            'add_new_item'       => 'Add New Agent',
            'edit_item'          => 'Edit Agent',
            'new_item'           => 'New Agent',
            'view_item'          => 'View Agent',
            'search_items'       => 'Search Agents',
            'not_found'          => 'No agents found',
            'all_items'          => 'All Agents',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'agents' ],
        'supports'            => [ 'title', 'editor', 'excerpt', 'thumbnail', 'custom-fields' ],
        'menu_icon'           => 'dashicons-groups',
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'pmwAgent',
        'graphql_plural_name' => 'pmwAgents',
    ] );

    // ── Content Topics (pmw_topic CPT; agent workflow source of truth) ─────────────
    register_post_type( 'pmw_topic', [
        'label'        => 'Content Topics',
        'public'       => false,
        'show_ui'      => true,
        'show_in_rest' => true,
        'rest_base'    => 'pmw-topics',
        'supports'     => [ 'title', 'editor', 'custom-fields' ],
        'menu_icon'    => 'dashicons-calendar-alt',
        'labels'       => [
            'name'          => 'Content Topics',
            'singular_name' => 'Topic',
            'add_new_item'  => 'Add New Topic',
            'edit_item'     => 'Edit Topic',
        ],
    ] );
}

// ── PMW Agent Profile Meta (schema from brief) ──
function pmw_register_agent_meta() {
    $meta_fields = [
        [ 'pmw_slug', 'string', 'URL-safe identifier e.g. research-analyst' ],
        [ 'pmw_display_name', 'string', 'Full name e.g. Marcus Webb' ],
        [ 'pmw_title', 'string', 'e.g. The Research Analyst' ],
        [ 'pmw_role', 'string', 'e.g. Market Research & Data Specialist' ],
        [ 'pmw_tier', 'string', 'One of: intelligence, editorial, production' ],
        [ 'pmw_model_family', 'string', 'e.g. Claude (Anthropic)' ],
        [ 'pmw_bio', 'string', 'Long text, plain text paragraph' ],
        [ 'pmw_personality', 'string', 'Long text, plain text paragraph' ],
        [ 'pmw_quirks', 'string', 'JSON-encoded array of quirk strings' ],
        [ 'pmw_specialisms', 'string', 'JSON-encoded array of specialism strings' ],
        [ 'pmw_status', 'string', 'One of: active, in-development' ],
        [ 'pmw_eta', 'string', 'Optional. Only if status is in-development.' ],
        [ 'pmw_avatar_image_url', 'string', 'URL to uploaded image. Empty until uploaded.' ],
        [ 'pmw_avatar_video_url', 'string', 'URL to uploaded video. Empty until uploaded.' ],
        [ 'pmw_display_order', 'integer', 'Controls order on Team page. 1 = first.' ],
    ];
    foreach ( $meta_fields as $f ) {
        register_post_meta( 'pmw_agent', $f[0], [
            'show_in_rest' => true,
            'single'       => true,
            'type'         => $f[1],
            'description'  => $f[2],
        ] );
    }
}

add_action( 'add_meta_boxes', 'pmw_agent_profile_meta_box' );
add_action( 'add_meta_boxes', 'pmw_tools_meta_box' );
add_action( 'add_meta_boxes', 'pmw_topic_meta_box' );
add_action( 'add_meta_boxes', 'pmw_article_topic_link_meta_box' );
add_action( 'save_post_pmw_agent', 'pmw_save_agent_profile_meta', 10, 2 );
add_action( 'save_post_pmw_tools', 'pmw_save_tool_meta', 10, 2 );
add_action( 'save_post_pmw_topic', 'pmw_save_topic_meta', 10, 2 );
add_action( 'save_post', 'pmw_save_article_topic_link', 10, 2 );
add_filter( 'upload_mimes', 'pmw_allow_mp4_upload' );
add_action( 'admin_enqueue_scripts', 'pmw_agent_profile_admin_scripts' );
add_action( 'wp_ajax_pmw_agent_upload_avatar_image', 'pmw_agent_ajax_upload_avatar_image' );
add_action( 'wp_ajax_pmw_agent_upload_avatar_video', 'pmw_agent_ajax_upload_avatar_video' );

function pmw_allow_mp4_upload( $mimes ) {
    $mimes['mp4'] = 'video/mp4';
    return $mimes;
}

function pmw_agent_profile_admin_scripts( $hook ) {
    global $post;
    if ( $hook !== 'post.php' && $hook !== 'post-new.php' ) return;
    if ( ! $post || $post->post_type !== 'pmw_agent' ) return;

    wp_enqueue_script(
        'pmw-agent-profile-upload',
        plugins_url( 'pmw-agent-upload.js', __FILE__ ),
        [ 'jquery' ],
        '1.0',
        true
    );
    wp_localize_script( 'pmw-agent-profile-upload', 'pmwAgentUpload', [
        'ajaxUrl' => admin_url( 'admin-ajax.php' ),
        'nonce'   => wp_create_nonce( 'pmw_agent_upload_avatar' ),
        'postId'  => $post->ID,
    ] );
}

function pmw_agent_ajax_upload_avatar_image() {
    check_ajax_referer( 'pmw_agent_upload_avatar', 'nonce' );
    $post_id = isset( $_POST['post_id'] ) ? (int) $_POST['post_id'] : 0;
    if ( ! $post_id || ! current_user_can( 'edit_post', $post_id ) ) {
        wp_send_json_error( [ 'message' => 'Unauthorized' ] );
    }
    if ( empty( $_FILES['file'] ) || ! is_uploaded_file( $_FILES['file']['tmp_name'] ) ) {
        wp_send_json_error( [ 'message' => 'No file uploaded' ] );
    }
    $file = $_FILES['file'];
    $allowed = [ 'image/jpeg', 'image/png', 'image/webp' ];
    if ( ! in_array( $file['type'] ?? '', $allowed, true ) ) {
        wp_send_json_error( [ 'message' => 'Unsupported file type. Use JPEG, PNG, or WebP.' ] );
    }
    if ( ( $file['size'] ?? 0 ) > 5 * 1024 * 1024 ) {
        wp_send_json_error( [ 'message' => 'File exceeds 5MB limit.' ] );
    }
    require_once ABSPATH . 'wp-admin/includes/file.php';
    require_once ABSPATH . 'wp-admin/includes/media.php';
    require_once ABSPATH . 'wp-admin/includes/image.php';
    $overrides = [ 'test_form' => false, 'mimes' => [ 'jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'png' => 'image/png', 'webp' => 'image/webp' ] ];
    $upload = wp_handle_upload( $file, $overrides );
    if ( isset( $upload['error'] ) ) {
        wp_send_json_error( [ 'message' => $upload['error'] ] );
    }
    $attachment = [
        'post_mime_type' => $upload['type'],
        'post_title'     => sanitize_file_name( pathinfo( $file['name'], PATHINFO_FILENAME ) ),
        'post_content'   => '',
        'post_status'    => 'inherit',
    ];
    $attach_id = wp_insert_attachment( $attachment, $upload['file'], $post_id );
    if ( is_wp_error( $attach_id ) ) {
        wp_send_json_error( [ 'message' => $attach_id->get_error_message() ] );
    }
    wp_generate_attachment_metadata( $attach_id, $upload['file'] );
    update_post_meta( $post_id, 'pmw_avatar_image_url', $upload['url'] );
    wp_send_json_success( [ 'avatar_image_url' => $upload['url'], 'attachment_id' => $attach_id ] );
}

function pmw_agent_ajax_upload_avatar_video() {
    check_ajax_referer( 'pmw_agent_upload_avatar', 'nonce' );
    $post_id = isset( $_POST['post_id'] ) ? (int) $_POST['post_id'] : 0;
    if ( ! $post_id || ! current_user_can( 'edit_post', $post_id ) ) {
        wp_send_json_error( [ 'message' => 'Unauthorized' ] );
    }
    if ( empty( $_FILES['file'] ) || ! is_uploaded_file( $_FILES['file']['tmp_name'] ) ) {
        wp_send_json_error( [ 'message' => 'No file uploaded' ] );
    }
    $file = $_FILES['file'];
    if ( ( $file['type'] ?? '' ) !== 'video/mp4' ) {
        wp_send_json_error( [ 'message' => 'Unsupported file type. Use MP4.' ] );
    }
    if ( ( $file['size'] ?? 0 ) > 50 * 1024 * 1024 ) {
        wp_send_json_error( [ 'message' => 'File exceeds 50MB limit.' ] );
    }
    require_once ABSPATH . 'wp-admin/includes/file.php';
    require_once ABSPATH . 'wp-admin/includes/media.php';
    require_once ABSPATH . 'wp-admin/includes/image.php';
    $overrides = [ 'test_form' => false, 'mimes' => [ 'mp4' => 'video/mp4' ] ];
    $upload = wp_handle_upload( $file, $overrides );
    if ( isset( $upload['error'] ) ) {
        wp_send_json_error( [ 'message' => $upload['error'] ] );
    }
    $attachment = [
        'post_mime_type' => $upload['type'],
        'post_title'     => sanitize_file_name( pathinfo( $file['name'], PATHINFO_FILENAME ) ),
        'post_content'   => '',
        'post_status'    => 'inherit',
    ];
    $attach_id = wp_insert_attachment( $attachment, $upload['file'], $post_id );
    if ( is_wp_error( $attach_id ) ) {
        wp_send_json_error( [ 'message' => $attach_id->get_error_message() ] );
    }
    wp_generate_attachment_metadata( $attach_id, $upload['file'] );
    update_post_meta( $post_id, 'pmw_avatar_video_url', $upload['url'] );
    wp_send_json_success( [ 'avatar_video_url' => $upload['url'], 'attachment_id' => $attach_id ] );
}

function pmw_agent_profile_meta_box() {
    add_meta_box(
        'pmw_agent_profile',
        __( 'Agent Profile', 'pmw-core' ),
        'pmw_agent_profile_meta_box_cb',
        'pmw_agent',
        'normal'
    );
}

function pmw_agent_profile_meta_box_cb( $post ) {
    wp_nonce_field( 'pmw_agent_profile_save', 'pmw_agent_profile_nonce' );

    $fields = [
        'pmw_slug'             => [ 'label' => 'Slug', 'type' => 'text', 'group' => 'identity' ],
        'pmw_display_name'     => [ 'label' => 'Display name', 'type' => 'text', 'group' => 'identity' ],
        'pmw_title'            => [ 'label' => 'Title', 'type' => 'text', 'group' => 'identity' ],
        'pmw_role'             => [ 'label' => 'Role', 'type' => 'text', 'group' => 'identity' ],
        'pmw_tier'             => [ 'label' => 'Tier', 'type' => 'select', 'choices' => [ 'intelligence' => 'intelligence', 'editorial' => 'editorial', 'production' => 'production' ], 'group' => 'identity' ],
        'pmw_model_family'     => [ 'label' => 'Model family', 'type' => 'text', 'group' => 'identity' ],
        'pmw_display_order'    => [ 'label' => 'Display order', 'type' => 'number', 'group' => 'identity' ],
        'pmw_bio'              => [ 'label' => 'Bio', 'type' => 'textarea', 'group' => 'content' ],
        'pmw_personality'      => [ 'label' => 'Personality', 'type' => 'textarea', 'group' => 'content' ],
        'pmw_quirks'           => [ 'label' => 'Quirks (one per line)', 'type' => 'textarea', 'group' => 'content' ],
        'pmw_specialisms'      => [ 'label' => 'Specialisms (one per line)', 'type' => 'textarea', 'group' => 'content' ],
        'pmw_status'           => [ 'label' => 'Status', 'type' => 'select', 'choices' => [ 'active' => 'active', 'in-development' => 'in-development' ], 'group' => 'status' ],
        'pmw_eta'              => [ 'label' => 'ETA (shown if in-development)', 'type' => 'text', 'group' => 'status' ],
        'pmw_avatar_image_url' => [ 'label' => 'Avatar image', 'type' => 'avatar_upload', 'group' => 'media' ],
        'pmw_avatar_video_url' => [ 'label' => 'Avatar video', 'type' => 'avatar_video_upload', 'group' => 'media' ],
    ];

    $groups = [ 'identity' => 'Identity', 'content' => 'Content', 'status' => 'Status', 'media' => 'Media' ];
    foreach ( $groups as $gkey => $gtitle ) {
        echo '<h4 style="margin:1em 0 0.5em;">' . esc_html( $gtitle ) . '</h4>';
        echo '<table class="form-table" role="presentation"><tbody>';
        foreach ( $fields as $key => $f ) {
            if ( ( $f['group'] ?? '' ) !== $gkey ) continue;
            $val = get_post_meta( $post->ID, $key, true );
            if ( $key === 'pmw_quirks' || $key === 'pmw_specialisms' ) {
                $arr = is_string( $val ) ? json_decode( $val, true ) : [];
                $val = is_array( $arr ) ? implode( "\n", $arr ) : (string) $val;
            }
            echo '<tr><th scope="row"><label for="' . esc_attr( $key ) . '">' . esc_html( $f['label'] ) . '</label></th><td>';
            if ( $f['type'] === 'avatar_upload' ) {
                echo '<div class="pmw-avatar-upload" data-meta="pmw_avatar_image_url" data-action="pmw_agent_upload_avatar_image">';
                echo '<input type="hidden" name="' . esc_attr( $key ) . '" id="' . esc_attr( $key ) . '" value="' . esc_attr( $val ) . '" />';
                if ( $val ) {
                    echo '<p><img src="' . esc_url( $val ) . '" alt="" class="pmw-current-preview" style="max-width: 150px; height: auto; display: block; margin-bottom: 8px;" /></p>';
                    echo '<p class="description pmw-current-url">Current: ' . esc_html( $val ) . '</p>';
                }
                echo '<p><input type="file" accept="image/jpeg,image/png,image/webp" class="pmw-avatar-file-input" />';
                echo ' <button type="button" class="button pmw-avatar-upload-btn">Upload image</button>';
                echo ' <span class="pmw-upload-status" style="margin-left: 8px;"></span></p>';
                echo '<p class="description">JPEG, PNG or WebP. Max 5MB.</p></div>';
            } elseif ( $f['type'] === 'avatar_video_upload' ) {
                echo '<div class="pmw-avatar-upload" data-meta="pmw_avatar_video_url" data-action="pmw_agent_upload_avatar_video">';
                echo '<input type="hidden" name="' . esc_attr( $key ) . '" id="' . esc_attr( $key ) . '" value="' . esc_attr( $val ) . '" />';
                if ( $val ) {
                    echo '<p class="description pmw-current-url">Current: ' . esc_html( $val ) . '</p>';
                }
                echo '<p><input type="file" accept="video/mp4" class="pmw-avatar-file-input" />';
                echo ' <button type="button" class="button pmw-avatar-upload-btn">Upload video</button>';
                echo ' <span class="pmw-upload-status" style="margin-left: 8px;"></span></p>';
                echo '<p class="description">MP4 only. Max 50MB.</p></div>';
            } elseif ( $f['type'] === 'textarea' ) {
                echo '<textarea id="' . esc_attr( $key ) . '" name="' . esc_attr( $key ) . '" rows="4" class="large-text">' . esc_textarea( $val ) . '</textarea>';
            } elseif ( $f['type'] === 'select' ) {
                echo '<select id="' . esc_attr( $key ) . '" name="' . esc_attr( $key ) . '">';
                foreach ( $f['choices'] ?? [] as $opt => $lbl ) {
                    echo '<option value="' . esc_attr( $opt ) . '" ' . selected( $val, $opt, false ) . '>' . esc_html( $lbl ) . '</option>';
                }
                echo '</select>';
            } else {
                echo '<input type="' . esc_attr( $f['type'] ) . '" id="' . esc_attr( $key ) . '" name="' . esc_attr( $key ) . '" value="' . esc_attr( $val ) . '" class="regular-text" />';
            }
            echo '</td></tr>';
        }
        echo '</tbody></table>';
    }
}

function pmw_save_agent_profile_meta( $post_id, $post ) {
    if ( ! isset( $_POST['pmw_agent_profile_nonce'] ) || ! wp_verify_nonce( $_POST['pmw_agent_profile_nonce'], 'pmw_agent_profile_save' ) ) return;
    if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) return;
    if ( ! current_user_can( 'edit_post', $post_id ) ) return;

    $text_keys = [ 'pmw_slug', 'pmw_display_name', 'pmw_title', 'pmw_role', 'pmw_tier', 'pmw_model_family', 'pmw_bio', 'pmw_personality', 'pmw_status', 'pmw_eta', 'pmw_avatar_image_url', 'pmw_avatar_video_url' ];
    foreach ( $text_keys as $key ) {
        if ( isset( $_POST[ $key ] ) ) {
            $v = sanitize_text_field( wp_unslash( $_POST[ $key ] ) );
            if ( in_array( $key, [ 'pmw_bio', 'pmw_personality' ], true ) ) {
                $v = wp_strip_all_tags( $v );
            }
            update_post_meta( $post_id, $key, $v );
        }
    }
    if ( isset( $_POST['pmw_display_order'] ) && is_numeric( $_POST['pmw_display_order'] ) ) {
        update_post_meta( $post_id, 'pmw_display_order', (int) $_POST['pmw_display_order'] );
    }
    foreach ( [ 'pmw_quirks', 'pmw_specialisms' ] as $key ) {
        if ( isset( $_POST[ $key ] ) ) {
            $lines = array_filter( array_map( 'trim', explode( "\n", wp_unslash( $_POST[ $key ] ) ) ) );
            update_post_meta( $post_id, $key, wp_json_encode( $lines ) );
        }
    }
}

// ── PMW Tools meta (v2.0 brief) ─────────────────────────────────────────────────
function pmw_register_tool_meta() {
    $meta = [
        [ 'pmw_tool_type', 'string', 'calculator | comparison-table | portfolio-tracker | price-chart' ],
        [ 'pmw_implementation', 'string', 'custom-react | embed | shortcode' ],
        [ 'pmw_react_component', 'string', 'React component slug (Phase 2)' ],
        [ 'pmw_embed_code', 'string', 'Raw HTML/JS for embed' ],
        [ 'pmw_affiliate_partner', 'string', 'bullionvault | royal-mint | chards | hatton-garden | none' ],
        [ 'pmw_affiliate_cta_text', 'string', 'Button label' ],
        [ 'pmw_affiliate_cta_url', 'string', 'Affiliate URL' ],
        [ 'pmw_affiliate_cta_position', 'string', 'after-result | inline | sidebar' ],
        [ 'pmw_show_disclaimer', 'boolean', 'Show disclaimer' ],
        [ 'pmw_disclaimer_text', 'string', 'Override disclaimer' ],
        [ 'pmw_related_tools', 'string', 'JSON array of post IDs' ],
        [ 'pmw_display_order', 'integer', 'Order on hub' ],
        [ 'pmw_is_featured', 'boolean', 'Featured on hub' ],
        [ 'pmw_metal_relevance', 'string', 'JSON array: gold, silver, etc.' ],
        [ 'pmw_tool_status', 'string', 'live | coming-soon | draft' ],
    ];
    foreach ( $meta as $m ) {
        register_post_meta( 'pmw_tools', $m[0], [
            'show_in_rest' => true,
            'single'       => true,
            'type'         => $m[1],
            'description'  => $m[2],
        ] );
    }
}

// ── Content Topics (pmw_topic) meta ──────────────────────────────────────────────
function pmw_register_topic_meta() {
    $fields = [
        'pmw_target_keyword'    => [ 'type' => 'string'  ],
        'pmw_summary'           => [ 'type' => 'string'  ],
        'pmw_include_keywords'  => [ 'type' => 'string'  ],
        'pmw_exclude_keywords'  => [ 'type' => 'string'  ],
        'pmw_asset_class'       => [ 'type' => 'string'  ],
        'pmw_product_type'      => [ 'type' => 'string'  ],
        'pmw_geography'         => [ 'type' => 'string'  ],
        'pmw_is_buy_side'       => [ 'type' => 'boolean' ],
        'pmw_intent_stage'      => [ 'type' => 'string'  ],
        'pmw_priority'          => [ 'type' => 'integer' ],
        'pmw_schedule_cron'     => [ 'type' => 'string'  ],
        'pmw_agent_status'      => [ 'type' => 'string'  ],
        'pmw_last_run_at'       => [ 'type' => 'string'  ],
        'pmw_run_count'         => [ 'type' => 'integer' ],
        'pmw_last_run_id'       => [ 'type' => 'integer' ],
        'pmw_last_wp_post_id'   => [ 'type' => 'integer' ],
        'pmw_wp_category_id'    => [ 'type' => 'integer' ],
        'pmw_affiliate_page_id' => [ 'type' => 'integer' ],
    ];
    foreach ( $fields as $key => $config ) {
        register_post_meta( 'pmw_topic', $key, [
            'type'         => $config['type'],
            'single'       => true,
            'show_in_rest' => true,
            'default'      => $config['type'] === 'integer' ? 0 : ( $config['type'] === 'boolean' ? false : '' ),
        ] );
    }
}

// ── Article → Topic link (post ID of pmw_topic) ───────────────────────────────────
function pmw_register_article_topic_link_meta() {
    foreach ( [ 'post', 'pmw_news_analysis' ] as $pt ) {
        register_post_meta( $pt, 'pmw_topic_id', [
            'type'         => 'integer',
            'single'       => true,
            'show_in_rest' => true,
            'default'      => 0,
        ] );
    }
}

function pmw_tools_meta_box() {
    add_meta_box( 'pmw_tool_details', __( 'Tool Details', 'pmw-core' ), 'pmw_tools_meta_box_cb', 'pmw_tools', 'normal' );
}

function pmw_tools_meta_box_cb( $post ) {
    wp_nonce_field( 'pmw_tool_save', 'pmw_tool_nonce' );
    $impl = get_post_meta( $post->ID, 'pmw_implementation', true ) ?: 'embed';
    $tool_type = get_post_meta( $post->ID, 'pmw_tool_type', true );
    $status = get_post_meta( $post->ID, 'pmw_tool_status', true );
    $order = get_post_meta( $post->ID, 'pmw_display_order', true );
    $featured = get_post_meta( $post->ID, 'pmw_is_featured', true );
    $react = get_post_meta( $post->ID, 'pmw_react_component', true );
    $embed = get_post_meta( $post->ID, 'pmw_embed_code', true );
    $partner = get_post_meta( $post->ID, 'pmw_affiliate_partner', true );
    $cta_text = get_post_meta( $post->ID, 'pmw_affiliate_cta_text', true );
    $cta_url = get_post_meta( $post->ID, 'pmw_affiliate_cta_url', true );
    $cta_pos = get_post_meta( $post->ID, 'pmw_affiliate_cta_position', true );
    $show_disc = get_post_meta( $post->ID, 'pmw_show_disclaimer', true );
    $disc_text = get_post_meta( $post->ID, 'pmw_disclaimer_text', true );
    $metal_rel = get_post_meta( $post->ID, 'pmw_metal_relevance', true );
    $metal_arr = is_string( $metal_rel ) ? json_decode( $metal_rel, true ) : [];
    if ( ! is_array( $metal_arr ) ) $metal_arr = [];
    $related_tools = get_post_meta( $post->ID, 'pmw_related_tools', true );
    $metals = [ 'gold' => 'Gold', 'silver' => 'Silver', 'platinum' => 'Platinum', 'palladium' => 'Palladium', 'gemstones' => 'Gemstones', 'all' => 'All' ];

    echo '<div class="pmw-tool-meta">';
    echo '<h4 style="margin:1em 0 0.5em;">Tool identity</h4>';
    echo '<table class="form-table"><tr><th>Tool type</th><td><select name="pmw_tool_type">';
    foreach ( [ 'calculator' => 'Calculator', 'comparison-table' => 'Comparison Table', 'portfolio-tracker' => 'Portfolio Tracker', 'price-chart' => 'Price Chart' ] as $v => $l ) {
        echo '<option value="' . esc_attr( $v ) . '" ' . selected( $tool_type, $v, false ) . '>' . esc_html( $l ) . '</option>';
    }
    echo '</select></td></tr>';
    echo '<tr><th>Implementation</th><td><select name="pmw_implementation" id="pmw_implementation">';
    foreach ( [ 'embed' => 'Embed', 'custom-react' => 'Custom React', 'shortcode' => 'Shortcode' ] as $v => $l ) {
        echo '<option value="' . esc_attr( $v ) . '" ' . selected( $impl, $v, false ) . '>' . esc_html( $l ) . '</option>';
    }
    echo '</select></td></tr>';
    echo '<tr id="pmw_react_row"><th>React component ID</th><td><input type="text" name="pmw_react_component" value="' . esc_attr( $react ) . '" class="regular-text" /></td></tr>';
    echo '<tr id="pmw_embed_row"><th>Embed code</th><td><textarea name="pmw_embed_code" rows="6" class="large-text code">' . esc_textarea( $embed ) . '</textarea></td></tr>';
    echo '<tr><th>Status</th><td><select name="pmw_tool_status">';
    foreach ( [ 'live' => 'Live', 'coming-soon' => 'Coming Soon', 'draft' => 'Draft' ] as $v => $l ) {
        echo '<option value="' . esc_attr( $v ) . '" ' . selected( $status, $v, false ) . '>' . esc_html( $l ) . '</option>';
    }
    echo '</select></td></tr>';
    echo '<tr><th>Display order</th><td><input type="number" name="pmw_display_order" value="' . esc_attr( $order ) . '" /></td></tr>';
    echo '<tr><th>Is featured</th><td><input type="checkbox" name="pmw_is_featured" value="1" ' . checked( $featured, '1', false ) . ' /></td></tr>';
    echo '</table>';

    echo '<h4 style="margin:1em 0 0.5em;">Affiliate CTA</h4>';
    echo '<table class="form-table">';
    echo '<tr><th>Affiliate partner</th><td><select name="pmw_affiliate_partner">';
    foreach ( [ 'none' => 'None', 'bullionvault' => 'BullionVault', 'royal-mint' => 'Royal Mint', 'chards' => 'Chards', 'hatton-garden' => 'Hatton Garden' ] as $v => $l ) {
        echo '<option value="' . esc_attr( $v ) . '" ' . selected( $partner, $v, false ) . '>' . esc_html( $l ) . '</option>';
    }
    echo '</select></td></tr>';
    echo '<tr><th>CTA text</th><td><input type="text" name="pmw_affiliate_cta_text" value="' . esc_attr( $cta_text ) . '" class="regular-text" /></td></tr>';
    echo '<tr><th>CTA URL</th><td><input type="url" name="pmw_affiliate_cta_url" value="' . esc_attr( $cta_url ) . '" class="regular-text" /></td></tr>';
    echo '<tr><th>CTA position</th><td><select name="pmw_affiliate_cta_position">';
    foreach ( [ 'after-result' => 'After result', 'inline' => 'Inline', 'sidebar' => 'Sidebar' ] as $v => $l ) {
        echo '<option value="' . esc_attr( $v ) . '" ' . selected( $cta_pos, $v, false ) . '>' . esc_html( $l ) . '</option>';
    }
    echo '</select></td></tr>';
    echo '<tr><th>Show disclaimer</th><td><input type="checkbox" name="pmw_show_disclaimer" value="1" ' . checked( $show_disc, '1', false ) . ' /></td></tr>';
    echo '<tr><th>Disclaimer text</th><td><textarea name="pmw_disclaimer_text" rows="2" class="large-text">' . esc_textarea( $disc_text ) . '</textarea></td></tr>';
    echo '</table>';

    echo '<h4 style="margin:1em 0 0.5em;">Relationships</h4>';
    echo '<table class="form-table"><tr><th>Metal relevance</th><td>';
    foreach ( $metals as $v => $l ) {
        $checked = in_array( $v, $metal_arr, true ) ? ' checked' : '';
        echo '<label style="display:block;"><input type="checkbox" name="pmw_metal_relevance[]" value="' . esc_attr( $v ) . '"' . $checked . ' /> ' . esc_html( $l ) . '</label>';
    }
    echo '<tr><th>Related tools</th><td><input type="text" name="pmw_related_tools" value="' . esc_attr( is_string( $related_tools ) ? $related_tools : '' ) . '" class="regular-text" placeholder="JSON array of post IDs" /></td></tr></table>';
    echo '</div>';
}

function pmw_save_tool_meta( $post_id, $post ) {
    if ( ! isset( $_POST['pmw_tool_nonce'] ) || ! wp_verify_nonce( $_POST['pmw_tool_nonce'], 'pmw_tool_save' ) ) return;
    if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) return;
    if ( ! current_user_can( 'edit_post', $post_id ) ) return;
    $keys = [ 'pmw_tool_type', 'pmw_implementation', 'pmw_react_component', 'pmw_embed_code', 'pmw_affiliate_partner', 'pmw_affiliate_cta_text', 'pmw_affiliate_cta_url', 'pmw_affiliate_cta_position', 'pmw_disclaimer_text', 'pmw_related_tools', 'pmw_tool_status' ];
    foreach ( $keys as $key ) {
        if ( isset( $_POST[ $key ] ) ) {
            $v = sanitize_text_field( wp_unslash( $_POST[ $key ] ) );
            if ( $key === 'pmw_embed_code' || $key === 'pmw_disclaimer_text' ) {
                $v = wp_unslash( $_POST[ $key ] );
            }
            if ( $key === 'pmw_related_tools' ) {
                $raw = wp_unslash( $_POST[ $key ] );
                $dec = json_decode( $raw );
                $v = is_array( $dec ) ? wp_json_encode( $dec ) : ( is_string( $raw ) ? $raw : '[]' );
            }
            update_post_meta( $post_id, $key, $v );
        }
    }
    if ( isset( $_POST['pmw_metal_relevance'] ) && is_array( $_POST['pmw_metal_relevance'] ) ) {
        update_post_meta( $post_id, 'pmw_metal_relevance', wp_json_encode( array_map( 'sanitize_text_field', wp_unslash( $_POST['pmw_metal_relevance'] ) ) ) );
    }
    if ( isset( $_POST['pmw_display_order'] ) && is_numeric( $_POST['pmw_display_order'] ) ) {
        update_post_meta( $post_id, 'pmw_display_order', (int) $_POST['pmw_display_order'] );
    }
    update_post_meta( $post_id, 'pmw_show_disclaimer', isset( $_POST['pmw_show_disclaimer'] ) && $_POST['pmw_show_disclaimer'] === '1' ? '1' : '0' );
    update_post_meta( $post_id, 'pmw_is_featured', isset( $_POST['pmw_is_featured'] ) && $_POST['pmw_is_featured'] === '1' ? '1' : '0' );
}

function pmw_topic_meta_box() {
    add_meta_box( 'pmw_topic_details', __( 'Topic Details', 'pmw-core' ), 'pmw_topic_meta_box_cb', 'pmw_topic', 'normal' );
}

function pmw_topic_meta_box_cb( $post ) {
    wp_nonce_field( 'pmw_topic_save', 'pmw_topic_nonce' );
    $editable = [ 'pmw_target_keyword', 'pmw_summary', 'pmw_include_keywords', 'pmw_exclude_keywords', 'pmw_asset_class', 'pmw_product_type', 'pmw_geography', 'pmw_is_buy_side', 'pmw_intent_stage', 'pmw_priority', 'pmw_schedule_cron' ];
    $readonly = [ 'pmw_agent_status', 'pmw_last_run_at', 'pmw_run_count', 'pmw_last_run_id', 'pmw_last_wp_post_id', 'pmw_wp_category_id', 'pmw_affiliate_page_id' ];
    echo '<table class="form-table">';
    foreach ( $editable as $key ) {
        $v = get_post_meta( $post->ID, $key, true );
        $label = str_replace( 'pmw_', '', $key );
        $label = ucwords( str_replace( '_', ' ', $label ) );
        if ( $key === 'pmw_is_buy_side' ) {
            echo '<tr><th>' . esc_html( $label ) . '</th><td><input type="checkbox" name="' . esc_attr( $key ) . '" value="1" ' . checked( $v, '1', false ) . ' /></td></tr>';
        } elseif ( $key === 'pmw_summary' ) {
            echo '<tr><th>' . esc_html( $label ) . '</th><td><textarea name="' . esc_attr( $key ) . '" rows="3" class="large-text">' . esc_textarea( $v ) . '</textarea></td></tr>';
        } else {
            echo '<tr><th>' . esc_html( $label ) . '</th><td><input type="text" name="' . esc_attr( $key ) . '" value="' . esc_attr( $v ) . '" class="regular-text" /></td></tr>';
        }
    }
    echo '<tr><td colspan="2"><em style="color:#666;">Display-only (agent-managed):</em></td></tr>';
    foreach ( $readonly as $key ) {
        $v = get_post_meta( $post->ID, $key, true );
        $label = str_replace( 'pmw_', '', $key );
        $label = ucwords( str_replace( '_', ' ', $label ) );
        echo '<tr><th>' . esc_html( $label ) . '</th><td><code>' . esc_html( (string) $v ) . '</code></td></tr>';
    }
    echo '</table>';
}

function pmw_save_topic_meta( $post_id, $post ) {
    if ( ! isset( $_POST['pmw_topic_nonce'] ) || ! wp_verify_nonce( $_POST['pmw_topic_nonce'], 'pmw_topic_save' ) ) return;
    if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) return;
    if ( ! current_user_can( 'edit_post', $post_id ) ) return;
    $keys = [ 'pmw_target_keyword', 'pmw_summary', 'pmw_include_keywords', 'pmw_exclude_keywords', 'pmw_asset_class', 'pmw_product_type', 'pmw_geography', 'pmw_intent_stage', 'pmw_priority', 'pmw_schedule_cron' ];
    foreach ( $keys as $key ) {
        if ( isset( $_POST[ $key ] ) ) {
            $v = sanitize_text_field( wp_unslash( $_POST[ $key ] ) );
            if ( $key === 'pmw_summary' ) $v = sanitize_textarea_field( wp_unslash( $_POST[ $key ] ) );
            update_post_meta( $post_id, $key, $v );
        }
    }
    if ( isset( $_POST['pmw_is_buy_side'] ) ) {
        update_post_meta( $post_id, 'pmw_is_buy_side', $_POST['pmw_is_buy_side'] === '1' ? '1' : '0' );
    }
    if ( isset( $_POST['pmw_priority'] ) && is_numeric( $_POST['pmw_priority'] ) ) {
        update_post_meta( $post_id, 'pmw_priority', (int) $_POST['pmw_priority'] );
    }
}

function pmw_article_topic_link_meta_box() {
    add_meta_box( 'pmw_article_topic', __( 'Content Topic', 'pmw-core' ), 'pmw_article_topic_link_meta_box_cb', [ 'post', 'pmw_news_analysis' ], 'side' );
}

function pmw_article_topic_link_meta_box_cb( $post ) {
    $topic_id = (int) get_post_meta( $post->ID, 'pmw_topic_id', true );
    wp_nonce_field( 'pmw_article_topic_save', 'pmw_article_topic_nonce' );
    $topics = get_posts( [ 'post_type' => 'pmw_topic', 'post_status' => 'publish', 'numberposts' => -1, 'orderby' => 'title', 'order' => 'ASC' ] );
    echo '<select name="pmw_topic_id" class="widefat">';
    echo '<option value="0">— None —</option>';
    foreach ( $topics as $t ) {
        echo '<option value="' . (int) $t->ID . '" ' . selected( $topic_id, $t->ID, false ) . '>' . esc_html( $t->post_title ) . '</option>';
    }
    echo '</select>';
    echo '<p class="description">Link this article to a Content Topic. Used by the agent workflow.</p>';
}

function pmw_save_article_topic_link( $post_id, $post ) {
    if ( ! $post || ! in_array( $post->post_type ?? '', [ 'post', 'pmw_news_analysis' ], true ) ) return;
    if ( ! isset( $_POST['pmw_article_topic_nonce'] ) || ! wp_verify_nonce( $_POST['pmw_article_topic_nonce'], 'pmw_article_topic_save' ) ) return;
    if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) return;
    if ( ! current_user_can( 'edit_post', $post_id ) ) return;
    $tid = isset( $_POST['pmw_topic_id'] ) ? (int) $_POST['pmw_topic_id'] : 0;
    update_post_meta( $post_id, 'pmw_topic_id', $tid );
}

add_action( 'add_meta_boxes', 'pmw_form_submission_meta_box' );
function pmw_form_submission_meta_box() {
    add_meta_box(
        'pmw_form_submission_details',
        __( 'Contact details', 'pmw-core' ),
        'pmw_form_submission_meta_box_cb',
        'form_submission',
        'normal'
    );
}

function pmw_form_submission_meta_box_cb( $post ) {
    $name    = get_post_meta( $post->ID, '_pmw_contact_name', true );
    $email   = get_post_meta( $post->ID, '_pmw_contact_email', true );
    $subject = get_post_meta( $post->ID, '_pmw_contact_subject', true );
    $message = get_post_meta( $post->ID, '_pmw_contact_message', true );
    $source  = get_post_meta( $post->ID, '_pmw_contact_source', true );
    $at      = get_post_meta( $post->ID, '_pmw_contact_submitted_at', true );
    echo '<p><strong>Name:</strong> ' . esc_html( $name ) . '</p>';
    echo '<p><strong>Email:</strong> ' . esc_html( $email ) . '</p>';
    echo '<p><strong>Subject:</strong> ' . esc_html( $subject ) . '</p>';
    echo '<p><strong>Submitted:</strong> ' . esc_html( $at ) . ' <em>(' . esc_html( $source ) . ')</em></p>';
    echo '<p><strong>Message:</strong></p><p>' . nl2br( esc_html( $message ) ) . '</p>';
}

// ── v2.0: News & Analysis migration admin page ───────────────────────────────────
add_action( 'admin_menu', 'pmw_news_migration_menu' );
add_action( 'admin_menu', 'pmw_seed_tools_menu' );
add_action( 'admin_menu', 'pmw_topics_admin_menu' );
add_action( 'admin_init', 'pmw_news_migration_run' );
add_action( 'admin_init', 'pmw_topics_admin_actions' );
add_action( 'template_redirect', 'pmw_news_redirects' );

function pmw_news_migration_menu() {
    add_submenu_page(
        null,
        'News & Analysis Migration',
        'News Migration',
        'manage_options',
        'pmw-run-news-migration',
        'pmw_news_migration_page'
    );
}

function pmw_news_migration_page() {
    if ( ! current_user_can( 'manage_options' ) ) return;
    $done = get_option( 'pmw_news_migration_done', false );
    global $wpdb;
    $count = 0;
    if ( ! $done ) {
        $count = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type = %s", 'market-insight' ) );
    }
    echo '<div class="wrap"><h1>News & Analysis Migration</h1>';
    if ( $done ) {
        echo '<p><strong>Migration already completed.</strong> No action needed.</p>';
        echo '</div>';
        return;
    }
    echo '<p>This will migrate all <strong>Market Insights</strong> posts to the new <strong>News & Analysis</strong> post type and assign news categories.</p>';
    echo '<p>Posts to migrate: <strong>' . (int) $count . '</strong></p>';
    if ( $count > 0 ) {
        echo '<form method="post" onsubmit="return confirm(\'Run migration now? This cannot be undone.\');">';
        wp_nonce_field( 'pmw_news_migration', 'pmw_news_migration_nonce' );
        echo '<p><input type="submit" name="pmw_run_news_migration" class="button button-primary" value="Run migration" /></p>';
        echo '</form>';
    } else {
        echo '<p>No market-insight posts found. Nothing to migrate.</p>';
    }
    echo '</div>';
}

function pmw_news_migration_run() {
    if ( ! isset( $_POST['pmw_run_news_migration'] ) || ! isset( $_POST['pmw_news_migration_nonce'] ) ) return;
    if ( ! current_user_can( 'manage_options' ) || ! wp_verify_nonce( $_POST['pmw_news_migration_nonce'], 'pmw_news_migration' ) ) return;
    if ( get_option( 'pmw_news_migration_done', false ) ) return;

    global $wpdb;
    $updated = $wpdb->update( $wpdb->posts, [ 'post_type' => 'pmw_news_analysis' ], [ 'post_type' => 'market-insight' ] );
    if ( $updated === false ) {
        if ( function_exists( 'error_log' ) ) {
            error_log( '[PMW News Migration] wpdb->update failed' );
        }
        return;
    }
    $post_ids = $wpdb->get_col( $wpdb->prepare( "SELECT ID FROM {$wpdb->posts} WHERE post_type = %s", 'pmw_news_analysis' ) );
    $slug_map = [ 'market-news' => 'market-news', 'price-analysis' => 'price-analysis', 'investment-guides' => 'investment-guides', 'industry-trends' => 'industry-trends' ];
    $default_term = get_term_by( 'slug', 'market-news', 'pmw_news_category' );
    $default_id = $default_term ? $default_term->term_id : 0;
    foreach ( (array) $post_ids as $post_id ) {
        $terms = wp_get_object_terms( $post_id, 'pmw-topic' );
        $news_term_slug = 'market-news';
        if ( ! empty( $terms ) && ! is_wp_error( $terms ) ) {
            $first = $terms[0];
            $slug = isset( $slug_map[ $first->slug ] ) ? $first->slug : ( isset( $slug_map[ $first->name ] ) ? $slug_map[ $first->name ] : null );
            if ( $slug ) $news_term_slug = $slug;
        }
        $term = get_term_by( 'slug', $news_term_slug, 'pmw_news_category' );
        $tid = $term ? $term->term_id : $default_id;
        if ( $tid ) wp_set_object_terms( $post_id, (int) $tid, 'pmw_news_category' );
    }
    flush_rewrite_rules();
    update_option( 'pmw_news_migration_done', true );
    if ( function_exists( 'error_log' ) ) {
        error_log( '[PMW News Migration] Migrated ' . (int) $updated . ' posts to pmw_news_analysis' );
    }
    wp_safe_redirect( add_query_arg( 'page', 'pmw-run-news-migration', admin_url( 'admin.php' ) ) );
    exit;
}

function pmw_seed_tools_menu() {
    add_submenu_page(
        null,
        'Seed Tools',
        'Seed Tools',
        'manage_options',
        'pmw-seed-tools',
        'pmw_seed_tools_page'
    );
}

function pmw_seed_tools_page() {
    if ( ! current_user_can( 'manage_options' ) ) return;
    $done = get_option( 'pmw_tools_seeded', false );
    echo '<div class="wrap"><h1>Seed Tools</h1>';
    if ( $done ) {
        echo '<p><strong>Tools already seeded.</strong> You can create more from Tools → Add New.</p>';
        echo '</div>';
        return;
    }
    echo '<p>This will create the 7 tool posts from the v2.0 brief (Gold Value Calculator, Investment Return Calculator, etc.). Replace <code>YOUR_BULLIONVAULT_USERNAME</code> in the two BullionVault embed tools before going live.</p>';
    echo '<form method="post">';
    wp_nonce_field( 'pmw_seed_tools', 'pmw_seed_tools_nonce' );
    echo '<p><input type="submit" name="pmw_run_seed_tools" class="button button-primary" value="Seed tools" /></p>';
    echo '</form></div>';
}

add_action( 'admin_init', 'pmw_seed_tools_run' );
function pmw_seed_tools_run() {
    if ( ! isset( $_POST['pmw_run_seed_tools'] ) || ! isset( $_POST['pmw_seed_tools_nonce'] ) ) return;
    if ( ! current_user_can( 'manage_options' ) || ! wp_verify_nonce( $_POST['pmw_seed_tools_nonce'], 'pmw_seed_tools' ) ) return;
    if ( get_option( 'pmw_tools_seeded', false ) ) return;

    $calculator_term = get_term_by( 'slug', 'calculator', 'pmw_tool_type' );
    $comparison_term = get_term_by( 'slug', 'comparison-table', 'pmw_tool_type' );
    $portfolio_term = get_term_by( 'slug', 'portfolio-tracker', 'pmw_tool_type' );
    $chart_term = get_term_by( 'slug', 'price-chart', 'pmw_tool_type' );

    $tools = [
        [ 'title' => 'Gold Value Calculator', 'slug' => 'gold-value-calculator', 'type' => $calculator_term, 'impl' => 'custom-react', 'status' => 'live', 'order' => 1, 'featured' => true, 'cta' => 'Buy gold at today\'s spot price →', 'partner' => 'bullionvault', 'position' => 'after-result' ],
        [ 'title' => 'Investment Return Calculator', 'slug' => 'investment-return-calculator', 'type' => $calculator_term, 'impl' => 'custom-react', 'status' => 'live', 'order' => 2, 'featured' => true, 'cta' => 'Start investing in gold from £25 →', 'partner' => 'bullionvault', 'position' => 'after-result' ],
        [ 'title' => 'Dealer Comparison Table', 'slug' => 'dealer-comparison-table', 'type' => $comparison_term, 'impl' => 'custom-react', 'status' => 'live', 'order' => 3, 'featured' => true, 'cta' => '', 'partner' => 'none', 'position' => 'inline' ],
        [ 'title' => 'Portfolio Tracker', 'slug' => 'portfolio-tracker', 'type' => $portfolio_term, 'impl' => 'custom-react', 'status' => 'live', 'order' => 4, 'featured' => false, 'cta' => 'Compare storage options at BullionVault →', 'partner' => 'bullionvault', 'position' => 'after-result' ],
        [ 'title' => 'Scrap Gold Calculator', 'slug' => 'scrap-gold-calculator', 'type' => $calculator_term, 'impl' => 'custom-react', 'status' => 'live', 'order' => 5, 'featured' => false, 'cta' => 'Get your free valuation →', 'partner' => 'hatton-garden', 'position' => 'after-result' ],
        [ 'title' => 'BullionVault Live Prices', 'slug' => 'bullionvault-live-price', 'type' => $chart_term, 'impl' => 'embed', 'status' => 'live', 'order' => 6, 'featured' => false, 'embed' => '<script src="https://www.bullionvault.com/banners/live_price_widget.js?v=1"></script><div id="bv-price-widget"></div><script>new BullionVaultPriceWidget("bv-price-widget",{currency:"GBP",bullion:"gold",weight:"oz",referrerID:"YOUR_BULLIONVAULT_USERNAME"});</script>', 'partner' => 'bullionvault', 'position' => 'inline' ],
        [ 'title' => 'BullionVault Price Chart', 'slug' => 'bullionvault-price-chart', 'type' => $chart_term, 'impl' => 'embed', 'status' => 'live', 'order' => 7, 'featured' => false, 'embed' => '<script src="https://www.bullionvault.com/chart/bullionvaultchart.js"></script><div id="bv-chart" style="height:400px;width:100%;"></div><script>var options={bullion:"gold",currency:"GBP",timeframe:"1y",chartType:"line",referrerID:"YOUR_BULLIONVAULT_USERNAME",containerDefinedSize:true,switchBullion:true,switchCurrency:true,switchTimeframe:true,exportButton:true};new BullionVaultChart(options,"bv-chart");</script>', 'partner' => 'bullionvault', 'position' => 'inline' ],
    ];

    foreach ( $tools as $t ) {
        if ( get_page_by_path( $t['slug'], OBJECT, 'pmw_tools' ) ) continue;
        $post_id = wp_insert_post( [
            'post_title'   => $t['title'],
            'post_name'    => $t['slug'],
            'post_type'    => 'pmw_tools',
            'post_status'  => 'publish',
            'post_content' => '',
            'post_excerpt' => '',
        ] );
        if ( ! $post_id || is_wp_error( $post_id ) ) continue;
        if ( $t['type'] && isset( $t['type']->term_id ) ) wp_set_object_terms( $post_id, $t['type']->term_id, 'pmw_tool_type' );
        update_post_meta( $post_id, 'pmw_implementation', $t['impl'] );
        update_post_meta( $post_id, 'pmw_tool_status', $t['status'] );
        update_post_meta( $post_id, 'pmw_display_order', $t['order'] );
        update_post_meta( $post_id, 'pmw_is_featured', $t['featured'] ? '1' : '0' );
        update_post_meta( $post_id, 'pmw_affiliate_partner', $t['partner'] );
        update_post_meta( $post_id, 'pmw_affiliate_cta_position', $t['position'] );
        if ( ! empty( $t['cta'] ) ) update_post_meta( $post_id, 'pmw_affiliate_cta_text', $t['cta'] );
        update_post_meta( $post_id, 'pmw_affiliate_cta_url', '[AFFILIATE_URL_TO_BE_ADDED]' );
        if ( $t['impl'] === 'custom-react' ) update_post_meta( $post_id, 'pmw_react_component', $t['slug'] );
        if ( ! empty( $t['embed'] ) ) update_post_meta( $post_id, 'pmw_embed_code', $t['embed'] );
        update_post_meta( $post_id, 'pmw_metal_relevance', wp_json_encode( [ 'gold', 'silver', 'platinum', 'palladium' ] ) );
    }

    update_option( 'pmw_tools_seeded', true );
    wp_safe_redirect( add_query_arg( 'page', 'pmw-seed-tools', admin_url( 'admin.php' ) ) );
    exit;
}

// ── Content Topics: Seed, Reset, Unlink ───────────────────────────────────────────
function pmw_topics_admin_menu() {
    add_submenu_page(
        'edit.php?post_type=pmw_topic',
        'Seed & Reset Topics',
        'Seed & Reset',
        'manage_options',
        'pmw-topics-seed-reset',
        'pmw_topics_seed_reset_page'
    );
}

function pmw_topics_seed_reset_page() {
    if ( ! current_user_can( 'manage_options' ) ) return;
    $done = isset( $_GET['done'] ) ? sanitize_text_field( wp_unslash( $_GET['done'] ) ) : '';
    if ( $done === 'seed' ) echo '<div class="notice notice-success"><p>Topics seeded from JSON.</p></div>';
    if ( $done === 'reset' ) echo '<div class="notice notice-success"><p>All topics reset to seed state.</p></div>';
    if ( $done === 'unlink' ) echo '<div class="notice notice-success"><p>All articles unlinked from topics.</p></div>';
    $seed_path = apply_filters( 'pmw_topics_seed_json_path', plugin_dir_path( __FILE__ ) . 'data/pmw_topics_seed_100.json' );
    $seed_exists = file_exists( $seed_path );
    $topic_count = (int) wp_count_posts( 'pmw_topic' )->publish;
    $linked_count = pmw_count_articles_linked_to_topics();
    echo '<div class="wrap"><h1>Seed & Reset Content Topics</h1>';
    echo '<p>Topics: <strong>' . (int) $topic_count . '</strong> | Articles linked to topics: <strong>' . (int) $linked_count . '</strong></p>';
    echo '<div style="display:flex;gap:1em;flex-wrap:wrap;margin:1em 0;">';
    echo '<form method="post" style="display:inline;" onsubmit="return confirm(\'Seed topics from JSON? Existing topics are preserved; new ones are added.\');">';
    wp_nonce_field( 'pmw_topics_seed', 'pmw_topics_seed_nonce' );
    echo '<input type="hidden" name="pmw_topics_action" value="seed" />';
    echo '<input type="submit" class="button button-primary" value="Seed topics from JSON" ' . ( $seed_exists ? '' : 'disabled' ) . ' />';
    echo '</form>';
    echo '<form method="post" style="display:inline;" onsubmit="return confirm(\'Reset ALL topics to seed state? This deletes all existing topics and recreates from JSON.\');">';
    wp_nonce_field( 'pmw_topics_seed', 'pmw_topics_seed_nonce' );
    echo '<input type="hidden" name="pmw_topics_action" value="reset" />';
    echo '<input type="submit" class="button" value="Reset all topics to seed state" ' . ( $seed_exists ? '' : 'disabled' ) . ' />';
    echo '</form>';
    echo '<form method="post" style="display:inline;" onsubmit="return confirm(\'Unlink all articles from topics? This clears pmw_topic_id from posts and News & Analysis. Articles are NOT deleted.\');">';
    wp_nonce_field( 'pmw_topics_seed', 'pmw_topics_seed_nonce' );
    echo '<input type="hidden" name="pmw_topics_action" value="unlink" />';
    echo '<input type="submit" class="button" value="Unlink all articles from topics" />';
    echo '</form>';
    echo '</div>';
    if ( ! $seed_exists ) {
        echo '<p class="notice notice-warning"><strong>Seed file not found:</strong> <code>' . esc_html( $seed_path ) . '</code></p>';
    }
    echo '</div>';
}

function pmw_count_articles_linked_to_topics() {
    global $wpdb;
    $posts = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID = m.post_id WHERE m.meta_key = 'pmw_topic_id' AND m.meta_value != '0' AND m.meta_value != '' AND p.post_type = 'post'" );
    $news = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID = m.post_id WHERE m.meta_key = 'pmw_topic_id' AND m.meta_value != '0' AND m.meta_value != '' AND p.post_type = 'pmw_news_analysis'" );
    return $posts + $news;
}

function pmw_topics_admin_actions() {
    if ( ! isset( $_POST['pmw_topics_action'] ) || ! isset( $_POST['pmw_topics_seed_nonce'] ) ) return;
    if ( ! current_user_can( 'manage_options' ) || ! wp_verify_nonce( $_POST['pmw_topics_seed_nonce'], 'pmw_topics_seed' ) ) return;
    $action = sanitize_text_field( wp_unslash( $_POST['pmw_topics_action'] ) );
    $seed_path = apply_filters( 'pmw_topics_seed_json_path', plugin_dir_path( __FILE__ ) . 'data/pmw_topics_seed_100.json' );
    if ( $action === 'reset' || $action === 'seed' ) {
        if ( ! file_exists( $seed_path ) ) {
            wp_die( esc_html__( 'Seed file not found.', 'pmw-core' ) );
        }
        $json = file_get_contents( $seed_path );
        $items = json_decode( $json, true );
        if ( ! is_array( $items ) ) {
            wp_die( esc_html__( 'Invalid seed JSON.', 'pmw-core' ) );
        }
        if ( $action === 'reset' ) {
            $ids = get_posts( [ 'post_type' => 'pmw_topic', 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids' ] );
            foreach ( $ids as $id ) {
                wp_delete_post( $id, true );
            }
        }
        pmw_seed_topics_from_json( $items );
    } elseif ( $action === 'unlink' ) {
        pmw_unlink_all_articles_from_topics();
    }
    wp_safe_redirect( add_query_arg( [ 'post_type' => 'pmw_topic', 'page' => 'pmw-topics-seed-reset', 'done' => $action ], admin_url( 'edit.php' ) ) );
    exit;
}

function pmw_seed_topics_from_json( array $items ) {
    foreach ( $items as $item ) {
        $title = isset( $item['title'] ) ? sanitize_text_field( $item['title'] ) : '';
        if ( empty( $title ) ) continue;
        $meta = isset( $item['meta'] ) && is_array( $item['meta'] ) ? $item['meta'] : [];
        $status = isset( $item['status'] ) ? sanitize_text_field( $item['status'] ) : 'publish';
        $existing = get_page_by_title( $title, OBJECT, 'pmw_topic' );
        if ( $existing ) continue;
        $post_id = wp_insert_post( [
            'post_title'   => $title,
            'post_type'    => 'pmw_topic',
            'post_status'  => $status,
            'post_content' => '',
        ] );
        if ( ! $post_id || is_wp_error( $post_id ) ) continue;
        foreach ( $meta as $key => $val ) {
            if ( strpos( $key, 'pmw_' ) !== 0 ) continue;
            if ( is_bool( $val ) ) {
                update_post_meta( $post_id, $key, $val ? '1' : '0' );
            } elseif ( is_int( $val ) ) {
                update_post_meta( $post_id, $key, $val );
            } else {
                update_post_meta( $post_id, $key, (string) $val );
            }
        }
    }
}

function pmw_unlink_all_articles_from_topics() {
    global $wpdb;
    $wpdb->query( "DELETE m FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID = m.post_id WHERE m.meta_key = 'pmw_topic_id' AND p.post_type IN ('post','pmw_news_analysis')" );
}

add_filter( 'manage_pmw_topic_posts_columns', 'pmw_topic_columns' );
add_action( 'manage_pmw_topic_posts_custom_column', 'pmw_topic_column_cb', 10, 2 );
add_filter( 'manage_post_posts_columns', 'pmw_article_topic_column' );
add_action( 'manage_post_posts_custom_column', 'pmw_article_topic_column_cb', 10, 2 );
add_filter( 'manage_pmw_news_analysis_posts_columns', 'pmw_article_topic_column' );
add_action( 'manage_pmw_news_analysis_posts_custom_column', 'pmw_article_topic_column_cb', 10, 2 );

function pmw_topic_columns( $columns ) {
    $new = [];
    foreach ( $columns as $k => $v ) {
        $new[ $k ] = $v;
        if ( $k === 'title' ) {
            $new['pmw_target_keyword'] = 'Target Keyword';
            $new['pmw_agent_status'] = 'Status';
        }
    }
    return $new;
}

function pmw_topic_column_cb( $column, $post_id ) {
    if ( $column === 'pmw_target_keyword' ) {
        echo esc_html( get_post_meta( $post_id, 'pmw_target_keyword', true ) ?: '—' );
    }
    if ( $column === 'pmw_agent_status' ) {
        echo esc_html( get_post_meta( $post_id, 'pmw_agent_status', true ) ?: 'idle' );
    }
}

function pmw_article_topic_column( $columns ) {
    $new = [];
    foreach ( $columns as $k => $v ) {
        $new[ $k ] = $v;
        if ( $k === 'title' ) $new['pmw_topic'] = 'Content Topic';
    }
    return $new;
}

function pmw_article_topic_column_cb( $column, $post_id ) {
    if ( $column === 'pmw_topic' ) {
        $tid = (int) get_post_meta( $post_id, 'pmw_topic_id', true );
        if ( $tid ) {
            $t = get_post( $tid );
            echo $t ? '<a href="' . esc_url( get_edit_post_link( $tid ) ) . '">' . esc_html( $t->post_title ) . '</a>' : '—';
        } else {
            echo '—';
        }
    }
}

add_action( 'load-edit.php', 'pmw_topics_list_buttons' );
function pmw_topics_list_buttons() {
    global $pagenow, $typenow;
    if ( $pagenow !== 'edit.php' || $typenow !== 'pmw_topic' ) return;
    add_action( 'all_admin_notices', function() {
        $url = add_query_arg( 'page', 'pmw-topics-seed-reset', admin_url( 'edit.php?post_type=pmw_topic' ) );
        echo '<div class="notice notice-info" style="margin:15px 0;"><p><a href="' . esc_url( $url ) . '" class="button">Seed & Reset Topics</a> — Seed from JSON, reset to seed state, or unlink all articles from topics.</p></div>';
    } );
}

function pmw_news_redirects() {
    if ( empty( $_SERVER['REQUEST_URI'] ) ) return;
    $uri = sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) );
    if ( preg_match( '#^/market-insights/?$#', $uri ) ) {
        wp_redirect( home_url( '/news-analysis/' ), 301 );
        exit;
    }
    if ( preg_match( '#^/market-insights/([^/?]+)/?$#', $uri, $m ) ) {
        wp_redirect( home_url( '/news-analysis/' . $m[1] . '/' ), 301 );
        exit;
    }
}

add_action( 'init', 'pmw_register_taxonomies' );

function pmw_register_taxonomies() {

    // ── Topic (for posts + market insights) ─
    register_taxonomy( 'pmw-topic', [ 'post', 'market-insight' ], [
        'labels' => [
            'name'          => 'Topics',
            'singular_name' => 'Topic',
            'search_items'  => 'Search Topics',
            'all_items'     => 'All Topics',
            'edit_item'     => 'Edit Topic',
            'add_new_item'  => 'Add New Topic',
        ],
        'hierarchical'    => true,
        'public'          => true,
        'rewrite'         => [ 'slug' => 'topic' ],
        'show_in_rest'    => true,
        'show_in_graphql' => true,
        'graphql_single_name' => 'topic',
        'graphql_plural_name' => 'topics',
    ] );

    // ── Metal Type (for all content types) ─
    register_taxonomy( 'pmw-metal-type', [ 'post', 'market-insight', 'dealer', 'affiliate-product' ], [
        'labels' => [
            'name'          => 'Metal Types',
            'singular_name' => 'Metal Type',
            'add_new_item'  => 'Add New Metal Type',
        ],
        'hierarchical'    => false,
        'public'          => true,
        'rewrite'         => [ 'slug' => 'metal' ],
        'show_in_rest'    => true,
        'show_in_graphql' => true,
        'graphql_single_name' => 'metalType',
        'graphql_plural_name' => 'metalTypes',
    ] );

    // ── Gemstone Type (for all content types) ─
    register_taxonomy( 'pmw-gemstone-type', [ 'post', 'market-insight', 'dealer', 'affiliate-product' ], [
        'labels' => [
            'name'          => 'Gemstone Types',
            'singular_name' => 'Gemstone Type',
            'add_new_item'  => 'Add New Gemstone Type',
        ],
        'hierarchical'    => false,
        'public'          => true,
        'rewrite'         => [ 'slug' => 'gemstone' ],
        'show_in_rest'    => true,
        'show_in_graphql' => true,
        'graphql_single_name' => 'gemstoneType',
        'graphql_plural_name' => 'gemstoneTypes',
    ] );

    // ── Dealer Category ──────────────────────
    register_taxonomy( 'pmw-dealer-category', [ 'dealer' ], [
        'labels' => [
            'name'          => 'Dealer Categories',
            'singular_name' => 'Dealer Category',
            'add_new_item'  => 'Add New Dealer Category',
        ],
        'hierarchical'    => true,
        'public'          => true,
        'rewrite'         => [ 'slug' => 'dealer-category' ],
        'show_in_rest'    => true,
        'show_in_graphql' => true,
        'graphql_single_name' => 'dealerCategory',
        'graphql_plural_name' => 'dealerCategories',
    ] );

    // ── News & Analysis category (v2.0) ───────────────────────────────────────────
    register_taxonomy( 'pmw_news_category', 'pmw_news_analysis', [
        'labels'            => [
            'name' => 'News Categories',
            'singular_name' => 'News Category',
        ],
        'hierarchical'      => true,
        'public'            => true,
        'show_in_rest'      => true,
        'show_in_graphql'   => true,
        'graphql_single_name' => 'newsCategory',
        'graphql_plural_name' => 'newsCategories',
        'rewrite'           => [ 'slug' => 'news-analysis/category', 'with_front' => false ],
        'show_admin_column' => true,
    ] );

    // ── Tool type (v2.0) ─────────────────────────────────────────────────────────
    register_taxonomy( 'pmw_tool_type', 'pmw_tools', [
        'labels'            => [
            'name' => 'Tool Types',
            'singular_name' => 'Tool Type',
        ],
        'hierarchical'      => true,
        'public'            => true,
        'show_in_rest'      => true,
        'show_in_graphql'   => true,
        'graphql_single_name' => 'toolType',
        'graphql_plural_name' => 'toolTypes',
        'rewrite'           => [ 'slug' => 'tool-type' ],
        'show_admin_column' => true,
    ] );
}


// ─────────────────────────────────────────────
// 3. SEED DEFAULT TERMS (runs once on activation)
// ─────────────────────────────────────────────

register_activation_hook( __FILE__, 'pmw_on_activation' );

function pmw_on_activation() {
    pmw_seed_terms();
    pmw_seed_agents();
    pmw_seed_news_categories();
    pmw_seed_tool_types();
}

function pmw_seed_news_categories() {
    $terms = [
        [ 'name' => 'Market News', 'slug' => 'market-news', 'description' => 'Breaking news and developments in precious metals markets' ],
        [ 'name' => 'Price Analysis', 'slug' => 'price-analysis', 'description' => 'In-depth analysis of gold, silver, platinum and palladium prices' ],
        [ 'name' => 'Investment Guides', 'slug' => 'investment-guides', 'description' => 'Guides and educational content for precious metals investors' ],
        [ 'name' => 'Industry Trends', 'slug' => 'industry-trends', 'description' => 'Longer-form trends shaping the precious metals industry' ],
    ];
    foreach ( $terms as $t ) {
        if ( ! term_exists( $t['slug'], 'pmw_news_category' ) ) {
            wp_insert_term( $t['name'], 'pmw_news_category', [ 'slug' => $t['slug'], 'description' => $t['description'] ] );
        }
    }
}

function pmw_seed_tool_types() {
    $terms = [
        [ 'name' => 'Calculator', 'slug' => 'calculator' ],
        [ 'name' => 'Comparison Table', 'slug' => 'comparison-table' ],
        [ 'name' => 'Portfolio Tracker', 'slug' => 'portfolio-tracker' ],
        [ 'name' => 'Price Chart', 'slug' => 'price-chart' ],
    ];
    foreach ( $terms as $t ) {
        if ( ! term_exists( $t['slug'], 'pmw_tool_type' ) ) {
            wp_insert_term( $t['name'], 'pmw_tool_type', [ 'slug' => $t['slug'] ] );
        }
    }
}

function pmw_seed_terms() {

    $topics = [
        'Precious Metals',
        'Gemstones',
        'Jewelry Investment',
        'Market Insights',
        'Buying Guides',
        'Investment Strategy',
        'Industry News',
    ];
    foreach ( $topics as $term ) {
        if ( ! term_exists( $term, 'pmw-topic' ) ) {
            wp_insert_term( $term, 'pmw-topic' );
        }
    }

    $metals = [ 'Gold', 'Silver', 'Platinum', 'Palladium' ];
    foreach ( $metals as $term ) {
        if ( ! term_exists( $term, 'pmw-metal-type' ) ) {
            wp_insert_term( $term, 'pmw-metal-type' );
        }
    }

    $gemstones = [ 'Diamond', 'Ruby', 'Sapphire', 'Emerald' ];
    foreach ( $gemstones as $term ) {
        if ( ! term_exists( $term, 'pmw-gemstone-type' ) ) {
            wp_insert_term( $term, 'pmw-gemstone-type' );
        }
    }

    $dealer_cats = [ 'Bullion Dealer', 'Jeweler', 'Online Marketplace', 'Auction House' ];
    foreach ( $dealer_cats as $term ) {
        if ( ! term_exists( $term, 'pmw-dealer-category' ) ) {
            wp_insert_term( $term, 'pmw-dealer-category' );
        }
    }
}

function pmw_seed_agents() {
    if ( ! post_type_exists( 'pmw_agent' ) ) {
        return;
    }
    $agents = [
        [ 'title' => 'The Director', 'role' => 'Executive Orchestrator', 'tier' => 1, 'agent_role' => 'The Director', 'bio' => 'Orchestrates the entire pipeline. Receives briefs, assigns tasks, makes final publish decisions.', 'specialisms' => 'Strategy, Coordination', 'menu_order' => 1 ],
        [ 'title' => 'The Trend Analyst', 'role' => 'Trend Analyst', 'tier' => 2, 'agent_role' => 'The Trend Analyst', 'bio' => 'Monitors Google Trends, Reddit, X/Twitter for emerging topics. Weekly trending reports.', 'specialisms' => 'Search trends, Social velocity', 'menu_order' => 10 ],
        [ 'title' => 'The Content Gap Analyst', 'role' => 'Content Gap Analyst', 'tier' => 2, 'agent_role' => 'The Content Gap Analyst', 'bio' => 'Audits content against competitors and search demand. Identifies missing topics.', 'specialisms' => 'SEO gaps, Competitor analysis', 'menu_order' => 11 ],
        [ 'title' => 'The Performance Intelligence Agent', 'role' => 'Performance Intelligence', 'tier' => 2, 'agent_role' => 'The Performance Intelligence Agent', 'bio' => 'Analyses GA4 and Clarity. Flags underperforming pages, UX issues.', 'specialisms' => 'Analytics, Conversion', 'menu_order' => 12 ],
        [ 'title' => 'The Financial Intelligence Agent', 'role' => 'Financial Intelligence', 'tier' => 2, 'agent_role' => 'The Financial Intelligence Agent', 'bio' => 'Monitors markets, central banks, commodity exchanges. Real-time alerts for price movements.', 'specialisms' => 'Markets, Macro events', 'menu_order' => 13 ],
        [ 'title' => 'The Affiliate Intelligence Agent', 'role' => 'Affiliate Intelligence', 'tier' => 2, 'agent_role' => 'The Affiliate Intelligence Agent', 'bio' => 'Monitors affiliate performance. Tracks conversion, recommends placements.', 'specialisms' => 'Affiliate, Revenue', 'menu_order' => 14 ],
        [ 'title' => 'The Editor-in-Chief', 'role' => 'Editor-in-Chief', 'tier' => 3, 'agent_role' => 'The Editor-in-Chief', 'bio' => 'Reviews all drafted content. Enforces house style, tone, factual consistency.', 'specialisms' => 'Editorial standards, Style guide', 'menu_order' => 20 ],
        [ 'title' => 'The Research Director', 'role' => 'Research Director', 'tier' => 3, 'agent_role' => 'The Research Director', 'bio' => 'Validates research output before it reaches writers. Source quality gatekeeper.', 'specialisms' => 'Source validation, Accuracy', 'menu_order' => 21 ],
        [ 'title' => 'The SEO Strategist', 'role' => 'SEO Strategist', 'tier' => 3, 'agent_role' => 'The SEO Strategist', 'bio' => 'Defines keyword strategy. Reviews content for SEO compliance. Internal linking.', 'specialisms' => 'Keywords, Search performance', 'menu_order' => 22 ],
        [ 'title' => 'The Metals Analyst', 'role' => 'Metals Analyst', 'tier' => 4, 'agent_role' => 'The Metals Analyst', 'bio' => 'Specialist research: gold, silver, platinum, palladium. Price data, macro trends.', 'specialisms' => 'Gold, Silver, Platinum, Palladium', 'menu_order' => 30 ],
        [ 'title' => 'The Gemstone Analyst', 'role' => 'Gemstone Analyst', 'tier' => 4, 'agent_role' => 'The Gemstone Analyst', 'bio' => 'Specialist research: diamonds, rubies, sapphires, emeralds. Auction results.', 'specialisms' => 'Diamonds, Colored stones', 'menu_order' => 31 ],
        [ 'title' => 'The Market Writer', 'role' => 'Market Writer', 'tier' => 4, 'agent_role' => 'The Market Writer', 'bio' => 'Writes market insight articles and price analysis. Translates research into editorial.', 'specialisms' => 'Market insights, Analysis', 'menu_order' => 32 ],
        [ 'title' => 'The Feature Writer', 'role' => 'Feature Writer', 'tier' => 4, 'agent_role' => 'The Feature Writer', 'bio' => 'Writes long-form educational content: buying guides, investment strategy.', 'specialisms' => 'Guides, Evergreen content', 'menu_order' => 33 ],
        [ 'title' => 'The Fact Checker', 'role' => 'Fact Checker', 'tier' => 4, 'agent_role' => 'The Fact Checker', 'bio' => 'Cross-references all claims against verified sources before editorial review.', 'specialisms' => 'Verification, Sources', 'menu_order' => 34 ],
        [ 'title' => 'The Publisher', 'role' => 'Publisher', 'tier' => 4, 'agent_role' => 'The Publisher', 'bio' => 'Handles the mechanical publish process: formatting, taxonomies, SEO fields.', 'specialisms' => 'WordPress, Publishing', 'menu_order' => 35 ],
        [ 'title' => 'The Newsletter Curator', 'role' => 'Newsletter Curator', 'tier' => 5, 'agent_role' => 'The Newsletter Curator', 'bio' => 'Assembles newsletter digests. Selects relevant pieces, writes summary copy.', 'specialisms' => 'Newsletter, Mailchimp', 'menu_order' => 40 ],
        [ 'title' => 'The Social Scribe', 'role' => 'Social Scribe', 'tier' => 5, 'agent_role' => 'The Social Scribe', 'bio' => 'Generates platform-appropriate social content: LinkedIn, X threads.', 'specialisms' => 'Social media, Distribution', 'menu_order' => 41 ],
        [ 'title' => 'The Quality Monitor', 'role' => 'Quality Monitor', 'tier' => 5, 'agent_role' => 'The Quality Monitor', 'bio' => 'Ongoing audit agent. Flags outdated content, broken links, declining visibility.', 'specialisms' => 'Content audit, Re-optimisation', 'menu_order' => 42 ],
    ];
    foreach ( $agents as $a ) {
        $existing = get_posts( [
            'post_type'      => 'pmw_agent',
            'title'          => $a['title'],
            'post_status'    => 'any',
            'posts_per_page' => 1,
        ] );
        if ( ! empty( $existing ) ) {
            continue;
        }
        $id = wp_insert_post( [
            'post_type'    => 'pmw_agent',
            'post_title'   => $a['title'],
            'post_status'  => 'publish',
            'menu_order'   => $a['menu_order'],
        ], true );
        if ( $id && ! is_wp_error( $id ) && function_exists( 'update_field' ) ) {
            update_field( 'role', $a['role'], $id );
            update_field( 'tier', $a['tier'], $id );
            update_field( 'agent_role', $a['agent_role'], $id );
            update_field( 'bio', $a['bio'], $id );
            update_field( 'specialisms', $a['specialisms'], $id );
            update_field( 'status', 'active', $id );
        }
    }
}

function pmw_maybe_seed_agents() {
    if ( get_option( 'pmw_agents_seeded' ) ) {
        return;
    }
    if ( ! post_type_exists( 'pmw_agent' ) ) {
        return;
    }
    $count = wp_count_posts( 'pmw_agent' );
    if ( $count && (int) $count->publish > 0 ) {
        update_option( 'pmw_agents_seeded', 1 );
        return;
    }
    pmw_seed_agents();
    update_option( 'pmw_agents_seeded', 1 );
}

// ── Seed 7 Agent Profiles from Appendix A (Team page) ──
add_action( 'admin_menu', 'pmw_agent_profiles_seed_menu' );
add_action( 'admin_init', 'pmw_agent_profiles_seed_action' );

function pmw_agent_profiles_seed_menu() {
    add_management_page( 'Seed Agent Profiles', 'Seed Agent Profiles', 'manage_options', 'pmw-seed-agent-profiles', 'pmw_agent_profiles_seed_page' );
}

function pmw_agent_profiles_seed_page() {
    if ( ! current_user_can( 'manage_options' ) ) return;
    $done = isset( $_GET['pmw_seed_agent_profiles'] ) && $_GET['pmw_seed_agent_profiles'] === '1';
    echo '<div class="wrap"><h1>Seed Agent Profiles</h1>';
    if ( $done ) {
        echo '<p class="notice notice-success">Agent profiles seeded. <a href="' . esc_url( admin_url( 'edit.php?post_type=pmw_agent' ) ) . '">View agents</a>.</p>';
    } else {
        echo '<p>Creates the 7 agent profiles from the Developer Brief (Appendix A).</p>';
        echo '<p><a href="' . esc_url( admin_url( 'tools.php?page=pmw-seed-agent-profiles&pmw_seed_agent_profiles=1&_wpnonce=' . wp_create_nonce( 'pmw_seed_agent_profiles' ) ) ) . '" class="button button-primary">Run Seed</a></p>';
    }
    echo '</div>';
}

function pmw_agent_profiles_seed_action() {
    if ( ! isset( $_GET['pmw_seed_agent_profiles'] ) || $_GET['pmw_seed_agent_profiles'] !== '1' ) return;
    if ( ! current_user_can( 'manage_options' ) ) return;
    if ( ! isset( $_GET['_wpnonce'] ) || ! wp_verify_nonce( $_GET['_wpnonce'], 'pmw_seed_agent_profiles' ) ) return;

    pmw_seed_agent_profiles();
    wp_safe_redirect( admin_url( 'tools.php?page=pmw-seed-agent-profiles&pmw_seed_agent_profiles=1' ) );
    exit;
}

function pmw_seed_agent_profiles() {
    if ( ! post_type_exists( 'pmw_agent' ) ) return;

    $agents = pmw_get_agent_profiles_seed_data();
    foreach ( $agents as $a ) {
        $existing = get_posts( [ 'post_type' => 'pmw_agent', 'post_status' => 'any', 'posts_per_page' => 1, 'meta_key' => 'pmw_slug', 'meta_value' => $a['pmw_slug'] ] );
        if ( ! empty( $existing ) ) continue;

        $id = wp_insert_post( [
            'post_type'   => 'pmw_agent',
            'post_title'  => $a['post_title'],
            'post_status' => 'publish',
        ], true );
        if ( ! $id || is_wp_error( $id ) ) continue;

        foreach ( $a as $key => $val ) {
            if ( $key === 'post_title' ) continue;
            update_post_meta( $id, $key, $val );
        }
    }
}

function pmw_get_agent_profiles_seed_data() {
    return [
        [
            'post_title' => 'Marcus Webb',
            'pmw_slug' => 'research-analyst',
            'pmw_display_name' => 'Marcus Webb',
            'pmw_title' => 'The Research Analyst',
            'pmw_role' => 'Market Research & Data Specialist',
            'pmw_tier' => 'intelligence',
            'pmw_model_family' => 'Claude (Anthropic)',
            'pmw_status' => 'active',
            'pmw_eta' => '',
            'pmw_display_order' => 1,
            'pmw_bio' => "Marcus is first in every morning and last to leave — metaphorically speaking. Before a single word of an article is written, he has already scanned live price feeds, aggregated the latest market news, and identified the specific questions PMW readers are asking right now. He never passes a brief to the team without a minimum of five authoritative sources, a clear picture of what readers actually need, and a view on which affiliate partners are most relevant to the story.",
            'pmw_personality' => "Marcus has the energy of a financial journalist on deadline — precise, relentless, slightly obsessive about source quality. He distrusts anything that can't be verified and has a known habit of flagging when a news story is 'thinner than it looks.' Colleagues joke that he treats a weak source like a personal affront.",
            'pmw_quirks' => wp_json_encode( [ "Refuses to pass a brief with fewer than five sources — five is the floor, not the target", "Has a particular distrust of press releases masquerading as news", "Always notes the timestamp on price data — 'stale data is worse than no data'", "Thinks in tabs — reportedly has 47 open at any given moment" ] ),
            'pmw_specialisms' => wp_json_encode( [ 'Gold', 'Silver', 'Platinum', 'Palladium', 'Live Price Data', 'News Aggregation', 'Market Trends', 'Source Verification' ] ),
            'pmw_avatar_image_url' => '',
            'pmw_avatar_video_url' => '',
        ],
        [
            'post_title' => 'Sophia Brennan',
            'pmw_slug' => 'content-strategist',
            'pmw_display_name' => 'Sophia Brennan',
            'pmw_title' => 'The Content Strategist',
            'pmw_role' => 'Senior Content Architect',
            'pmw_tier' => 'editorial',
            'pmw_model_family' => 'Claude (Anthropic)',
            'pmw_status' => 'active',
            'pmw_eta' => '',
            'pmw_display_order' => 2,
            'pmw_bio' => "Sophia takes the raw research Marcus produces and turns it into something a reader can actually use. She is the architect behind every article's structure — deciding how the story flows, where the reader's questions get answered, and at what point a recommended product becomes the natural next step rather than an interruption. She thinks in reader journeys, not word counts.",
            'pmw_personality' => "Sophia has the strategic patience of a chess player and the commercial instincts of someone who has read too many conversion rate studies. She is warm but exacting — she will rebuild a content plan from scratch if the narrative arc isn't right, and she has a low tolerance for articles that bury the lead. Her feedback is always specific and never personal.",
            'pmw_quirks' => wp_json_encode( [ "Draws content plans as flowcharts before writing a single heading", "Categorises every reader as one of three types before planning begins: price checker, researcher, or ready-to-buy", "Has a documented hatred of the phrase 'in today's fast-paced world'", "Believes the best affiliate placement is one the reader thanks you for" ] ),
            'pmw_specialisms' => wp_json_encode( [ 'Content Architecture', 'SEO Strategy', 'Affiliate Integration', 'Reader Journey Mapping', 'Conversion Optimisation', 'Editorial Planning' ] ),
            'pmw_avatar_image_url' => '',
            'pmw_avatar_video_url' => '',
        ],
        [
            'post_title' => 'Elliot Nash',
            'pmw_slug' => 'content-writer',
            'pmw_display_name' => 'Elliot Nash',
            'pmw_title' => 'The Content Writer',
            'pmw_role' => 'Specialist Financial Copywriter',
            'pmw_tier' => 'production',
            'pmw_model_family' => 'Claude (Anthropic)',
            'pmw_status' => 'active',
            'pmw_eta' => '',
            'pmw_display_order' => 3,
            'pmw_bio' => "Elliot writes every article you read on PMW. He takes Sophia's plan and Marcus's research and turns them into something a real person actually wants to read — clear, factual, and honest about what it's recommending and why. He has a particular talent for making complex investment topics accessible without dumbing them down, and a zero-tolerance policy for vague claims that can't be backed with a source. Every article goes to a human reviewer before it goes live.",
            'pmw_personality' => "Elliot has the disposition of a good science journalist — curious, clear-headed, and slightly allergic to hype. He writes the way a knowledgeable friend would explain something: directly, without jargon, without padding. He takes the craft seriously and occasionally pushes back on a brief he thinks is asking him to oversell.",
            'pmw_quirks' => wp_json_encode( [ "Will not write a claim without a source to attach to it", "Rewrites his opening sentence last — 'the intro only works once you know the ending'", "Has an irrational dislike of the em dash being used for decoration rather than function", "Reads every article aloud internally before finalising — 'if it doesn't sound like a person, it isn't ready'" ] ),
            'pmw_specialisms' => wp_json_encode( [ 'Article Writing', 'Precious Metals', 'Gemstones', 'Investment Copy', 'Factual Accuracy', 'Plain English', 'Affiliate Copywriting' ] ),
            'pmw_avatar_image_url' => '',
            'pmw_avatar_video_url' => '',
        ],
        [
            'post_title' => 'Dr. Imogen Hale',
            'pmw_slug' => 'quality-judge',
            'pmw_display_name' => 'Dr. Imogen Hale',
            'pmw_title' => 'The Quality Judge',
            'pmw_role' => 'Editorial Standards Director',
            'pmw_tier' => 'editorial',
            'pmw_model_family' => 'Claude (Anthropic)',
            'pmw_status' => 'active',
            'pmw_eta' => '',
            'pmw_display_order' => 4,
            'pmw_bio' => "Nothing published on PMW has passed through fewer than two of Imogen's reviews. She evaluates every piece of work independently — research, plans, and finished articles — against structured criteria and returns precise, actionable feedback when something doesn't meet the standard. She is not unkind, but she is not lenient. If it goes through Imogen and comes out the other side, it's ready.",
            'pmw_personality' => "Imogen has the measured authority of a senior academic reviewer and the commercial sharpness of someone who has seen too many well-written articles fail to convert. She holds the team to standards they didn't know they had until she pointed them out. Her feedback is always in writing, always specific, and never about the person — only ever about the work.",
            'pmw_quirks' => wp_json_encode( [ "Annotates everything — returns feedback as a structured breakdown, never a vague 'needs work'", "Tracks pass rates obsessively and notices immediately when first-attempt quality dips", "Has a particular issue with unsubstantiated superlatives — 'leading', 'best', 'most trusted' without evidence", "Keeps a private list of the questions readers would ask that the article fails to answer" ] ),
            'pmw_specialisms' => wp_json_encode( [ 'Quality Assurance', 'Conversion Analysis', 'Factual Verification', 'Editorial Standards', 'Scoring & Evaluation', 'Feedback Frameworks' ] ),
            'pmw_avatar_image_url' => '',
            'pmw_avatar_video_url' => '',
        ],
        [
            'post_title' => 'Zara Okonkwo',
            'pmw_slug' => 'visual-designer',
            'pmw_display_name' => 'Zara Okonkwo',
            'pmw_title' => 'The Visual Designer',
            'pmw_role' => 'Digital Asset Creator',
            'pmw_tier' => 'production',
            'pmw_model_family' => 'DALL-E (OpenAI)',
            'pmw_status' => 'active',
            'pmw_eta' => '',
            'pmw_display_order' => 5,
            'pmw_bio' => "Zara is responsible for every image and infographic you see on PMW. She translates each article's core message into a visual that works as a standalone asset — something worth sharing, worth clicking, and worth remembering. She has a particular eye for making financial content feel premium rather than corporate, and she understands that a well-made infographic does more for trust than three paragraphs of text.",
            'pmw_personality' => "Zara has the aesthetic confidence of someone who knows exactly why something works visually and can articulate it precisely. She is quietly opinionated about colour — has strong views on when gold tones become tacky — and believes most financial content is let down by visual mediocrity rather than bad writing. She treats every asset as a potential first impression.",
            'pmw_quirks' => wp_json_encode( [ "Strong opinions on the difference between 'gold' and 'yellow' — they are not the same", "Will not put text in an image if the layout works without it", "Judges a financial site's credibility by its typography before reading a word", "Has a habit of noticing when competitors use the same stock photo and flagging it" ] ),
            'pmw_specialisms' => wp_json_encode( [ 'Featured Images', 'Infographics', 'Data Visualisation', 'Brand Consistency', 'Financial Photography Aesthetics', 'SVG Design' ] ),
            'pmw_avatar_image_url' => '',
            'pmw_avatar_video_url' => '',
        ],
        [
            'post_title' => 'Rio Castellano',
            'pmw_slug' => 'social-author',
            'pmw_display_name' => 'Rio Castellano',
            'pmw_title' => 'The Social Author',
            'pmw_role' => 'Social Media Content Specialist',
            'pmw_tier' => 'production',
            'pmw_model_family' => 'Claude (Anthropic)',
            'pmw_status' => 'in-development',
            'pmw_eta' => 'Phase 3',
            'pmw_display_order' => 6,
            'pmw_bio' => "Rio takes every article PMW publishes and gives it a second life across Twitter, LinkedIn, Facebook, and Instagram. He has a sharp instinct for what stops a scroll and what gets ignored, and he understands that the same insight needs to land completely differently depending on the platform and the audience's mood. He keeps one eye on the article and one on what the precious metals community is talking about right now.",
            'pmw_personality' => "Rio has the cultural awareness of someone who lives online without being chronically online — he understands tone, timing, and the difference between what gets shared and what gets ignored. He is energetic and opinionated about hooks, believes the first three words are the whole game on Twitter, and has a healthy competitive streak when it comes to engagement metrics.",
            'pmw_quirks' => wp_json_encode( [ "Believes the first three words of a tweet determine whether anyone reads the rest", "Keeps a running mental tab of what the r/Gold and r/silverbugs communities are discussing", "Has a documented preference for the fear hook over the greed hook — 'urgency converts better than excitement'", "Rewrites LinkedIn posts at least twice — 'the first version always sounds like a press release'" ] ),
            'pmw_specialisms' => wp_json_encode( [ 'Twitter / X', 'LinkedIn', 'Facebook', 'Instagram', 'Hook Writing', 'Engagement Strategy', 'Trending Topics', 'Community Listening' ] ),
            'pmw_avatar_image_url' => '',
            'pmw_avatar_video_url' => '',
        ],
        [
            'post_title' => 'Nadia Osei',
            'pmw_slug' => 'performance-analyst',
            'pmw_display_name' => 'Nadia Osei',
            'pmw_title' => 'The Performance Analyst',
            'pmw_role' => 'Analytics & Optimisation Specialist',
            'pmw_tier' => 'intelligence',
            'pmw_model_family' => 'Claude (Anthropic)',
            'pmw_status' => 'in-development',
            'pmw_eta' => 'Phase 2',
            'pmw_display_order' => 7,
            'pmw_bio' => "Nadia closes the loop. Every Monday she reviews the previous week's traffic, engagement, search rankings, and affiliate click data — and turns it into specific, actionable intelligence for the team. She identifies which articles are working and why, which ones are underperforming and what to do about it, and where the next content opportunities are hiding in the data. Without Nadia, the team would be publishing into a void. With her, everything compounds.",
            'pmw_personality' => "Nadia has the methodical rigour of a data scientist and the commercial instincts of someone who cares about outcomes, not vanity metrics. She is deeply unimpressed by page views that don't convert and has a gift for finding the one number in a dashboard that actually explains what's happening. Her weekly reports are dense with insight and short on padding.",
            'pmw_quirks' => wp_json_encode( [ "Filters every metric through one question: 'did this lead to a click on an affiliate link?'", "Has no patience for high-traffic articles with 0% affiliate CTR — she calls them 'pretty failures'", "Builds correlation tables recreationally — once mapped content score vs. conversion rate across 90 articles for fun", "Her weekly reports always end with exactly three prioritised recommendations, never two, never four" ] ),
            'pmw_specialisms' => wp_json_encode( [ 'Google Analytics 4', 'Search Console', 'Microsoft Clarity', 'Heatmap Analysis', 'Conversion Optimisation', 'SEO Performance', 'Scoring Model Validation', 'Revenue Attribution' ] ),
            'pmw_avatar_image_url' => '',
            'pmw_avatar_video_url' => '',
        ],
    ];
}


// ─────────────────────────────────────────────
// 4. ACF FIELD GROUPS
// ─────────────────────────────────────────────

add_action( 'acf/init', 'pmw_register_acf_fields' );

function pmw_register_acf_fields() {

    if ( ! function_exists( 'acf_add_local_field_group' ) ) return;

    // ── Dealer Fields ────────────────────────
    acf_add_local_field_group( [
        'key'    => 'group_dealer_fields',
        'title'  => 'Dealer Details',
        'fields' => [
            [
                'key'              => 'field_dealer_short_description',
                'label'            => 'Short Description',
                'name'             => 'short_description',
                'type'             => 'textarea',
                'rows'             => 3,
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'shortDescription',
            ],
            [
                'key'              => 'field_dealer_rating',
                'label'            => 'Rating',
                'name'             => 'rating',
                'type'             => 'number',
                'min'              => 0,
                'max'              => 5,
                'step'             => 0.1,
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'rating',
            ],
            [
                'key'              => 'field_dealer_review_link',
                'label'            => 'Review Link',
                'name'             => 'review_link',
                'type'             => 'url',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'reviewLink',
            ],
            [
                'key'              => 'field_dealer_affiliate_link',
                'label'            => 'Affiliate Link',
                'name'             => 'affiliate_link',
                'type'             => 'url',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'affiliateLink',
            ],
            [
                'key'              => 'field_dealer_logo',
                'label'            => 'Logo',
                'name'             => 'logo',
                'type'             => 'image',
                'return_format'    => 'array',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'logo',
            ],
            [
                'key'              => 'field_dealer_featured',
                'label'            => 'Featured',
                'name'             => 'featured',
                'type'             => 'true_false',
                'ui'               => 1,
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'featured',
            ],
        ],
        'location' => [
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'dealer' ] ],
        ],
        'show_in_graphql'     => 1,
        'graphql_field_name'  => 'dealers',
    ] );

    // ── Affiliate Product Fields ─────────────
    acf_add_local_field_group( [
        'key'    => 'group_affiliate_product_fields',
        'title'  => 'Product Details',
        'fields' => [
            [
                'key'   => 'field_product_price',
                'label' => 'Price',
                'name'  => 'price',
                'type'  => 'text',
                'show_in_graphql' => 1,
            ],
            [
                'key'              => 'field_product_original_price',
                'label'            => 'Original Price',
                'name'             => 'original_price',
                'type'             => 'text',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'originalPrice',
            ],
            [
                'key'              => 'field_product_affiliate_link',
                'label'            => 'Affiliate Link',
                'name'             => 'affiliate_link',
                'type'             => 'url',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'affiliateLink',
            ],
            [
                'key'              => 'field_product_dealer_name',
                'label'            => 'Dealer Name',
                'name'             => 'dealer_name',
                'type'             => 'text',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'dealerName',
            ],
            [
                'key'   => 'field_product_badge',
                'label' => 'Badge (e.g. Best Seller)',
                'name'  => 'badge',
                'type'  => 'text',
                'show_in_graphql' => 1,
            ],
            [
                'key'   => 'field_product_features',
                'label' => 'Features',
                'name'  => 'features',
                'type'  => 'textarea',
                'instructions' => 'One feature per line (e.g. IRA Eligible)',
                'show_in_graphql' => 1,
            ],
        ],
        'location' => [
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'affiliate-product' ] ],
        ],
        'show_in_graphql'    => 1,
        'graphql_field_name' => 'productDetails',
    ] );

    // ── Market Insight Fields ────────────────
    acf_add_local_field_group( [
        'key'    => 'group_market_insight_fields',
        'title'  => 'Article Meta',
        'fields' => [
            [
                'key'              => 'field_insight_read_time',
                'label'            => 'Read Time',
                'name'             => 'read_time',
                'type'             => 'text',
                'placeholder'      => '5 min read',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'readTime',
            ],
            [
                'key'   => 'field_insight_sponsored',
                'label' => 'Sponsored',
                'name'  => 'sponsored',
                'type'  => 'true_false',
                'ui'    => 1,
                'show_in_graphql' => 1,
            ],
        ],
        'location' => [
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'market-insight' ] ],
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'post' ] ],
        ],
        'show_in_graphql'    => 1,
        'graphql_field_name' => 'articleMeta',
    ] );

    // ── Homepage Settings ────────────────────
    acf_add_local_field_group( [
        'key'    => 'group_homepage_settings',
        'title'  => 'Homepage Settings',
        'fields' => [
            [
                'key'   => 'field_homepage_hero',
                'label' => 'Hero',
                'name'  => 'hero',
                'type'  => 'group',
                'show_in_graphql' => 1,
                'sub_fields' => [
                    [
                        'key'   => 'field_hero_title',
                        'label' => 'Title',
                        'name'  => 'title',
                        'type'  => 'text',
                        'show_in_graphql' => 1,
                    ],
                    [
                        'key'   => 'field_hero_subtitle',
                        'label' => 'Subtitle',
                        'name'  => 'subtitle',
                        'type'  => 'textarea',
                        'rows'  => 2,
                        'show_in_graphql' => 1,
                    ],
                    [
                        'key'              => 'field_hero_background_image',
                        'label'            => 'Background Image',
                        'name'             => 'background_image',
                        'type'             => 'image',
                        'return_format'    => 'array',
                        'show_in_graphql'  => 1,
                        'graphql_field_name' => 'backgroundImage',
                    ],
                ],
            ],
            [
                'key'   => 'field_homepage_newsletter',
                'label' => 'Newsletter',
                'name'  => 'newsletter',
                'type'  => 'group',
                'show_in_graphql' => 1,
                'sub_fields' => [
                    [
                        'key'   => 'field_newsletter_email',
                        'label' => 'Signup Email (Mailchimp etc.)',
                        'name'  => 'email',
                        'type'  => 'email',
                        'show_in_graphql' => 1,
                    ],
                ],
            ],
        ],
        'location' => [
            [ [ 'param' => 'page_type', 'operator' => '==', 'value' => 'front_page' ] ],
        ],
        'show_in_graphql'    => 1,
        'graphql_field_name' => 'homepageSettings',
    ] );

    // ── Gem Index Data ─────────────────────
    acf_add_local_field_group( [
        'key'    => 'group_gem_index_data',
        'title'  => 'Gem Index Data',
        'fields' => [
            [
                'key'                => 'field_gem_index_gem_type',
                'label'              => 'Gem Type',
                'name'               => 'gem_type',
                'type'               => 'text',
                'instructions'       => 'e.g. Ruby, Sapphire, Emerald',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'gemType',
            ],
            [
                'key'                => 'field_gem_index_gem_category',
                'label'              => 'Category',
                'name'               => 'gem_category',
                'type'               => 'select',
                'choices'            => [
                    'precious'      => 'Precious',
                    'semi-precious' => 'Semi-Precious',
                    'organic'       => 'Organic',
                ],
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'gemCategory',
            ],
            [
                'key'                => 'field_gem_index_price_low_usd',
                'label'              => 'Price Range (Low) USD',
                'name'               => 'price_low_usd',
                'type'               => 'number',
                'instructions'       => 'Per carat, USD',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'priceLowUsd',
            ],
            [
                'key'                => 'field_gem_index_price_high_usd',
                'label'              => 'Price Range (High) USD',
                'name'               => 'price_high_usd',
                'type'               => 'number',
                'instructions'       => 'Per carat, USD',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'priceHighUsd',
            ],
            [
                'key'                => 'field_gem_index_price_low_gbp',
                'label'              => 'Price Range (Low) GBP',
                'name'               => 'price_low_gbp',
                'type'               => 'number',
                'instructions'       => 'Per carat, GBP',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'priceLowGbp',
            ],
            [
                'key'                => 'field_gem_index_price_high_gbp',
                'label'              => 'Price Range (High) GBP',
                'name'               => 'price_high_gbp',
                'type'               => 'number',
                'instructions'       => 'Per carat, GBP',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'priceHighGbp',
            ],
            [
                'key'                => 'field_gem_index_quality_grade',
                'label'              => 'Quality Grade',
                'name'               => 'quality_grade',
                'type'               => 'select',
                'choices'            => [
                    'commercial' => 'Commercial',
                    'good'       => 'Good',
                    'fine'       => 'Fine',
                    'extra_fine' => 'Extra Fine',
                ],
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'qualityGrade',
            ],
            [
                'key'                => 'field_gem_index_carat_range',
                'label'              => 'Carat Weight Range',
                'name'               => 'carat_range',
                'type'               => 'text',
                'instructions'       => 'e.g. "1–3ct"',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'caratRange',
            ],
            [
                'key'                => 'field_gem_index_producing_countries',
                'label'              => 'Key Producing Countries',
                'name'               => 'producing_countries',
                'type'               => 'text',
                'instructions'       => 'Comma-separated',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'producingCountries',
            ],
            [
                'key'                => 'field_gem_index_market_trend',
                'label'              => 'Market Trend',
                'name'               => 'market_trend',
                'type'               => 'select',
                'choices'            => [
                    'rising'   => 'Rising',
                    'stable'   => 'Stable',
                    'declining' => 'Declining',
                ],
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'marketTrend',
            ],
            [
                'key'                => 'field_gem_index_trend_percentage',
                'label'              => 'Trend Percentage (%)',
                'name'               => 'trend_percentage',
                'type'               => 'number',
                'instructions'       => 'e.g. 4.2 for +4.2%',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'trendPercentage',
            ],
            [
                'key'                => 'field_gem_index_last_reviewed',
                'label'              => 'Last Reviewed Date',
                'name'               => 'last_reviewed',
                'type'               => 'date_picker',
                'display_format'     => 'F j, Y',
                'return_format'      => 'Y-m-d',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'lastReviewed',
            ],
            [
                'key'                => 'field_gem_index_reviewer_notes',
                'label'              => 'Reviewer Notes',
                'name'               => 'reviewer_notes',
                'type'               => 'textarea',
                'instructions'       => 'Internal editorial notes',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'reviewerNotes',
            ],
            [
                'key'                => 'field_gem_index_data_source',
                'label'              => 'Data Source',
                'name'               => 'data_source',
                'type'               => 'text',
                'instructions'       => 'e.g. "IGS Market Research, Q1 2025"',
                'show_in_graphql'    => 1,
                'graphql_field_name' => 'dataSource',
            ],
        ],
        'location' => [
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'gem_index' ] ],
        ],
        'show_in_graphql'    => 1,
        'graphql_field_name' => 'gemIndexData',
    ] );

    // ── Page Sections (Flexible Content for all Pages) ──
    // Check if ACF PRO is active and flexible content is available
    $has_flexible = function_exists( 'acf_get_field_type' ) && acf_get_field_type( 'flexible_content' );

    if ( ! $has_flexible ) {
        add_action( 'admin_notices', function() {
            echo '<div class="notice notice-warning"><p><strong>PMW Core:</strong> Page Sections require ACF PRO (flexible content). <a href="https://www.advancedcustomfields.com/pro/" target="_blank">Upgrade to ACF PRO</a> to manage page sections from WordPress.</p></div>';
        } );
        
        // Fallback: register a simple text field so at least something shows in the editor
        acf_add_local_field_group( [
            'key'    => 'group_page_sections_fallback',
            'title'  => 'Page Content',
            'fields' => [
                [
                    'key'   => 'field_page_content_fallback',
                    'label' => 'Content',
                    'name'  => 'page_content_fallback',
                    'type'  => 'wysiwyg',
                    'instructions' => 'ACF PRO is required for full page sections functionality. Please install ACF PRO to use the flexible content builder.',
                    'show_in_graphql' => 1,
                ],
            ],
            'location' => [
                [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'page' ] ],
            ],
            'show_in_graphql' => 1,
            'graphql_field_name' => 'pageContent',
        ] );
    } else {
        // ACF PRO is active - register the full flexible content field group
        acf_add_local_field_group( [
            'key'    => 'group_page_sections',
            'title'  => 'Page Sections',
            'fields' => [
                [
                    'key'              => 'field_page_breadcrumb_label',
                    'label'            => 'Breadcrumb Label (Short Name)',
                    'name'             => 'breadcrumb_label',
                    'type'             => 'text',
                    'instructions'     => 'Short name for breadcrumbs (e.g. "About", "Gold"). Leave empty to use page title.',
                    'show_in_graphql'  => 1,
                    'graphql_field_name' => 'breadcrumbLabel',
                ],
                [
                    'key'          => 'field_page_sections',
                    'label'        => 'Page Sections',
                    'name'         => 'page_sections',
                    'type'         => 'flexible_content',
                    'button_label' => 'Add Section',
                    'instructions' => 'Build the page layout. Add hero, rich text, team grid, stats, CTA, and more.',
                    'layouts'      => [
                        [
                            'key'        => 'layout_hero',
                            'name'       => 'hero',
                            'label'      => 'Hero',
                            'display'    => 'block',
                            'sub_fields' => [
                                [ 'key' => 'field_hero_heading', 'label' => 'Heading', 'name' => 'heading', 'type' => 'text', 'show_in_graphql' => 1 ],
                                [ 'key' => 'field_hero_subheading', 'label' => 'Subheading', 'name' => 'subheading', 'type' => 'textarea', 'rows' => 2, 'show_in_graphql' => 1 ],
                                [ 'key' => 'field_hero_background_image', 'label' => 'Background Image', 'name' => 'background_image', 'type' => 'image', 'return_format' => 'array', 'show_in_graphql' => 1, 'graphql_field_name' => 'backgroundImage' ],
                                [ 'key' => 'field_hero_topic_pill', 'label' => 'Topic/Category Pill', 'name' => 'topic_pill', 'type' => 'text', 'show_in_graphql' => 1, 'graphql_field_name' => 'topicPill' ],
                                [
                                    'key'        => 'field_hero_breadcrumbs',
                                    'label'      => 'Breadcrumb Links',
                                    'name'       => 'breadcrumbs',
                                    'type'       => 'repeater',
                                    'layout'     => 'table',
                                    'instructions' => 'Parent path links (e.g. Home, Precious Metals). The current page appears as non-linked text at the end.',
                                    'sub_fields' => [
                                        [ 'key' => 'field_breadcrumb_label', 'label' => 'Label', 'name' => 'label', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_breadcrumb_url', 'label' => 'URL', 'name' => 'url', 'type' => 'url', 'show_in_graphql' => 1 ],
                                    ],
                                ],
                                [
                                    'key'        => 'field_hero_bookmarks',
                                    'label'      => 'Page Bookmarks',
                                    'name'       => 'bookmarks',
                                    'type'       => 'repeater',
                                    'layout'     => 'table',
                                    'sub_fields' => [
                                        [ 'key' => 'field_bookmark_label', 'label' => 'Label', 'name' => 'label', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_bookmark_url', 'label' => 'URL', 'name' => 'url', 'type' => 'url', 'show_in_graphql' => 1 ],
                                    ],
                                ],
                            ],
                        ],
                        [
                            'key'        => 'layout_rich_text',
                            'name'       => 'rich_text',
                            'label'      => 'Rich Text',
                            'display'    => 'block',
                            'sub_fields' => [
                                [ 'key' => 'field_rich_text_content', 'label' => 'Content', 'name' => 'content', 'type' => 'wysiwyg', 'show_in_graphql' => 1 ],
                            ],
                        ],
                        [
                            'key'        => 'layout_team_grid',
                            'name'       => 'team_grid',
                            'label'      => 'Team Grid',
                            'display'    => 'block',
                            'sub_fields' => [
                                [ 'key' => 'field_team_heading', 'label' => 'Heading', 'name' => 'heading', 'type' => 'text', 'show_in_graphql' => 1 ],
                                [ 'key' => 'field_team_show_tiers', 'label' => 'Show Tiers', 'name' => 'show_tiers', 'type' => 'true_false', 'ui' => 1, 'show_in_graphql' => 1, 'graphql_field_name' => 'showTiers' ],
                                [ 'key' => 'field_team_filter_status', 'label' => 'Filter Status (optional)', 'name' => 'filter_status', 'type' => 'text', 'show_in_graphql' => 1, 'graphql_field_name' => 'filterStatus' ],
                            ],
                        ],
                        [
                            'key'        => 'layout_pipeline_steps',
                            'name'       => 'pipeline_steps',
                            'label'      => 'Pipeline Steps',
                            'display'    => 'block',
                            'sub_fields' => [
                                [ 'key' => 'field_pipeline_heading', 'label' => 'Heading', 'name' => 'heading', 'type' => 'text', 'show_in_graphql' => 1 ],
                                [
                                    'key'        => 'field_pipeline_steps',
                                    'label'      => 'Steps',
                                    'name'       => 'steps',
                                    'type'       => 'repeater',
                                    'layout'     => 'table',
                                    'sub_fields' => [
                                        [ 'key' => 'field_step_label', 'label' => 'Label', 'name' => 'label', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_step_description', 'label' => 'Description', 'name' => 'description', 'type' => 'textarea', 'rows' => 2, 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_step_agent_role', 'label' => 'Agent Role', 'name' => 'agent_role', 'type' => 'text', 'show_in_graphql' => 1, 'graphql_field_name' => 'agentRole' ],
                                    ],
                                ],
                            ],
                        ],
                        [
                            'key'        => 'layout_stats_bar',
                            'name'       => 'stats_bar',
                            'label'      => 'Stats Bar',
                            'display'    => 'block',
                            'sub_fields' => [
                                [
                                    'key'        => 'field_stats_bar_stats',
                                    'label'      => 'Stats',
                                    'name'       => 'stats',
                                    'type'       => 'repeater',
                                    'layout'     => 'table',
                                    'sub_fields' => [
                                        [ 'key' => 'field_stat_label', 'label' => 'Label', 'name' => 'label', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_stat_value', 'label' => 'Value', 'name' => 'value', 'type' => 'text', 'show_in_graphql' => 1 ],
                                    ],
                                ],
                            ],
                        ],
                        [
                            'key'        => 'layout_team_performance_stats',
                            'name'       => 'team_performance_stats',
                            'label'      => 'Team Performance Stats (AI Work)',
                            'display'    => 'block',
                            'sub_fields' => [
                                [
                                    'key'        => 'field_team_performance_stats',
                                    'label'      => 'Stats',
                                    'name'       => 'stats',
                                    'type'       => 'repeater',
                                    'layout'     => 'table',
                                    'sub_fields' => [
                                        [ 'key' => 'field_tps_label', 'label' => 'Label', 'name' => 'label', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_tps_value', 'label' => 'Value', 'name' => 'value', 'type' => 'text', 'show_in_graphql' => 1 ],
                                    ],
                                ],
                            ],
                        ],
                        [
                            'key'        => 'layout_our_values',
                            'name'       => 'our_values',
                            'label'      => 'Our Values',
                            'display'    => 'block',
                            'sub_fields' => [
                                [ 'key' => 'field_our_values_heading', 'label' => 'Heading', 'name' => 'heading', 'type' => 'text', 'default_value' => 'Our Values', 'show_in_graphql' => 1 ],
                                [
                                    'key'        => 'field_our_values_values',
                                    'label'      => 'Values',
                                    'name'       => 'values',
                                    'type'       => 'repeater',
                                    'layout'     => 'block',
                                    'sub_fields' => [
                                        [ 'key' => 'field_value_icon', 'label' => 'Icon (lucide name, e.g. shield, book-open, target, eye)', 'name' => 'icon', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_value_title', 'label' => 'Title', 'name' => 'title', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_value_description', 'label' => 'Description', 'name' => 'description', 'type' => 'textarea', 'rows' => 2, 'show_in_graphql' => 1 ],
                                    ],
                                ],
                            ],
                        ],
                        [
                            'key'        => 'layout_cta_block',
                            'name'       => 'cta_block',
                            'label'      => 'CTA Block',
                            'display'    => 'block',
                            'sub_fields' => [
                                [ 'key' => 'field_cta_variant', 'label' => 'Variant', 'name' => 'variant', 'type' => 'select', 'choices' => [ 'dark' => 'Dark', 'light' => 'Light' ], 'default_value' => 'dark', 'show_in_graphql' => 1 ],
                                [ 'key' => 'field_cta_heading', 'label' => 'Heading', 'name' => 'heading', 'type' => 'text', 'show_in_graphql' => 1 ],
                                [ 'key' => 'field_cta_body', 'label' => 'Body', 'name' => 'body', 'type' => 'wysiwyg', 'show_in_graphql' => 1 ],
                                [ 'key' => 'field_cta_button_label', 'label' => 'Button Label', 'name' => 'button_label', 'type' => 'text', 'show_in_graphql' => 1, 'graphql_field_name' => 'buttonLabel' ],
                                [ 'key' => 'field_cta_button_url', 'label' => 'Button URL', 'name' => 'button_url', 'type' => 'url', 'show_in_graphql' => 1, 'graphql_field_name' => 'buttonUrl' ],
                            ],
                        ],
                        [
                            'key'        => 'layout_link_cards',
                            'name'       => 'link_cards',
                            'label'      => 'Link Cards',
                            'display'    => 'block',
                            'sub_fields' => [
                                [
                                    'key'        => 'field_link_cards_cards',
                                    'label'      => 'Cards',
                                    'name'       => 'cards',
                                    'type'       => 'repeater',
                                    'layout'     => 'block',
                                    'sub_fields' => [
                                        [ 'key' => 'field_card_label', 'label' => 'Label', 'name' => 'label', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_card_description', 'label' => 'Description', 'name' => 'description', 'type' => 'textarea', 'rows' => 2, 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_card_url', 'label' => 'URL', 'name' => 'url', 'type' => 'url', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_card_icon', 'label' => 'Icon (lucide name)', 'name' => 'icon', 'type' => 'text', 'show_in_graphql' => 1 ],
                                    ],
                                ],
                            ],
                        ],
                        [
                            'key'        => 'layout_data_sources',
                            'name'       => 'data_sources',
                            'label'      => 'Data Sources',
                            'display'    => 'block',
                            'sub_fields' => [
                                [
                                    'key'        => 'field_data_sources_items',
                                    'label'      => 'Sources',
                                    'name'       => 'items',
                                    'type'       => 'repeater',
                                    'layout'     => 'table',
                                    'sub_fields' => [
                                        [ 'key' => 'field_source_name', 'label' => 'Name', 'name' => 'name', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_source_description', 'label' => 'Description', 'name' => 'description', 'type' => 'textarea', 'rows' => 2, 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_source_url', 'label' => 'URL', 'name' => 'url', 'type' => 'url', 'show_in_graphql' => 1 ],
                                    ],
                                ],
                            ],
                        ],
                        [
                            'key'        => 'layout_faq',
                            'name'       => 'faq',
                            'label'      => 'FAQ Accordion',
                            'display'    => 'block',
                            'sub_fields' => [
                                [
                                    'key'        => 'field_faq_items',
                                    'label'      => 'Items',
                                    'name'       => 'items',
                                    'type'       => 'repeater',
                                    'layout'     => 'block',
                                    'sub_fields' => [
                                        [ 'key' => 'field_faq_question', 'label' => 'Question', 'name' => 'question', 'type' => 'text', 'show_in_graphql' => 1 ],
                                        [ 'key' => 'field_faq_answer', 'label' => 'Answer', 'name' => 'answer', 'type' => 'textarea', 'rows' => 3, 'show_in_graphql' => 1 ],
                                    ],
                                ],
                            ],
                        ],
                        [
                            'key'        => 'layout_image_text',
                            'name'       => 'image_text',
                            'label'      => 'Image + Text',
                            'display'    => 'block',
                            'sub_fields' => [
                                [ 'key' => 'field_image_text_image', 'label' => 'Image', 'name' => 'image', 'type' => 'image', 'return_format' => 'array', 'show_in_graphql' => 1 ],
                                [ 'key' => 'field_image_text_content', 'label' => 'Content', 'name' => 'content', 'type' => 'wysiwyg', 'show_in_graphql' => 1 ],
                                [ 'key' => 'field_image_text_alignment', 'label' => 'Image Position', 'name' => 'alignment', 'type' => 'select', 'choices' => [ 'left' => 'Left', 'right' => 'Right' ], 'show_in_graphql' => 1 ],
                            ],
                        ],
                    ],
                    'show_in_graphql'  => 1,
                    'graphql_field_name' => 'sections',
                ],
            ],
            'location' => [
                [
                    [
                        'param' => 'post_type',
                        'operator' => '==',
                        'value' => 'page',
                    ],
                ],
            ],
            'show_in_graphql'    => 1,
            'graphql_field_name' => 'pageSections',
            'graphql_types'      => [ 'Page' ],
            'active'             => true,
            'description'        => 'Build custom page layouts using flexible content sections',
        ]);
    } // end ACF PRO check

}

/**
 * Fallback: register pageSections + layout types when ACF PRO (flexible content) is not available.
 * Returns empty sections so the frontend query doesn't fail.
 */
function pmw_register_page_sections_fallback() {
    if ( ! function_exists( 'register_graphql_field' ) || ! function_exists( 'register_graphql_object_type' ) || ! function_exists( 'register_graphql_union_type' ) ) {
        return;
    }
    $media_stub = 'Page_PageSections_MediaStub';
    register_graphql_object_type( $media_stub, [
        'description' => __( 'Media stub for page sections fallback', 'pmw-core' ),
        'fields'      => [
            'sourceUrl' => [ 'type' => 'String' ],
            'altText'   => [ 'type' => 'String' ],
        ],
    ] );
    $layout_types = [
        'Page_PageSections_Sections_HeroLayout',
        'Page_PageSections_Sections_RichTextLayout',
        'Page_PageSections_Sections_TeamGridLayout',
        'Page_PageSections_Sections_PipelineStepsLayout',
        'Page_PageSections_Sections_StatsBarLayout',
        'Page_PageSections_Sections_TeamPerformanceStatsLayout',
        'Page_PageSections_Sections_OurValuesLayout',
        'Page_PageSections_Sections_CtaBlockLayout',
        'Page_PageSections_Sections_LinkCardsLayout',
        'Page_PageSections_Sections_DataSourcesLayout',
        'Page_PageSections_Sections_FaqLayout',
        'Page_PageSections_Sections_ImageTextLayout',
    ];
    foreach ( $layout_types as $type_name ) {
        register_graphql_object_type( $type_name, [
            'description' => __( 'Page section layout (stub when ACF PRO not active)', 'pmw-core' ),
            'fields'      => [
                'fieldGroupName' => [ 'type' => 'String' ],
                'heading'        => [ 'type' => 'String' ],
                'subheading'     => [ 'type' => 'String' ],
                'content'        => [ 'type' => 'String' ],
                'backgroundImage' => [ 'type' => $media_stub ],
                'topicPill'      => [ 'type' => 'String' ],
                'breadcrumbs'    => [ 'type' => [ 'list_of' => 'Page_PageSections_Sections_Bookmark' ] ],
                'bookmarks'      => [ 'type' => [ 'list_of' => 'Page_PageSections_Sections_Bookmark' ] ],
                'variant'        => [ 'type' => 'String' ],
                'showTiers'      => [ 'type' => 'Boolean' ],
                'filterStatus'   => [ 'type' => 'String' ],
                'steps'          => [ 'type' => [ 'list_of' => 'Page_PageSections_Sections_Step' ] ],
                'stats'          => [ 'type' => [ 'list_of' => 'Page_PageSections_Sections_Stat' ] ],
                'body'           => [ 'type' => 'String' ],
                'buttonLabel'    => [ 'type' => 'String' ],
                'buttonUrl'      => [ 'type' => 'String' ],
                'cards'          => [ 'type' => [ 'list_of' => 'Page_PageSections_Sections_Card' ] ],
                'items'          => [ 'type' => [ 'list_of' => 'Page_PageSections_Sections_Item' ] ],
                'image'          => [ 'type' => $media_stub ],
                'alignment'      => [ 'type' => 'String' ],
                'values'         => [ 'type' => [ 'list_of' => 'Page_PageSections_Sections_Value' ] ],
            ],
        ] );
    }
    register_graphql_object_type( 'Page_PageSections_Sections_Step', [
        'fields' => [
            'label'      => [ 'type' => 'String' ],
            'description' => [ 'type' => 'String' ],
            'agentRole'  => [ 'type' => 'String' ],
        ],
    ] );
    register_graphql_object_type( 'Page_PageSections_Sections_Stat', [
        'fields' => [
            'label' => [ 'type' => 'String' ],
            'value' => [ 'type' => 'String' ],
        ],
    ] );
    register_graphql_object_type( 'Page_PageSections_Sections_Bookmark', [
        'fields' => [
            'label' => [ 'type' => 'String' ],
            'url'   => [ 'type' => 'String' ],
        ],
    ] );
    register_graphql_object_type( 'Page_PageSections_Sections_Value', [
        'fields' => [
            'icon'        => [ 'type' => 'String' ],
            'title'       => [ 'type' => 'String' ],
            'description' => [ 'type' => 'String' ],
        ],
    ] );
    register_graphql_object_type( 'Page_PageSections_Sections_Card', [
        'fields' => [
            'label'       => [ 'type' => 'String' ],
            'description' => [ 'type' => 'String' ],
            'url'         => [ 'type' => 'String' ],
            'icon'        => [ 'type' => 'String' ],
        ],
    ] );
    register_graphql_object_type( 'Page_PageSections_Sections_Item', [
        'fields' => [
            'name'        => [ 'type' => 'String' ],
            'description' => [ 'type' => 'String' ],
            'url'         => [ 'type' => 'String' ],
            'question'    => [ 'type' => 'String' ],
            'answer'      => [ 'type' => 'String' ],
        ],
    ] );
    register_graphql_union_type( 'Page_PageSections_Sections_Union', [
        'typeNames'   => $layout_types,
        'resolveType' => function() {
            return null;
        },
    ] );
    register_graphql_object_type( 'Page_PageSections', [
        'description' => __( 'Page sections (requires ACF PRO when populated)', 'pmw-core' ),
        'fields'      => [
            'sections' => [
                'type'    => [ 'list_of' => 'Page_PageSections_Sections_Union' ],
                'resolve' => function() {
                    return [];
                },
            ],
        ],
    ] );
    register_graphql_field( 'Page', 'pageSections', [
        'type'    => 'Page_PageSections',
        'resolve' => function( $page ) {
            return [ 'sections' => [] ];
        },
    ] );
}

// ─────────────────────────────────────────────
// 5. GEM INDEX REST API (GEM-03)
// ─────────────────────────────────────────────

add_action( 'rest_api_init', 'pmw_register_gems_rest_route' );
add_action( 'rest_api_init', 'pmw_register_prices_history_route' );
add_action( 'rest_api_init', 'pmw_register_prices_latest_route' );
add_action( 'rest_api_init', 'pmw_register_prices_ticker_route' );
add_action( 'rest_api_init', 'pmw_register_subscribe_route' );
add_action( 'graphql_register_types', 'pmw_register_page_breadcrumb_graphql' );
add_action( 'graphql_register_types', 'pmw_register_tools_graphql', 15 );
add_action( 'graphql_register_types', 'pmw_register_metal_prices_graphql' );
add_action( 'graphql_register_types', 'pmw_register_team_grid_agents_graphql', 20 );

function pmw_register_page_breadcrumb_graphql() {
    register_graphql_field( 'Page', 'breadcrumbLabel', [
        'type'        => 'String',
        'description' => 'Short name for breadcrumbs (e.g. About, Gold). Falls back to page title.',
        'resolve'     => function( $source ) {
            $id = isset( $source->databaseId ) ? (int) $source->databaseId : ( isset( $source->ID ) ? (int) $source->ID : 0 );
            if ( ! $id ) return null;
            $val = function_exists( 'get_field' ) ? get_field( 'breadcrumb_label', $id ) : null;
            if ( is_string( $val ) && $val !== '' ) return $val;
            $post = get_post( $id );
            return $post && isset( $post->post_title ) ? $post->post_title : null;
        },
    ] );
}

function pmw_register_tools_graphql() {
    $tool_id = function( $source ) {
        return isset( $source->databaseId ) ? (int) $source->databaseId : ( isset( $source->ID ) ? (int) $source->ID : 0 );
    };
    register_graphql_field( 'Tool', 'toolStatus', [
        'type'        => 'String',
        'description' => 'live | coming-soon | draft',
        'resolve'     => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_tool_status', true ),
    ] );
    register_graphql_field( 'Tool', 'displayOrder', [
        'type'    => 'Int',
        'resolve' => fn( $post ) => (int) get_post_meta( $tool_id( $post ), 'pmw_display_order', true ),
    ] );
    register_graphql_field( 'Tool', 'implementation', [
        'type'    => 'String',
        'resolve' => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_implementation', true ),
    ] );
    register_graphql_field( 'Tool', 'embedCode', [
        'type'    => 'String',
        'resolve' => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_embed_code', true ),
    ] );
    register_graphql_field( 'Tool', 'reactComponent', [
        'type'    => 'String',
        'resolve' => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_react_component', true ),
    ] );
    register_graphql_field( 'Tool', 'affiliatePartner', [
        'type'    => 'String',
        'resolve' => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_affiliate_partner', true ),
    ] );
    register_graphql_field( 'Tool', 'affiliateCtaText', [
        'type'    => 'String',
        'resolve' => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_affiliate_cta_text', true ),
    ] );
    register_graphql_field( 'Tool', 'affiliateCtaUrl', [
        'type'    => 'String',
        'resolve' => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_affiliate_cta_url', true ),
    ] );
    register_graphql_field( 'Tool', 'affiliateCtaPosition', [
        'type'    => 'String',
        'resolve' => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_affiliate_cta_position', true ),
    ] );
    register_graphql_field( 'Tool', 'isFeatured', [
        'type'    => 'Boolean',
        'resolve' => fn( $post ) => (bool) get_post_meta( $tool_id( $post ), 'pmw_is_featured', true ),
    ] );
    register_graphql_field( 'Tool', 'metalRelevance', [
        'type'    => [ 'list_of' => 'String' ],
        'resolve' => function( $post ) {
            $raw = get_post_meta( $tool_id( $post ), 'pmw_metal_relevance', true );
            $arr = is_string( $raw ) ? json_decode( $raw, true ) : $raw;
            return is_array( $arr ) ? $arr : [];
        },
    ] );
    register_graphql_field( 'Tool', 'showDisclaimer', [
        'type'    => 'Boolean',
        'resolve' => fn( $post ) => (bool) get_post_meta( $tool_id( $post ), 'pmw_show_disclaimer', true ),
    ] );
    register_graphql_field( 'Tool', 'disclaimerText', [
        'type'    => 'String',
        'resolve' => fn( $post ) => get_post_meta( $tool_id( $post ), 'pmw_disclaimer_text', true ),
    ] );

    register_graphql_field( 'RootQuery', 'dealerComparison', [
        'type'        => [ 'list_of' => 'String' ],
        'description' => 'Returns JSON-encoded dealer comparison rows',
        'resolve'     => function() {
            $data    = get_option( 'pmw_dealer_comparison_data', '[]' );
            $dealers = json_decode( $data, true );
            if ( ! is_array( $dealers ) ) $dealers = [];
            usort( $dealers, function( $a, $b ) {
                return ( $a['display_order'] ?? 99 ) <=> ( $b['display_order'] ?? 99 );
            } );
            return array_map( 'wp_json_encode', $dealers );
        },
    ] );
}
add_action( 'rest_api_init', 'pmw_register_contact_submit_route' );
add_action( 'rest_api_init', 'pmw_register_agents_rest_route' );
add_action( 'acf/init', 'pmw_register_market_data_options_page' );
add_action( 'acf/init', 'pmw_register_site_settings_options_page' );
add_action( 'admin_menu', 'pmw_dealer_comparison_options_page' );
add_action( 'admin_init', 'pmw_dealer_comparison_register_setting' );

function pmw_dealer_comparison_options_page() {
    add_options_page(
        'Dealer Comparison Data',
        'Dealer Comparison Data',
        'manage_options',
        'pmw-dealer-comparison',
        'pmw_dealer_comparison_render'
    );
}

function pmw_dealer_comparison_register_setting() {
    register_setting( 'pmw_dealer_comparison', 'pmw_dealer_comparison_data', [
        'type'              => 'string',
        'sanitize_callback' => function( $v ) {
            $dec = json_decode( $v );
            return is_array( $dec ) ? wp_json_encode( $dec ) : '[]';
        },
    ] );
}

function pmw_dealer_comparison_render() {
    if ( ! current_user_can( 'manage_options' ) ) return;
    $val = get_option( 'pmw_dealer_comparison_data', '[]' );
    if ( is_string( $val ) ) {
        $dec = json_decode( $val );
        if ( is_array( $dec ) ) $val = wp_json_encode( $dec, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
    }
    echo '<div class="wrap"><h1>Dealer Comparison Data</h1>';
    echo '<form method="post" action="options.php">';
    settings_fields( 'pmw_dealer_comparison' );
    echo '<table class="form-table"><tr><th>JSON array</th><td>';
    echo '<textarea name="pmw_dealer_comparison_data" rows="20" class="large-text code">' . esc_textarea( $val ) . '</textarea>';
    echo '<p class="description">JSON array of dealer objects. Each object may include display_order, name, etc. Sorted by display_order in GraphQL.</p>';
    echo '</td></tr></table>';
    submit_button();
    echo '</form></div>';
}

// ── HOME-02: Mailchimp newsletter subscribe (WordPress REST; frontend has no /api) ──
function pmw_register_subscribe_route() {
    register_rest_route( 'pmw/v1', '/subscribe', [
        'methods'             => 'POST',
        'callback'            => 'pmw_rest_post_subscribe',
        'permission_callback' => '__return_true',
        'args'                => [
            'email' => [
                'required'          => true,
                'type'              => 'string',
                'sanitize_callback' => 'sanitize_email',
                'validate_callback'  => function ( $value ) {
                    return is_email( $value ) ? true : new WP_Error( 'invalid_email', 'Please enter a valid email address.', [ 'status' => 400 ] );
                },
            ],
            'tags' => [
                'required' => false,
                'type'     => 'array',
                'items'    => [ 'type' => 'string' ],
                'default'  => [],
            ],
        ],
    ] );
}

function pmw_rest_post_subscribe( WP_REST_Request $request ) {
    $email = $request->get_param( 'email' );
    $tags  = $request->get_param( 'tags' );
    if ( ! is_array( $tags ) ) {
        $tags = [];
    }
    $api_key = defined( 'PMW_MAILCHIMP_API_KEY' ) ? PMW_MAILCHIMP_API_KEY : '';
    $list_id = defined( 'PMW_MAILCHIMP_LIST_ID' ) ? PMW_MAILCHIMP_LIST_ID : '';

    if ( empty( $api_key ) || empty( $list_id ) ) {
        return new WP_REST_Response( [ 'success' => false, 'message' => 'Newsletter is not configured.' ], 503 );
    }

    // Debug: confirm constants at runtime (set PMW_MAILCHIMP_DEBUG in wp-config to enable; remove after 403 resolved)
    if ( defined( 'PMW_MAILCHIMP_DEBUG' ) && PMW_MAILCHIMP_DEBUG && function_exists( 'error_log' ) ) {
        error_log( '[PMW Newsletter] MC KEY: ' . ( defined( 'PMW_MAILCHIMP_API_KEY' ) ? 'SET (' . strlen( $api_key ) . ' chars)' : 'NOT SET' ) );
        error_log( '[PMW Newsletter] MC LIST: ' . ( defined( 'PMW_MAILCHIMP_LIST_ID' ) ? $list_id : 'NOT SET' ) );
    }

    // Data centre from API key suffix (e.g. xxxxx-us16 → us16)
    $parts = explode( '-', $api_key );
    $dc    = ( count( $parts ) >= 2 && ! empty( $parts[1] ) ) ? strtolower( $parts[1] ) : 'us1';

    if ( defined( 'PMW_MAILCHIMP_DEBUG' ) && PMW_MAILCHIMP_DEBUG && function_exists( 'error_log' ) ) {
        error_log( '[PMW Newsletter] DC: ' . $dc );
    }

    $url  = sprintf( 'https://%s.api.mailchimp.com/3.0/lists/%s/members', $dc, $list_id );
    $body = [
        'email_address' => $email,
        'status'        => 'subscribed',
    ];
    // Tags are not sent in initial POST (can cause failures); applied via separate call after success (Fix 4)

    $resp = wp_remote_post( $url, [
        'headers' => [
            'Authorization' => 'Basic ' . base64_encode( 'anystring:' . $api_key ),
            'Content-Type'  => 'application/json',
        ],
        'body'    => wp_json_encode( $body ),
        'timeout' => 15,
    ] );

    if ( is_wp_error( $resp ) ) {
        return new WP_REST_Response( [ 'success' => false, 'message' => 'Subscription failed. Please try again later.' ], 502 );
    }

    $code = wp_remote_retrieve_response_code( $resp );
    $raw  = wp_remote_retrieve_body( $resp );
    $data = json_decode( $raw, true );

    if ( function_exists( 'error_log' ) ) {
        if ( defined( 'PMW_MAILCHIMP_DEBUG' ) && PMW_MAILCHIMP_DEBUG ) {
            error_log( '[PMW Newsletter] MC RESPONSE: ' . $raw );
        } elseif ( $code !== 200 ) {
            error_log( '[PMW Newsletter] Mailchimp response code=' . $code . ' body=' . $raw );
        }
    }

    if ( $code === 200 || $code === 201 ) {
        // Apply tags via separate call (Fix 4); tag failures are non-fatal
        if ( ! empty( $tags ) ) {
            $subscriber_hash = md5( strtolower( trim( $email ) ) );
            $tags_url        = sprintf(
                'https://%s.api.mailchimp.com/3.0/lists/%s/members/%s/tags',
                $dc,
                $list_id,
                $subscriber_hash
            );
            wp_remote_post( $tags_url, [
                'headers' => [
                    'Authorization' => 'Basic ' . base64_encode( 'anystring:' . $api_key ),
                    'Content-Type'  => 'application/json',
                ],
                'body'    => wp_json_encode( [
                    'tags' => array_map( function ( $name ) {
                        return [ 'name' => $name, 'status' => 'active' ];
                    }, $tags ),
                ] ),
                'timeout' => 10,
            ] );
        }
        return new WP_REST_Response( [ 'success' => true, 'message' => 'Subscribed! Check your email to confirm.' ], 200 );
    }

    // 400: validation or duplicate (214 = Member Exists)
    if ( $code === 400 && is_array( $data ) ) {
        $msg     = isset( $data['title'] ) ? $data['title'] : 'Invalid request';
        $detail  = isset( $data['detail'] ) ? (string) $data['detail'] : '';
        $status  = isset( $data['status'] ) ? (int) $data['status'] : 0;
        if ( $status === 214 || stripos( $detail, 'already' ) !== false || stripos( $detail, 'exists' ) !== false ) {
            $msg = 'This email is already subscribed.';
        }
        return new WP_REST_Response( [ 'success' => false, 'message' => $msg, 'error_code' => $status ? $status : 400 ], 400 );
    }

    // 403, 401, 5xx etc.: do not expose technical detail to frontend
    $err_code = is_array( $data ) && isset( $data['status'] ) ? (int) $data['status'] : $code;
    return new WP_REST_Response( [
        'success'    => false,
        'message'    => 'Subscription failed. Please try again.',
        'error_code' => $err_code,
    ], $code >= 400 ? $code : 502 );
}

// ── Contact form submit: POST /pmw/v1/contact/submit ──
function pmw_register_contact_submit_route() {
    register_rest_route( 'pmw/v1', '/contact/submit', [
        'methods'             => 'POST',
        'callback'            => 'pmw_rest_post_contact_submit',
        'permission_callback' => '__return_true',
        'args'                => [
            'name'    => [
                'required'          => true,
                'type'              => 'string',
                'sanitize_callback' => 'sanitize_text_field',
            ],
            'email'   => [
                'required'          => true,
                'type'              => 'string',
                'sanitize_callback' => 'sanitize_email',
                'validate_callback'  => function ( $value ) {
                    return is_email( $value ) ? true : new WP_Error( 'invalid_email', 'Please enter a valid email address.', [ 'status' => 400 ] );
                },
            ],
            'subject' => [
                'required'          => true,
                'type'              => 'string',
                'sanitize_callback' => 'sanitize_text_field',
            ],
            'message' => [
                'required'          => true,
                'type'              => 'string',
                'sanitize_callback' => 'sanitize_textarea_field',
            ],
        ],
    ] );
}

function pmw_rest_post_contact_submit( WP_REST_Request $request ) {
    $name    = $request->get_param( 'name' );
    $email   = $request->get_param( 'email' );
    $subject = $request->get_param( 'subject' );
    $message = $request->get_param( 'message' );

    $name = trim( $name );
    $subject = trim( $subject );
    $message = trim( $message );

    $errors = [];
    if ( strlen( $name ) < 1 ) {
        $errors['name'] = 'Name is required.';
    }
    if ( ! is_email( $email ) ) {
        $errors['email'] = 'Please enter a valid email address.';
    }
    if ( strlen( $subject ) < 1 ) {
        $errors['subject'] = 'Subject is required.';
    }
    if ( strlen( $message ) < 1 ) {
        $errors['message'] = 'Message is required.';
    }
    if ( ! empty( $errors ) ) {
        return new WP_REST_Response( [ 'success' => false, 'message' => 'Validation failed.', 'errors' => $errors ], 400 );
    }

    $post_id = wp_insert_post( [
        'post_type'   => 'form_submission',
        'post_title'  => wp_kses_post( $subject ),
        'post_status' => 'publish',
        'post_author' => 0,
    ], true );

    if ( is_wp_error( $post_id ) ) {
        return new WP_REST_Response( [ 'success' => false, 'message' => 'Could not save submission. Please try again.' ], 500 );
    }

    update_post_meta( $post_id, '_pmw_contact_name', $name );
    update_post_meta( $post_id, '_pmw_contact_email', $email );
    update_post_meta( $post_id, '_pmw_contact_subject', $subject );
    update_post_meta( $post_id, '_pmw_contact_message', $message );
    update_post_meta( $post_id, '_pmw_contact_source', 'contact-form' );
    update_post_meta( $post_id, '_pmw_contact_submitted_at', current_time( 'mysql' ) );

    $admin_email = get_option( 'admin_email' );
    if ( $admin_email ) {
        $mail_subject = '[Precious Market Watch] ' . $subject;
        $mail_body    = "Name: $name\nEmail: $email\nSubject: $subject\n\nMessage:\n$message";
        wp_mail( $admin_email, $mail_subject, $mail_body, [ 'Content-Type: text/plain; charset=UTF-8' ] );
    }

    return new WP_REST_Response( [ 'success' => true, 'message' => 'Your message has been sent. We\'ll be in touch shortly.' ], 200 );
}

// ── Agents API: GET /pmw/v1/agents, GET /pmw/v1/agents/{slug}, upload endpoints ──
function pmw_register_agents_rest_route() {
    register_rest_route( 'pmw/v1', '/agents', [
        'methods'             => 'GET',
        'callback'            => 'pmw_rest_get_agents',
        'permission_callback' => '__return_true',
    ] );
    register_rest_route( 'pmw/v1', '/agents/(?P<slug>[a-z0-9\-]+)', [
        'methods'             => 'GET',
        'callback'            => 'pmw_rest_get_agent_by_slug',
        'permission_callback' => '__return_true',
        'args'                => [ 'slug' => [ 'required' => true, 'type' => 'string' ] ],
    ] );
    register_rest_route( 'pmw/v1', '/agents/(?P<slug>[a-z0-9\-]+)/upload-avatar-image', [
        'methods'             => 'POST',
        'callback'            => 'pmw_rest_upload_agent_avatar_image',
        'permission_callback' => 'pmw_rest_agent_upload_permission',
        'args'                => [ 'slug' => [ 'required' => true, 'type' => 'string' ] ],
    ] );
    register_rest_route( 'pmw/v1', '/agents/(?P<slug>[a-z0-9\-]+)/upload-avatar-video', [
        'methods'             => 'POST',
        'callback'            => 'pmw_rest_upload_agent_avatar_video',
        'permission_callback' => 'pmw_rest_agent_upload_permission',
        'args'                => [ 'slug' => [ 'required' => true, 'type' => 'string' ] ],
    ] );
}

function pmw_rest_agent_upload_permission( $request ) {
    return current_user_can( 'edit_posts' );
}

function pmw_agent_display_order( $post_id ) {
    $v = get_post_meta( $post_id, 'pmw_display_order', true );
    return ( $v !== '' && is_numeric( $v ) ) ? (int) $v : 999;
}

function pmw_build_agent_response( $post ) {
    $id = $post->ID;
    $slug = get_post_meta( $id, 'pmw_slug', true );
    if ( $slug === '' ) {
        $slug = sanitize_title( get_the_title( $post ) );
    }
    $quirks_raw = get_post_meta( $id, 'pmw_quirks', true );
    $specialisms_raw = get_post_meta( $id, 'pmw_specialisms', true );
    $quirks = is_string( $quirks_raw ) ? json_decode( $quirks_raw, true ) : [];
    $specialisms = is_string( $specialisms_raw ) ? json_decode( $specialisms_raw, true ) : [];
    if ( ! is_array( $quirks ) ) $quirks = [];
    if ( ! is_array( $specialisms ) ) $specialisms = [];

    $avatar_img = get_post_meta( $id, 'pmw_avatar_image_url', true );
    $avatar_vid = get_post_meta( $id, 'pmw_avatar_video_url', true );
    if ( $avatar_img === '' ) $avatar_img = null;
    if ( $avatar_vid === '' ) $avatar_vid = null;
    $eta = get_post_meta( $id, 'pmw_eta', true );
    if ( $eta === '' ) $eta = null;

    return [
        'id'                 => (int) $id,
        'slug'               => $slug,
        'display_name'       => (string) ( get_post_meta( $id, 'pmw_display_name', true ) ?: get_the_title( $post ) ),
        'title'              => (string) get_post_meta( $id, 'pmw_title', true ),
        'role'               => (string) get_post_meta( $id, 'pmw_role', true ),
        'tier'               => (string) get_post_meta( $id, 'pmw_tier', true ),
        'model_family'       => (string) get_post_meta( $id, 'pmw_model_family', true ),
        'bio'                => (string) get_post_meta( $id, 'pmw_bio', true ),
        'personality'        => (string) get_post_meta( $id, 'pmw_personality', true ),
        'quirks'             => $quirks,
        'specialisms'        => $specialisms,
        'status'             => (string) ( get_post_meta( $id, 'pmw_status', true ) ?: 'active' ),
        'eta'                => $eta,
        'display_order'      => pmw_agent_display_order( $id ),
        'avatar_image_url'   => $avatar_img,
        'avatar_video_url'   => $avatar_vid,
    ];
}

function pmw_rest_get_agents( WP_REST_Request $request ) {
    $status = $request->get_param( 'status' ) ?: 'active';
    $posts  = get_posts( [
        'post_type'      => 'pmw_agent',
        'post_status'    => 'publish',
        'posts_per_page' => 100,
    ] );

    $agents = [];
    foreach ( $posts as $post ) {
        $agent_status = get_post_meta( $post->ID, 'pmw_status', true ) ?: 'active';
        if ( $status !== 'all' && $agent_status !== $status ) {
            continue;
        }
        $agents[] = pmw_build_agent_response( $post );
    }

    usort( $agents, function ( $a, $b ) {
        return $a['display_order'] - $b['display_order'];
    } );

    $response = new WP_REST_Response( $agents, 200 );
    $response->header( 'Cache-Control', 'public, max-age=300' );
    return $response;
}

function pmw_rest_get_agent_by_slug( WP_REST_Request $request ) {
    $slug = $request->get_param( 'slug' );
    $posts = get_posts( [
        'post_type'      => 'pmw_agent',
        'post_status'    => 'publish',
        'posts_per_page' => 1,
        'meta_key'       => 'pmw_slug',
        'meta_value'     => $slug,
    ] );
    if ( empty( $posts ) ) {
        return new WP_REST_Response( [ 'code' => 'agent_not_found', 'message' => 'No agent found with that slug.' ], 404 );
    }
    $response = new WP_REST_Response( pmw_build_agent_response( $posts[0] ), 200 );
    $response->header( 'Cache-Control', 'public, max-age=300' );
    return $response;
}

function pmw_rest_upload_agent_avatar_image( WP_REST_Request $request ) {
    $slug = $request->get_param( 'slug' );
    $posts = get_posts( [ 'post_type' => 'pmw_agent', 'post_status' => 'publish', 'posts_per_page' => 1, 'meta_key' => 'pmw_slug', 'meta_value' => $slug ] );
    if ( empty( $posts ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'agent_not_found', 'message' => 'No agent found with that slug.' ], 404 );
    }
    $post_id = $posts[0]->ID;

    $files = $request->get_file_params();
    if ( empty( $files['file'] ) || ! is_uploaded_file( $files['file']['tmp_name'] ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'no_file', 'message' => 'No file uploaded.' ], 400 );
    }
    $file = $files['file'];
    $allowed = [ 'image/jpeg', 'image/png', 'image/webp' ];
    if ( ! in_array( $file['type'] ?? '', $allowed, true ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'unsupported_type', 'message' => 'Unsupported file type. Use JPEG, PNG, or WebP.' ], 415 );
    }
    if ( ( $file['size'] ?? 0 ) > 5 * 1024 * 1024 ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'file_too_large', 'message' => 'File exceeds 5MB limit.' ], 413 );
    }

    require_once ABSPATH . 'wp-admin/includes/file.php';
    require_once ABSPATH . 'wp-admin/includes/media.php';
    require_once ABSPATH . 'wp-admin/includes/image.php';

    $overrides = [ 'test_form' => false, 'mimes' => [ 'jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'png' => 'image/png', 'webp' => 'image/webp' ] ];
    $upload = wp_handle_upload( $file, $overrides );
    if ( isset( $upload['error'] ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'upload_failed', 'message' => $upload['error'] ], 500 );
    }
    $attachment = [
        'post_mime_type' => $upload['type'],
        'post_title'     => sanitize_file_name( pathinfo( $file['name'], PATHINFO_FILENAME ) ),
        'post_content'   => '',
        'post_status'    => 'inherit',
    ];
    $attach_id = wp_insert_attachment( $attachment, $upload['file'], $post_id );
    if ( is_wp_error( $attach_id ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'upload_failed', 'message' => $attach_id->get_error_message() ], 500 );
    }
    wp_generate_attachment_metadata( $attach_id, $upload['file'] );
    update_post_meta( $post_id, 'pmw_avatar_image_url', $upload['url'] );

    return new WP_REST_Response( [ 'success' => true, 'avatar_image_url' => $upload['url'], 'attachment_id' => $attach_id ], 200 );
}

function pmw_rest_upload_agent_avatar_video( WP_REST_Request $request ) {
    $slug = $request->get_param( 'slug' );
    $posts = get_posts( [ 'post_type' => 'pmw_agent', 'post_status' => 'publish', 'posts_per_page' => 1, 'meta_key' => 'pmw_slug', 'meta_value' => $slug ] );
    if ( empty( $posts ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'agent_not_found', 'message' => 'No agent found with that slug.' ], 404 );
    }
    $post_id = $posts[0]->ID;

    $files = $request->get_file_params();
    if ( empty( $files['file'] ) || ! is_uploaded_file( $files['file']['tmp_name'] ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'no_file', 'message' => 'No file uploaded.' ], 400 );
    }
    $file = $files['file'];
    if ( ( $file['type'] ?? '' ) !== 'video/mp4' ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'unsupported_type', 'message' => 'Unsupported file type. Use MP4.' ], 415 );
    }
    if ( ( $file['size'] ?? 0 ) > 50 * 1024 * 1024 ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'file_too_large', 'message' => 'File exceeds 50MB limit.' ], 413 );
    }

    require_once ABSPATH . 'wp-admin/includes/file.php';
    require_once ABSPATH . 'wp-admin/includes/media.php';
    require_once ABSPATH . 'wp-admin/includes/image.php';

    $overrides = [ 'test_form' => false, 'mimes' => [ 'mp4' => 'video/mp4' ] ];
    $upload = wp_handle_upload( $file, $overrides );
    if ( isset( $upload['error'] ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'upload_failed', 'message' => $upload['error'] ], 500 );
    }
    $attachment = [
        'post_mime_type' => $upload['type'],
        'post_title'     => sanitize_file_name( pathinfo( $file['name'], PATHINFO_FILENAME ) ),
        'post_content'   => '',
        'post_status'    => 'inherit',
    ];
    $attach_id = wp_insert_attachment( $attachment, $upload['file'], $post_id );
    if ( is_wp_error( $attach_id ) ) {
        return new WP_REST_Response( [ 'success' => false, 'code' => 'upload_failed', 'message' => $attach_id->get_error_message() ], 500 );
    }
    wp_generate_attachment_metadata( $attach_id, $upload['file'] );
    update_post_meta( $post_id, 'pmw_avatar_video_url', $upload['url'] );

    return new WP_REST_Response( [ 'success' => true, 'avatar_video_url' => $upload['url'], 'attachment_id' => $attach_id ], 200 );
}

// ── Site Settings Options Page ───────────────────────
function pmw_register_site_settings_options_page() {
    if ( ! function_exists( 'acf_add_options_page' ) ) return;

    acf_add_options_page( [
        'page_title'  => 'Site Settings',
        'menu_title'  => 'Site Settings',
        'menu_slug'   => 'site-settings',
        'capability'  => 'edit_posts',
        'redirect'    => false,
        'post_id'     => 'site_settings',
    ] );

    if ( ! function_exists( 'acf_add_local_field_group' ) ) return;

    acf_add_local_field_group( [
        'key'    => 'group_site_settings',
        'title'  => 'Site Settings',
        'fields' => [
            [ 'key' => 'field_site_tagline', 'label' => 'Site Tagline', 'name' => 'site_tagline', 'type' => 'text', 'show_in_graphql' => 1, 'graphql_field_name' => 'siteTagline' ],
            [ 'key' => 'field_nav_cta_label', 'label' => 'Nav CTA Label', 'name' => 'nav_cta_label', 'type' => 'text', 'show_in_graphql' => 1, 'graphql_field_name' => 'navCtaLabel' ],
            [ 'key' => 'field_nav_cta_url', 'label' => 'Nav CTA URL', 'name' => 'nav_cta_url', 'type' => 'url', 'show_in_graphql' => 1, 'graphql_field_name' => 'navCtaUrl' ],
            [ 'key' => 'field_footer_about_text', 'label' => 'Footer About Text', 'name' => 'footer_about_text', 'type' => 'textarea', 'rows' => 3, 'show_in_graphql' => 1, 'graphql_field_name' => 'footerAboutText' ],
            [
                'key'        => 'field_footer_columns',
                'label'      => 'Footer Columns',
                'name'       => 'footer_columns',
                'type'       => 'repeater',
                'layout'     => 'block',
                'sub_fields' => [
                    [ 'key' => 'field_fc_label', 'label' => 'Label', 'name' => 'label', 'type' => 'text', 'show_in_graphql' => 1 ],
                    [
                        'key'        => 'field_fc_links',
                        'label'      => 'Links',
                        'name'       => 'links',
                        'type'       => 'repeater',
                        'layout'     => 'table',
                        'sub_fields' => [
                            [ 'key' => 'field_fcl_label', 'label' => 'Label', 'name' => 'label', 'type' => 'text', 'show_in_graphql' => 1 ],
                            [ 'key' => 'field_fcl_url', 'label' => 'URL', 'name' => 'url', 'type' => 'url', 'show_in_graphql' => 1 ],
                        ],
                    ],
                ],
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'footerColumns',
            ],
            [
                'key'        => 'field_social_links',
                'label'      => 'Social Links',
                'name'       => 'social_links',
                'type'       => 'group',
                'sub_fields' => [
                    [ 'key' => 'field_social_twitter', 'label' => 'Twitter/X URL', 'name' => 'twitter_url', 'type' => 'url', 'show_in_graphql' => 1, 'graphql_field_name' => 'twitterUrl' ],
                    [ 'key' => 'field_social_linkedin', 'label' => 'LinkedIn URL', 'name' => 'linkedin_url', 'type' => 'url', 'show_in_graphql' => 1, 'graphql_field_name' => 'linkedinUrl' ],
                    [ 'key' => 'field_social_youtube', 'label' => 'YouTube URL', 'name' => 'youtube_url', 'type' => 'url', 'show_in_graphql' => 1, 'graphql_field_name' => 'youtubeUrl' ],
                ],
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'socialLinks',
            ],
            [ 'key' => 'field_cookie_notice_text', 'label' => 'Cookie Notice Text', 'name' => 'cookie_notice_text', 'type' => 'textarea', 'rows' => 2, 'show_in_graphql' => 1, 'graphql_field_name' => 'cookieNoticeText' ],
            [ 'key' => 'field_analytics_notice', 'label' => 'Show Analytics Disclosure', 'name' => 'analytics_notice', 'type' => 'true_false', 'ui' => 1, 'show_in_graphql' => 1, 'graphql_field_name' => 'analyticsNotice' ],
        ],
        'location' => [
            [ [ 'param' => 'options_page', 'operator' => '==', 'value' => 'site-settings' ] ],
        ],
        'show_in_graphql'    => 1,
        'graphql_field_name' => 'siteSettings',
    ] );
}

// ── METAL-04: Price History API ──────────────────────
function pmw_register_prices_history_route() {
    register_rest_route( 'pmw/v1', '/prices/history', [
        'methods'             => 'GET',
        'callback'            => 'pmw_rest_get_prices_history',
        'permission_callback' => '__return_true',
        'args'                => [
            'metal'    => [
                'required'          => true,
                'enum'              => [ 'gold', 'silver', 'platinum', 'palladium' ],
                'sanitize_callback' => 'sanitize_text_field',
            ],
            'range'    => [
                'default'           => '1Y',
                'enum'              => [ '1M', '3M', '6M', '1Y', '5Y', 'all' ],
                'sanitize_callback' => 'sanitize_text_field',
            ],
            'currency' => [
                'default'           => 'usd',
                'enum'              => [ 'usd', 'gbp' ],
                'sanitize_callback' => 'sanitize_text_field',
            ],
        ],
    ] );
}

function pmw_rest_get_prices_history( WP_REST_Request $request ) {
    $metal    = $request->get_param( 'metal' );
    $range    = $request->get_param( 'range' );
    $currency = $request->get_param( 'currency' );

    // CACHE-05: Transient cache per (metal, range, currency), 1 hour
    $cache_key = 'pmw_prices_history_' . $metal . '_' . $range . '_' . $currency;
    $cached    = get_transient( $cache_key );
    if ( $cached !== false && is_array( $cached ) ) {
        $response = new WP_REST_Response( $cached, 200 );
        $response->header( 'Cache-Control', 'public, max-age=3600, s-maxage=3600, stale-while-revalidate=86400' );
        return $response;
    }

    global $wpdb;
    $table = $wpdb->prefix . 'metal_prices';

    $cutoff_map = [
        '1M'  => gmdate( 'Y-m-d', strtotime( '-1 month' ) ),
        '3M'  => gmdate( 'Y-m-d', strtotime( '-3 months' ) ),
        '6M'  => gmdate( 'Y-m-d', strtotime( '-6 months' ) ),
        '1Y'  => gmdate( 'Y-m-d', strtotime( '-1 year' ) ),
        '5Y'  => gmdate( 'Y-m-d', strtotime( '-5 years' ) ),
        'all' => '1990-01-01',
    ];
    $cutoff = $cutoff_map[ $range ] ?? $cutoff_map['1Y'];

    $sql = $wpdb->prepare(
        "SELECT date, price_usd, price_gbp FROM $table WHERE metal = %s AND date >= %s ORDER BY date ASC",
        $metal,
        $cutoff
    );
    $rows = $wpdb->get_results( $sql, ARRAY_A );
    $usd_to_gbp = 0.79;

    $data = [];
    foreach ( $rows as $row ) {
        $usd = isset( $row['price_usd'] ) && $row['price_usd'] > 0 ? (float) $row['price_usd'] : null;
        if ( $usd === null ) continue;
        $p = $currency === 'gbp'
            ? ( ( isset( $row['price_gbp'] ) && $row['price_gbp'] > 0 ) ? (float) $row['price_gbp'] : $usd * $usd_to_gbp )
            : $usd;
        $data[] = [ 'date' => $row['date'], 'price' => round( $p, 4 ) ];
    }

    $payload = [
        'metal'    => $metal,
        'currency' => $currency,
        'range'    => $range,
        'data'     => $data,
    ];
    set_transient( $cache_key, $payload, HOUR_IN_SECONDS );

    $response = new WP_REST_Response( $payload, 200 );
    // CACHE-04: Historical data rarely changes
    $response->header( 'Cache-Control', 'public, max-age=3600, s-maxage=3600, stale-while-revalidate=86400' );
    return $response;
}

// ── Latest price per metal (for metal page heroes) ──────────────────────
function pmw_register_prices_latest_route() {
    register_rest_route( 'pmw/v1', '/prices/latest', [
        'methods'             => 'GET',
        'callback'            => 'pmw_rest_get_prices_latest',
        'permission_callback' => '__return_true',
    ] );
}

function pmw_rest_get_prices_latest( WP_REST_Request $request ) {
    global $wpdb;
    $table = $wpdb->prefix . 'metal_prices';
    $metals = [ 'gold', 'silver', 'platinum', 'palladium' ];
    $result = [];

    foreach ( $metals as $metal ) {
        $row = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT date, price_usd, price_gbp FROM $table WHERE metal = %s ORDER BY date DESC LIMIT 1",
                $metal
            ),
            ARRAY_A
        );
        if ( $row ) {
            $result[ $metal ] = [
                'date'      => $row['date'],
                'price_usd' => isset( $row['price_usd'] ) ? (float) $row['price_usd'] : null,
                'price_gbp' => isset( $row['price_gbp'] ) && $row['price_gbp'] > 0 ? (float) $row['price_gbp'] : null,
            ];
        } else {
            $result[ $metal ] = null;
        }
    }

    $response = new WP_REST_Response( $result, 200 );
    $response->header( 'Cache-Control', 'public, max-age=300, s-maxage=300, stale-while-revalidate=3600' );
    return $response;
}

// ── Metal prices ticker: latest + previous for daily change (MarketOverview, header) ──
function pmw_register_prices_ticker_route() {
    register_rest_route( 'pmw/v1', '/prices/ticker', [
        'methods'             => 'GET',
        'callback'            => 'pmw_rest_get_prices_ticker',
        'permission_callback' => '__return_true',
    ] );
}

function pmw_rest_get_prices_ticker( WP_REST_Request $request ) {
    global $wpdb;
    $table = $wpdb->prefix . 'metal_prices';
    $metals = [ 'gold', 'silver', 'platinum', 'palladium' ];
    $symbol_map = [ 'gold' => 'XAU', 'silver' => 'XAG', 'platinum' => 'XPT', 'palladium' => 'XPD' ];
    $result = [];

    foreach ( $metals as $metal ) {
        $rows = $wpdb->get_results(
            $wpdb->prepare(
                "SELECT date, price_usd, price_gbp FROM $table WHERE metal = %s ORDER BY date DESC LIMIT 2",
                $metal
            ),
            ARRAY_A
        );
        $latest = isset( $rows[0] ) ? (float) $rows[0]['price_usd'] : null;
        $previous = isset( $rows[1] ) ? (float) $rows[1]['price_usd'] : null;
        $change = null;
        $change_percent = null;
        $is_up = true;
        if ( $latest !== null && $previous !== null && $previous > 0 ) {
            $change = round( $latest - $previous, 4 );
            $change_percent = round( ( $latest - $previous ) / $previous * 100, 2 );
            $is_up = $change >= 0;
        }
        $result[] = [
            'metal'          => $metal,
            'name'           => ucfirst( $metal ),
            'symbol'         => $symbol_map[ $metal ] ?? strtoupper( $metal ),
            'price'          => $latest !== null ? round( $latest, 4 ) : 0,
            'change'         => $change !== null ? $change : 0,
            'change_percent' => $change_percent !== null ? $change_percent : 0,
            'isUp'           => $is_up,
            'high'           => $latest !== null && $previous !== null ? max( $latest, $previous ) : ( $latest ?? 0 ),
            'low'            => $latest !== null && $previous !== null ? min( $latest, $previous ) : ( $previous ?? $latest ?? 0 ),
            'date'           => isset( $rows[0]['date'] ) ? $rows[0]['date'] : null,
        ];
    }

    $response = new WP_REST_Response( $result, 200 );
    $response->header( 'Cache-Control', 'public, max-age=300, s-maxage=300, stale-while-revalidate=3600' );
    return $response;
}

// ── GraphQL: metalPricesTicker (same data as /prices/ticker) ──
function pmw_register_metal_prices_graphql() {
    if ( ! function_exists( 'register_graphql_object_type' ) || ! function_exists( 'register_graphql_field' ) ) {
        return;
    }
    register_graphql_object_type( 'MetalTicker', [
        'description' => __( 'Metal price ticker with latest price and daily change', 'pmw-core' ),
        'fields'      => [
            'metal'          => [ 'type' => 'String' ],
            'name'           => [ 'type' => 'String' ],
            'symbol'         => [ 'type' => 'String' ],
            'price'          => [ 'type' => 'Float' ],
            'change'         => [ 'type' => 'Float' ],
            'changePercent'  => [ 'type' => 'Float' ],
            'isUp'           => [ 'type' => 'Boolean' ],
            'high'           => [ 'type' => 'Float' ],
            'low'            => [ 'type' => 'Float' ],
            'date'           => [ 'type' => 'String' ],
        ],
    ] );
    register_graphql_field( 'RootQuery', 'metalPricesTicker', [
        'type'        => [ 'list_of' => 'MetalTicker' ],
        'description' => __( 'Latest metal prices with daily change (from metal_prices seed)', 'pmw-core' ),
        'resolve'     => function () {
            $req  = new WP_REST_Request( 'GET' );
            $resp = pmw_rest_get_prices_ticker( $req );
            $data = $resp->get_data();
            if ( ! is_array( $data ) ) {
                return [];
            }
            return array_map( function ( $row ) {
                return [
                    'metal'         => $row['metal'] ?? '',
                    'name'          => $row['name'] ?? '',
                    'symbol'        => $row['symbol'] ?? '',
                    'price'         => (float) ( $row['price'] ?? 0 ),
                    'change'        => (float) ( $row['change'] ?? 0 ),
                    'changePercent' => (float) ( $row['change_percent'] ?? 0 ),
                    'isUp'          => ! empty( $row['isUp'] ),
                    'high'          => (float) ( $row['high'] ?? 0 ),
                    'low'           => (float) ( $row['low'] ?? 0 ),
                    'date'          => $row['date'] ?? null,
                ];
            }, $data );
        },
    ] );
}

// ── GraphQL: agents field on TeamGrid section (populates team data in page response) ──
function pmw_register_team_grid_agents_graphql() {
    if ( ! function_exists( 'register_graphql_object_type' ) || ! function_exists( 'register_graphql_field' ) ) {
        return;
    }
    register_graphql_object_type( 'PmwAgentProfile', [
        'description' => __( 'Agent profile for Team section', 'pmw-core' ),
        'fields'      => [
            'id'                  => [ 'type' => 'Int' ],
            'slug'                => [ 'type' => 'String' ],
            'displayName'          => [ 'type' => 'String' ],
            'title'               => [ 'type' => 'String' ],
            'role'                => [ 'type' => 'String' ],
            'tier'                => [ 'type' => 'String' ],
            'modelFamily'         => [ 'type' => 'String' ],
            'bio'                 => [ 'type' => 'String' ],
            'personality'         => [ 'type' => 'String' ],
            'quirks'              => [ 'type' => [ 'list_of' => 'String' ] ],
            'specialisms'         => [ 'type' => [ 'list_of' => 'String' ] ],
            'status'              => [ 'type' => 'String' ],
            'eta'                 => [ 'type' => 'String' ],
            'displayOrder'        => [ 'type' => 'Int' ],
            'avatarImageUrl'      => [ 'type' => 'String' ],
            'avatarVideoUrl'      => [ 'type' => 'String' ],
        ],
    ] );

    $type_names = [
        'Page_Pagesections_PageSections_TeamGrid',
        'Page_PageSections_PageSections_TeamGrid',
    ];
    foreach ( $type_names as $type_name ) {
        register_graphql_field( $type_name, 'agents', [
            'type'        => [ 'list_of' => 'PmwAgentProfile' ],
            'description' => __( 'Team agents to display in the grid', 'pmw-core' ),
            'resolve'     => function () {
                $posts = get_posts( [
                    'post_type'      => 'pmw_agent',
                    'post_status'    => 'publish',
                    'posts_per_page' => 100,
                ] );
                $agents = [];
                foreach ( $posts as $post ) {
                    $agents[] = pmw_graphql_agent_profile( $post );
                }
                usort( $agents, function ( $a, $b ) {
                    return ( $a['displayOrder'] ?? 999 ) - ( $b['displayOrder'] ?? 999 );
                } );
                return $agents;
            },
        ] );
    }
}

function pmw_graphql_agent_profile( $post ) {
    $id   = $post->ID;
    $slug = get_post_meta( $id, 'pmw_slug', true );
    if ( $slug === '' ) {
        $slug = sanitize_title( get_the_title( $post ) );
    }
    $quirks_raw     = get_post_meta( $id, 'pmw_quirks', true );
    $specialisms_raw = get_post_meta( $id, 'pmw_specialisms', true );
    $quirks         = is_string( $quirks_raw ) ? json_decode( $quirks_raw, true ) : [];
    $specialisms    = is_string( $specialisms_raw ) ? json_decode( $specialisms_raw, true ) : [];
    if ( ! is_array( $quirks ) ) $quirks = [];
    if ( ! is_array( $specialisms ) ) $specialisms = [];

    $avatar_img = get_post_meta( $id, 'pmw_avatar_image_url', true );
    $avatar_vid = get_post_meta( $id, 'pmw_avatar_video_url', true );
    if ( $avatar_img === '' ) $avatar_img = null;
    if ( $avatar_vid === '' ) $avatar_vid = null;
    $eta = get_post_meta( $id, 'pmw_eta', true );
    if ( $eta === '' ) $eta = null;

    return [
        'id'                => (int) $id,
        'slug'              => $slug,
        'displayName'       => (string) ( get_post_meta( $id, 'pmw_display_name', true ) ?: get_the_title( $post ) ),
        'title'             => (string) get_post_meta( $id, 'pmw_title', true ),
        'role'              => (string) get_post_meta( $id, 'pmw_role', true ),
        'tier'              => (string) get_post_meta( $id, 'pmw_tier', true ),
        'modelFamily'       => (string) get_post_meta( $id, 'pmw_model_family', true ),
        'bio'               => (string) get_post_meta( $id, 'pmw_bio', true ),
        'personality'       => (string) get_post_meta( $id, 'pmw_personality', true ),
        'quirks'            => $quirks,
        'specialisms'       => $specialisms,
        'status'            => (string) ( get_post_meta( $id, 'pmw_status', true ) ?: 'active' ),
        'eta'               => $eta,
        'displayOrder'      => (int) ( get_post_meta( $id, 'pmw_display_order', true ) ?: 999 ),
        'avatarImageUrl'    => $avatar_img,
        'avatarVideoUrl'    => $avatar_vid,
    ];
}

// ── METAL-05: Market Data ACF Options Page ───────────
function pmw_register_market_data_options_page() {
    if ( ! function_exists( 'acf_add_options_page' ) ) return;

    acf_add_options_page( [
        'page_title' => 'Market Data',
        'menu_title' => 'Market Data',
        'menu_slug'  => 'market_data',
        'capability' => 'edit_posts',
        'redirect'   => false,
        'post_id'    => 'market_data',
    ] );

    if ( ! function_exists( 'acf_add_local_field_group' ) ) return;

    $metals = [ 'gold', 'silver', 'platinum', 'palladium' ];
    $fields = [];
    foreach ( $metals as $m ) {
        $fields[] = [
            'key'   => 'field_market_' . $m . '_usd',
            'label' => ucfirst( $m ) . ' Price (USD)',
            'name'  => $m . '_price_usd',
            'type'  => 'number',
            'step'  => 0.0001,
            'readonly' => 1,
        ];
        $fields[] = [
            'key'   => 'field_market_' . $m . '_gbp',
            'label' => ucfirst( $m ) . ' Price (GBP)',
            'name'  => $m . '_price_gbp',
            'type'  => 'number',
            'step'  => 0.0001,
            'readonly' => 1,
        ];
        $fields[] = [
            'key'   => 'field_market_' . $m . '_change',
            'label' => ucfirst( $m ) . ' 24h Change (%)',
            'name'  => $m . '_change_24h',
            'type'  => 'number',
            'step'  => 0.01,
            'readonly' => 1,
        ];
    }
    $fields[] = [
        'key'   => 'field_market_last_updated',
        'label' => 'Last Updated',
        'name'  => 'last_updated',
        'type'  => 'text',
        'readonly' => 1,
    ];

    acf_add_local_field_group( [
        'key'    => 'group_market_data',
        'title'  => 'Market Data',
        'fields' => $fields,
        'location' => [
            [ [ 'param' => 'options_page', 'operator' => '==', 'value' => 'market_data' ] ],
        ],
    ] );
}

function pmw_register_gems_rest_route() {
    register_rest_route( 'pmw/v1', '/gems', [
        'methods'             => 'GET',
        'callback'            => 'pmw_rest_get_gems',
        'permission_callback' => '__return_true',
    ] );
}

function pmw_rest_get_gems() {
    $cache_key   = 'pmw_gems_index';
    $cache_ttl   = DAY_IN_SECONDS; // 24 hours
    $stale_key   = 'pmw_gems_index_stale';
    $stale_ttl   = 7 * DAY_IN_SECONDS;

    $fresh = get_transient( $cache_key );
    if ( $fresh !== false ) {
        return pmw_gems_response( $fresh, false );
    }

    $posts = get_posts( [
        'post_type'      => 'gem_index',
        'post_status'    => 'publish',
        'posts_per_page' => 100,
        'orderby'        => 'title',
        'order'          => 'ASC',
    ] );

    $gems = [];
    foreach ( $posts as $post ) {
        $data = pmw_build_gem_price( $post );
        if ( $data && (float) ( $data['priceLowUsd'] ?? 0 ) > 0 ) {
            $gems[] = $data;
        }
    }

    if ( ! empty( $gems ) ) {
        set_transient( $cache_key, $gems, $cache_ttl );
        set_transient( $stale_key, $gems, $stale_ttl );
        return pmw_gems_response( $gems, false );
    }

    $stale = get_transient( $stale_key );
    if ( $stale !== false ) {
        return pmw_gems_response( $stale, true );
    }

    return pmw_gems_response( [], false );
}

function pmw_build_gem_price( WP_Post $post ) {
    if ( ! function_exists( 'get_field' ) ) {
        return null;
    }

    $cat_map = [
        'precious'      => 'Precious',
        'semi-precious' => 'Semi-Precious',
        'organic'       => 'Organic',
    ];
    $trend_map = [
        'rising'   => 'Rising',
        'stable'   => 'Stable',
        'declining' => 'Declining',
    ];
    $grade_map = [
        'commercial' => 'Commercial',
        'good'       => 'Good',
        'fine'       => 'Fine',
        'extra_fine' => 'Extra Fine',
    ];

    $price_low_usd  = (float) get_field( 'price_low_usd', $post->ID );
    $price_high_usd = (float) get_field( 'price_high_usd', $post->ID );
    $price_low_gbp  = (float) get_field( 'price_low_gbp', $post->ID );
    $price_high_gbp = (float) get_field( 'price_high_gbp', $post->ID );

    $gem_cat = get_field( 'gem_category', $post->ID );
    $market  = get_field( 'market_trend', $post->ID );

    return [
        'id'             => (string) $post->ID,
        'name'           => get_the_title( $post ),
        'category'       => $cat_map[ $gem_cat ] ?? 'Semi-Precious',
        'priceLowUsd'    => $price_low_usd,
        'priceHighUsd'   => $price_high_usd,
        'priceLowGbp'    => $price_low_gbp,
        'priceHighGbp'   => $price_high_gbp,
        'qualityGrade'   => $grade_map[ get_field( 'quality_grade', $post->ID ) ] ?? '',
        'caratRange'     => (string) ( get_field( 'carat_range', $post->ID ) ?: '' ),
        'trend'          => $trend_map[ $market ] ?? 'Stable',
        'trendPercentage' => (float) ( get_field( 'trend_percentage', $post->ID ) ?: 0 ),
        'lastReviewed'   => (string) ( get_field( 'last_reviewed', $post->ID ) ?: '' ),
        'dataSource'     => (string) ( get_field( 'data_source', $post->ID ) ?: '' ),
    ];
}

function pmw_gems_response( array $gems, bool $stale ) {
    $response = new WP_REST_Response( [
        'gems'  => $gems,
        'stale' => $stale,
    ], 200 );
    // CACHE-04: Gem data changes quarterly
    $response->header( 'Cache-Control', 'public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800' );
    return $response;
}

// ── CACHE-05: Invalidate gems transient when a gem_index post is saved ──
add_action( 'save_post_gem_index', 'pmw_invalidate_gems_cache' );
function pmw_invalidate_gems_cache() {
    delete_transient( 'pmw_gems_index' );
    delete_transient( 'pmw_gems_index_stale' );
}

// Invalidate price history transients (call from cron/seed when metal_prices is updated)
function pmw_invalidate_prices_history_cache() {
    $metals   = [ 'gold', 'silver', 'platinum', 'palladium' ];
    $ranges   = [ '1M', '3M', '6M', '1Y', '5Y', 'all' ];
    $currencies = [ 'usd', 'gbp' ];
    foreach ( $metals as $m ) {
        foreach ( $ranges as $r ) {
            foreach ( $currencies as $c ) {
                delete_transient( 'pmw_prices_history_' . $m . '_' . $r . '_' . $c );
            }
        }
    }
}

// ─────────────────────────────────────────────
// 6. DASHBOARD WIDGET — GEM INDEX OVERDUE REVIEW (GEM-05)
// ─────────────────────────────────────────────

add_action( 'wp_dashboard_setup', 'pmw_register_gem_index_dashboard_widget' );

function pmw_register_gem_index_dashboard_widget() {
    if ( ! current_user_can( 'edit_posts' ) ) {
        return;
    }
    wp_add_dashboard_widget(
        'pmw_gem_index_overdue',
        'Gem Index — Overdue for Review',
        'pmw_render_gem_index_overdue_widget'
    );
}

function pmw_render_gem_index_overdue_widget() {
    if ( ! post_type_exists( 'gem_index' ) ) {
        echo '<p>Gem Index post type is not registered.</p>';
        return;
    }

    $posts = get_posts( [
        'post_type'   => 'gem_index',
        'post_status' => 'publish',
        'numberposts' => 100,
        'orderby'     => 'title',
        'order'       => 'ASC',
    ] );

    $cutoff = gmdate( 'Y-m-d', strtotime( '-90 days' ) );
    $overdue = [];

    foreach ( $posts as $post ) {
        $last_reviewed = function_exists( 'get_field' ) ? get_field( 'last_reviewed', $post->ID ) : null;
        if ( empty( $last_reviewed ) || $last_reviewed < $cutoff ) {
            $overdue[] = $post;
        }
    }

    if ( empty( $overdue ) ) {
        echo '<p>All gem index entries have been reviewed within the last 90 days.</p>';
        return;
    }

    echo '<ul style="list-style: none; margin: 0; padding: 0;">';
    foreach ( $overdue as $post ) {
        $last = function_exists( 'get_field' ) ? get_field( 'last_reviewed', $post->ID ) : '';
        $label = $last ? esc_html( $last ) : 'Never reviewed';
        $edit_url = get_edit_post_link( $post->ID, 'raw' );
        echo '<li style="margin-bottom: 8px; padding: 8px 12px; background: #fef3c7; border-left: 4px solid #d97706; border-radius: 2px;">';
        echo '<a href="' . esc_url( $edit_url ) . '" style="font-weight: 600; text-decoration: none;">' . esc_html( get_the_title( $post ) ) . '</a>';
        echo ' <span style="color: #92400e; font-size: 12px;">— Last reviewed: ' . esc_html( $label ) . '</span>';
        echo '</li>';
    }
    echo '</ul>';
}



