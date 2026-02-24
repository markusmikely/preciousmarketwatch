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

function pmw_register_post_types() {

    // ── Market Insight ──────────────────────
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
        // WPGraphQL
        'show_in_graphql'     => true,
        'graphql_single_name' => 'marketInsight',
        'graphql_plural_name' => 'marketInsights',
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


// ─────────────────────────────────────────────
// 2. CUSTOM TAXONOMIES
// ─────────────────────────────────────────────

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
}


// ─────────────────────────────────────────────
// 3. SEED DEFAULT TERMS (runs once on activation)
// ─────────────────────────────────────────────

register_activation_hook( __FILE__, 'pmw_seed_terms' );

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
}


// ─────────────────────────────────────────────
// 5. GEM INDEX REST API (GEM-03)
// ─────────────────────────────────────────────

add_action( 'rest_api_init', 'pmw_register_gems_rest_route' );
add_action( 'rest_api_init', 'pmw_register_prices_history_route' );
add_action( 'rest_api_init', 'pmw_register_prices_latest_route' );
add_action( 'rest_api_init', 'pmw_register_subscribe_route' );
add_action( 'rest_api_init', 'pmw_register_contact_submit_route' );
add_action( 'acf/init', 'pmw_register_market_data_options_page' );

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



