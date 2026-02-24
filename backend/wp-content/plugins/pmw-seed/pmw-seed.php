<?php
/**
 * Plugin Name: PMW Seed Data
 * Description: Seeds all initial content for Precious Market Watch (articles, dealers, pages, categories).
 *              This plugin should be run once, then can be deactivated. Run again anytime to refresh.
 * Version:     2.0.0
 * Author:      Markus Mikely
 */

if ( ! defined( 'ABSPATH' ) ) exit;

// Load dealer reviews
require_once( __DIR__ . '/dealer-reviews.php' );

register_activation_hook( __FILE__, 'pmw_seed_all' );
add_action( 'admin_init', 'pmw_maybe_show_seed_notice' );

/**
 * Show admin notice after activation
 */
function pmw_maybe_show_seed_notice() {
    if ( get_option( 'pmw_seed_just_activated' ) ) {
        delete_option( 'pmw_seed_just_activated' );
        add_action( 'admin_notices', function() {
            echo '<div class="notice notice-success is-dismissible"><p>';
            echo '<strong>PMW Seed Data:</strong> Content has been seeded. Articles, dealers, and pages are now available in the CMS. ';
            echo 'You can deactivate this plugin.';
            echo '</p></div>';
        });
    }
}

/**
 * Main seed function - runs on plugin activation
 */
function pmw_seed_all() {
    pmw_seed_homepage();
    pmw_seed_categories();
    pmw_seed_articles();
    pmw_seed_dealers();
    pmw_seed_gem_index();
    pmw_seed_category_pages();
    
    // Mark that we just seeded
    update_option( 'pmw_seed_just_activated', true );
}

// ─────────────────────────────────────────────────────────────
// HOMEPAGE
// ─────────────────────────────────────────────────────────────

function pmw_seed_homepage() {
    // Find or create the homepage page
    $homepage = get_posts( [
        'post_type'   => 'page',
        'title'       => 'Home',
        'post_status' => 'publish',
        'numberposts' => 1,
    ] );

    if ( empty( $homepage ) ) {
        $page_id = wp_insert_post( [
            'post_title'   => 'Home',
            'post_type'    => 'page',
            'post_status'  => 'publish',
            'post_content' => 'Welcome to Precious Market Watch - Your trusted source for precious metals and gemstone information.',
        ] );
    } else {
        $page_id = $homepage[0]->ID;
    }

    // Set as front page
    update_option( 'show_on_front', 'page' );
    update_option( 'page_on_front', $page_id );

    // Seed ACF homepage hero fields if ACF exists
    if ( function_exists( 'update_field' ) ) {
        update_field( 'hero', [
            'title'            => 'Trusted Insights for Precious Metals & Gemstones',
            'subtitle'         => 'Your authoritative source for gold, silver, platinum, diamonds, and fine gemstones. Expert analysis, market data, and investment guidance.',
            'background_image' => null,
        ], $page_id );

        update_field( 'newsletter', [
            'email' => '',
        ], $page_id );
    }
}

// ─────────────────────────────────────────────────────────────
// CATEGORIES
// ─────────────────────────────────────────────────────────────

function pmw_seed_categories() {
    $categories = [
        'precious-metals' => 'Precious Metals',
        'gemstones'       => 'Gemstones',
        'gold'            => 'Gold',
        'silver'          => 'Silver',
        'platinum'        => 'Platinum',
        'palladium'       => 'Palladium',
        'diamonds'        => 'Diamonds',
        'rubies'          => 'Rubies',
        'sapphires'       => 'Sapphires',
        'emeralds'        => 'Emeralds',
        'market-analysis' => 'Market Analysis',
        'investment'      => 'Investment',
    ];

    foreach ( $categories as $slug => $name ) {
        $term = term_exists( $name, 'category' );
        if ( ! $term ) {
            wp_insert_term( $name, 'category', [ 'slug' => $slug ] );
        }
    }
}

// ─────────────────────────────────────────────────────────────
// SAMPLE ARTICLES
// ─────────────────────────────────────────────────────────────

function pmw_seed_articles() {
    $articles = [
        // Precious Metals Articles
        [
            'title'       => 'Gold Reaches New Highs as Inflation Concerns Persist',
            'excerpt'     => 'Central bank policies continue to drive investor interest in gold as a hedge against currency devaluation and economic uncertainty.',
            'content'     => '<p>Gold prices have surged to record levels as persistent inflation and geopolitical uncertainty drive investors toward safe-haven assets. Gold is now trading above $2,600 per ounce, marking a significant milestone for investors.</p><p>Central banks around the world have been accumulating gold at record rates. China, Russia, and several emerging market central banks have been particularly active buyers, seeking to diversify their reserves away from the US dollar.</p><p>With inflation remaining elevated in many developed economies, investors are turning to gold as a traditional store of value. Gold\'s historical performance during inflationary periods supports its role as an effective hedge.</p>',
            'categories'  => [ 'precious-metals', 'gold', 'market-analysis' ],
            'author'      => 'Editor',
            'featured'    => true,
        ],
        [
            'title'       => 'Silver Industrial Demand Surges on Green Energy Push',
            'excerpt'     => 'Solar panel production and electric vehicle manufacturing drive unprecedented demand for silver in industrial applications.',
            'content'     => '<p>Silver demand in the industrial sector is reaching unprecedented levels as the green energy transition accelerates. Solar panel manufacturers and EV producers are consuming silver at record rates.</p><p>Unlike gold, which is primarily used for jewelry and investment, silver has significant industrial applications. Solar cells use silver as a conductor, and electric vehicles require silver components in battery technology.</p><p>This dual demand—investment interest plus industrial consumption—makes silver a compelling investment opportunity in 2024 and beyond.</p>',
            'categories'  => [ 'precious-metals', 'silver', 'market-analysis' ],
            'author'      => 'Editor',
            'featured'    => false,
        ],
        [
            'title'       => 'Platinum Supply Deficit: Investment Opportunity?',
            'excerpt'     => 'Mining disruptions in South Africa create supply deficit, potentially supporting platinum prices through 2025.',
            'content'     => '<p>Mining disruptions in South Africa, which produces about 75% of the world\'s platinum, have created a significant supply deficit. This supply squeeze is expected to continue through 2025.</p><p>Platinum is less well-known than gold and silver but has significant industrial applications in catalytic converters, electronics, and chemical processing.</p><p>The combination of supply constraints and industrial demand recovery post-pandemic suggests platinum could see significant appreciation.</p>',
            'categories'  => [ 'precious-metals', 'platinum', 'investment' ],
            'author'      => 'Editor',
            'featured'    => false,
        ],
        // Gemstones Articles
        [
            'title'       => 'Lab-Grown vs Natural Diamonds: Market Impact',
            'excerpt'     => 'How lab-grown diamonds are reshaping the natural diamond market dynamics and investor valuations.',
            'content'     => '<p>The diamond market has undergone a significant transformation with the rise of lab-grown diamonds. Lab-grown diamonds are chemically, physically, and optically identical to natural diamonds but cost 70-80% less.</p><p>For investment purposes, natural diamonds have historically held value better than lab-grown alternatives. The resale market for lab-grown diamonds is still developing, and their rapid price decline has made them less suitable as investment vehicles.</p><p>Natural diamonds, particularly rare colors and exceptional quality stones, continue to appreciate over time and maintain strong auction results.</p>',
            'categories'  => [ 'gemstones', 'diamonds', 'market-analysis' ],
            'author'      => 'Editor',
            'featured'    => true,
        ],
        [
            'title'       => 'Kashmir Sapphires: Record Auction Results',
            'excerpt'     => 'Recent auction sales highlight continued demand for rare Kashmir origin stones.',
            'content'     => '<p>Kashmir sapphires continue to command premium prices at major auction houses. Their unique characteristics—vivid blue color combined with a silky texture—make them among the most sought-after gemstones.</p><p>A 15-carat Kashmir sapphire recently sold for over $1 million per carat at auction, demonstrating the continued strength of the fine gemstone market.</p><p>Investment-grade Kashmir sapphires remain scarce, as mining in the region has been limited for decades.</p>',
            'categories'  => [ 'gemstones', 'sapphires', 'investment' ],
            'author'      => 'Editor',
            'featured'    => false,
        ],
        [
            'title'       => 'Colored Gemstone Investment Trends 2024',
            'excerpt'     => 'Which colored stones are gaining investor attention this year and why.',
            'content'     => '<p>While diamonds dominate media coverage, colored gemstones—particularly rubies, sapphires, and emeralds—have emerged as compelling alternative investments.</p><p>Fine-quality colored gemstones have outperformed traditional investments over the past decade, with some stones appreciating 10-15% annually.</p><p>The key to gemstone investment is quality: color, clarity, and provenance. Investment-grade stones from known origins command significant premiums.</p>',
            'categories'  => [ 'gemstones', 'investment', 'market-analysis' ],
            'author'      => 'Editor',
            'featured'    => false,
        ],
    ];

    foreach ( $articles as $article ) {
        // Check if article already exists
        $existing = get_posts( [
            'post_type'   => 'post',
            'title'       => $article['title'],
            'post_status' => 'publish',
            'numberposts' => 1,
        ] );

        if ( ! empty( $existing ) ) {
            continue;
        }

        // Create the post
        $post_id = wp_insert_post( [
            'post_title'   => $article['title'],
            'post_content' => $article['content'],
            'post_excerpt' => $article['excerpt'],
            'post_type'    => 'post',
            'post_status'  => 'publish',
            'post_author'  => get_current_user_id() ?: 1,
        ] );

        if ( is_wp_error( $post_id ) ) {
            continue;
        }

        // Set categories
        wp_set_post_categories( $post_id, get_term_ids_by_slugs( $article['categories'] ) );

        // Add ACF fields if available
        if ( function_exists( 'update_field' ) ) {
            update_field( 'read_time', '5 min read', $post_id );
        }
    }
}

// ─────────────────────────────────────────────────────────────
// DEALERS
// ─────────────────────────────────────────────────────────────

function pmw_seed_dealers() {
    $dealers = [
        [
            'name'           => 'APMEX',
            'description'    => 'One of the largest online precious metals dealers in the US, offering an extensive selection of gold, silver, platinum, and palladium products.',
            'short_desc'     => 'Leading online precious metals dealer with competitive pricing and fast shipping.',
            'rating'         => 4.8,
            'featured'       => true,
            'metals'         => [ 'Gold', 'Silver', 'Platinum', 'Palladium' ],
            'gemstones'      => [],
        ],
        [
            'name'           => 'JM Bullion',
            'description'    => 'Trusted dealer offering competitive prices on precious metals with fast, secure shipping and excellent customer service.',
            'short_desc'     => 'Competitive pricing on bullion with low premiums and reliable service.',
            'rating'         => 4.7,
            'featured'       => true,
            'metals'         => [ 'Gold', 'Silver', 'Platinum' ],
            'gemstones'      => [],
        ],
        [
            'name'           => 'Blue Nile',
            'description'    => 'Leading online diamond and fine jewelry retailer with exceptional selection and competitive pricing.',
            'short_desc'     => 'Premium diamond retailer with GIA certification and 360-degree imaging.',
            'rating'         => 4.5,
            'featured'       => true,
            'metals'         => [],
            'gemstones'      => [ 'Diamonds', 'Gemstones' ],
        ],
        [
            'name'           => 'James Allen',
            'description'    => 'Premium diamond retailer famous for 360° viewing technology and high average order values.',
            'short_desc'     => 'Innovative diamond marketplace with advanced viewing technology.',
            'rating'         => 4.6,
            'featured'       => false,
            'metals'         => [],
            'gemstones'      => [ 'Diamonds' ],
        ],
        [
            'name'           => 'SD Bullion',
            'description'    => 'Known for industry-low premiums and transparent pricing on gold and silver bullion products.',
            'short_desc'     => 'Lowest premiums on bullion with free shipping on large orders.',
            'rating'         => 4.4,
            'featured'       => false,
            'metals'         => [ 'Gold', 'Silver' ],
            'gemstones'      => [],
        ],
        [
            'name'           => 'Augusta Precious Metals',
            'description'    => 'Specialist in gold and silver IRAs with comprehensive investment guidance.',
            'short_desc'     => 'Gold and silver IRA specialist with expert guidance.',
            'rating'         => 4.7,
            'featured'       => false,
            'metals'         => [ 'Gold', 'Silver' ],
            'gemstones'      => [],
        ],
    ];

    foreach ( $dealers as $dealer ) {
        // Check if dealer already exists
        $existing = get_posts( [
            'post_type'   => 'dealer',
            'title'       => $dealer['name'],
            'post_status' => 'publish',
            'numberposts' => 1,
        ] );

        if ( ! empty( $existing ) ) {
            continue;
        }

        // Create dealer post
        $post_id = wp_insert_post( [
            'post_title'   => $dealer['name'],
            'post_content' => $dealer['description'],
            'post_excerpt' => $dealer['short_desc'],
            'post_type'    => 'dealer',
            'post_status'  => 'publish',
        ] );

        if ( is_wp_error( $post_id ) ) {
            continue;
        }

        // Add ACF fields if available
        if ( function_exists( 'update_field' ) ) {
            update_field( 'short_description', $dealer['short_desc'], $post_id );
            update_field( 'rating', $dealer['rating'], $post_id );
            update_field( 'featured', $dealer['featured'], $post_id );
            update_field( 'review_link', '', $post_id );
            update_field( 'affiliate_link', '#', $post_id );
        }

        // Set metal types
        if ( ! empty( $dealer['metals'] ) ) {
            wp_set_object_terms( $post_id, $dealer['metals'], 'pmw-metal-type' );
        }

        // Set gemstone types
        if ( ! empty( $dealer['gemstones'] ) ) {
            wp_set_object_terms( $post_id, $dealer['gemstones'], 'pmw-gemstone-type' );
        }
    }
}

// ─────────────────────────────────────────────────────────────
// GEM INDEX
// ─────────────────────────────────────────────────────────────

function pmw_seed_gem_index() {
    if ( ! post_type_exists( 'gem_index' ) ) {
        return;
    }

    $today      = gmdate( 'Y-m-d' );
    $data_source = 'PMW Editorial Research — Initial Seed';

    $gems = [
        [
            'title'               => 'Ruby',
            'gem_type'            => 'Ruby',
            'gem_category'        => 'precious',
            'price_low_usd'       => 800,
            'price_high_usd'      => 15000,
            'price_low_gbp'       => 632,
            'price_high_gbp'      => 11850,
            'quality_grade'       => 'fine',
            'carat_range'         => '1–3ct',
            'producing_countries' => 'Myanmar, Thailand, Mozambique, Madagascar',
            'market_trend'        => 'rising',
            'trend_percentage'    => 3.5,
            'reviewer_notes'      => 'Pigeon-blood Burmese commands premium. Treated stones at lower end.',
        ],
        [
            'title'               => 'Blue Sapphire',
            'gem_type'            => 'Blue Sapphire',
            'gem_category'        => 'precious',
            'price_low_usd'       => 500,
            'price_high_usd'      => 8000,
            'price_low_gbp'       => 395,
            'price_high_gbp'      => 6320,
            'quality_grade'       => 'fine',
            'carat_range'         => '1–5ct',
            'producing_countries' => 'Sri Lanka, Madagascar, Kashmir',
            'market_trend'        => 'stable',
            'trend_percentage'    => 0,
            'reviewer_notes'      => 'Kashmir and Ceylon premium. Madagascar commercial-grade abundant.',
        ],
        [
            'title'               => 'Emerald',
            'gem_type'            => 'Emerald',
            'gem_category'        => 'precious',
            'price_low_usd'       => 500,
            'price_high_usd'      => 6000,
            'price_low_gbp'       => 395,
            'price_high_gbp'      => 4740,
            'quality_grade'       => 'fine',
            'carat_range'         => '1–3ct',
            'producing_countries' => 'Colombia, Zambia, Brazil, Afghanistan',
            'market_trend'        => 'rising',
            'trend_percentage'    => 2.8,
            'reviewer_notes'      => 'Colombian origin premium. Oiled stones standard; no-oil commands top prices.',
        ],
        [
            'title'               => 'Diamond',
            'gem_type'            => 'Diamond',
            'gem_category'        => 'precious',
            'price_low_usd'       => 2500,
            'price_high_usd'      => 20000,
            'price_low_gbp'       => 1975,
            'price_high_gbp'      => 15800,
            'quality_grade'       => 'fine',
            'carat_range'         => '1–3ct',
            'producing_countries' => 'Botswana, Russia, Canada, Australia',
            'market_trend'        => 'stable',
            'trend_percentage'    => 0,
            'reviewer_notes'      => 'Natural mined only. Lab-grown excluded from index. G color VS2 reference.',
        ],
        [
            'title'               => 'Alexandrite',
            'gem_type'            => 'Alexandrite',
            'gem_category'        => 'precious',
            'price_low_usd'       => 8000,
            'price_high_usd'      => 50000,
            'price_low_gbp'       => 6320,
            'price_high_gbp'      => 39500,
            'quality_grade'       => 'extra_fine',
            'carat_range'         => '0.5–2ct',
            'producing_countries' => 'Russia, Brazil, Sri Lanka',
            'market_trend'        => 'rising',
            'trend_percentage'    => 5.0,
            'reviewer_notes'      => 'Natural only. Lab-grown excluded. Russian origin premium.',
        ],
        [
            'title'               => 'Tanzanite',
            'gem_type'            => 'Tanzanite',
            'gem_category'        => 'semi-precious',
            'price_low_usd'       => 300,
            'price_high_usd'      => 1200,
            'price_low_gbp'       => 237,
            'price_high_gbp'      => 948,
            'quality_grade'       => 'fine',
            'carat_range'         => '1–5ct',
            'producing_countries' => 'Tanzania',
            'market_trend'        => 'stable',
            'trend_percentage'    => 0,
            'reviewer_notes'      => 'Single-source stone. AAA grade at high end.',
        ],
        [
            'title'               => 'Amethyst',
            'gem_type'            => 'Amethyst',
            'gem_category'        => 'semi-precious',
            'price_low_usd'       => 15,
            'price_high_usd'      => 100,
            'price_low_gbp'       => 12,
            'price_high_gbp'      => 79,
            'quality_grade'       => 'good',
            'carat_range'         => '5–15ct',
            'producing_countries' => 'Brazil, Uruguay, Zambia',
            'market_trend'        => 'stable',
            'trend_percentage'    => 0,
            'reviewer_notes'      => 'Siberian deep purple premium. Commercial grades abundant.',
        ],
        [
            'title'               => 'Aquamarine',
            'gem_type'            => 'Aquamarine',
            'gem_category'        => 'semi-precious',
            'price_low_usd'       => 150,
            'price_high_usd'      => 800,
            'price_low_gbp'       => 119,
            'price_high_gbp'      => 632,
            'quality_grade'       => 'fine',
            'carat_range'         => '1–10ct',
            'producing_countries' => 'Brazil, Pakistan, Mozambique',
            'market_trend'        => 'rising',
            'trend_percentage'    => 2.0,
            'reviewer_notes'      => 'Santa Maria color premium. Large clean stones available.',
        ],
        [
            'title'               => 'Opal',
            'gem_type'            => 'Opal',
            'gem_category'        => 'semi-precious',
            'price_low_usd'       => 75,
            'price_high_usd'      => 600,
            'price_low_gbp'       => 59,
            'price_high_gbp'      => 474,
            'quality_grade'       => 'good',
            'carat_range'         => '1–5ct',
            'producing_countries' => 'Australia, Ethiopia, Mexico',
            'market_trend'        => 'stable',
            'trend_percentage'    => 0,
            'reviewer_notes'      => 'Black opal top tier. Ethiopian hydrophane excluded for stability.',
        ],
        [
            'title'               => 'Pearl',
            'gem_type'            => 'Pearl',
            'gem_category'        => 'organic',
            'price_low_usd'       => 80,
            'price_high_usd'      => 1500,
            'price_low_gbp'       => 63,
            'price_high_gbp'      => 1185,
            'quality_grade'       => 'good',
            'carat_range'         => '3–10mm',
            'producing_countries' => 'Japan, China, French Polynesia, Australia',
            'market_trend'        => 'stable',
            'trend_percentage'    => 0,
            'reviewer_notes'      => 'Per-carat equivalent. South Sea and Tahitian at high end.',
        ],
        [
            'title'               => 'Garnet',
            'gem_type'            => 'Garnet',
            'gem_category'        => 'semi-precious',
            'price_low_usd'       => 50,
            'price_high_usd'      => 400,
            'price_low_gbp'       => 40,
            'price_high_gbp'      => 316,
            'quality_grade'       => 'good',
            'carat_range'         => '1–5ct',
            'producing_countries' => 'Mozambique, Madagascar, India',
            'market_trend'        => 'stable',
            'trend_percentage'    => 0,
            'reviewer_notes'      => 'Rhodolite, tsavorite, demantoid premium. Almandine commercial.',
        ],
        [
            'title'               => 'Tourmaline',
            'gem_type'            => 'Tourmaline',
            'gem_category'        => 'semi-precious',
            'price_low_usd'       => 100,
            'price_high_usd'      => 1500,
            'price_low_gbp'       => 79,
            'price_high_gbp'      => 1185,
            'quality_grade'       => 'fine',
            'carat_range'         => '1–5ct',
            'producing_countries' => 'Brazil, Mozambique, Nigeria',
            'market_trend'        => 'rising',
            'trend_percentage'    => 3.0,
            'reviewer_notes'      => 'Paraíba commands premium. Watermelon and bi-color popular.',
        ],
    ];

    foreach ( $gems as $gem ) {
        $existing = get_posts( [
            'post_type'   => 'gem_index',
            'title'       => $gem['title'],
            'post_status' => 'any',
            'numberposts' => 1,
        ] );

        if ( ! empty( $existing ) ) {
            continue;
        }

        $post_id = wp_insert_post( [
            'post_title'   => $gem['title'],
            'post_content' => '',
            'post_type'    => 'gem_index',
            'post_status'  => 'publish',
            'post_author'  => get_current_user_id() ?: 1,
        ] );

        if ( is_wp_error( $post_id ) ) {
            continue;
        }

        if ( function_exists( 'update_field' ) ) {
            update_field( 'gem_type', $gem['gem_type'], $post_id );
            update_field( 'gem_category', $gem['gem_category'], $post_id );
            update_field( 'price_low_usd', $gem['price_low_usd'], $post_id );
            update_field( 'price_high_usd', $gem['price_high_usd'], $post_id );
            update_field( 'price_low_gbp', $gem['price_low_gbp'], $post_id );
            update_field( 'price_high_gbp', $gem['price_high_gbp'], $post_id );
            update_field( 'quality_grade', $gem['quality_grade'], $post_id );
            update_field( 'carat_range', $gem['carat_range'], $post_id );
            update_field( 'producing_countries', $gem['producing_countries'], $post_id );
            update_field( 'market_trend', $gem['market_trend'], $post_id );
            update_field( 'trend_percentage', $gem['trend_percentage'], $post_id );
            update_field( 'last_reviewed', $today, $post_id );
            update_field( 'reviewer_notes', $gem['reviewer_notes'], $post_id );
            update_field( 'data_source', $data_source, $post_id );
        }
    }
}

// ─────────────────────────────────────────────────────────────
// CATEGORY & MAIN PAGES
// ─────────────────────────────────────────────────────────────

function pmw_seed_category_pages() {
    $pages = [
        // Main category pages
        [
            'title' => 'Precious Metals',
            'slug'  => 'precious-metals',
            'content' => 'Comprehensive guide to precious metals investment.',
        ],
        [
            'title' => 'Gemstones',
            'slug'  => 'gemstones',
            'content' => 'Expert insights on gemstone investment and valuation.',
        ],
        // Individual metal pages
        [
            'title' => 'Gold',
            'slug'  => 'precious-metals/gold',
            'content' => 'Complete guide to gold investment and market analysis.',
        ],
        [
            'title' => 'Silver',
            'slug'  => 'precious-metals/silver',
            'content' => 'Silver investment strategies and industrial demand analysis.',
        ],
        [
            'title' => 'Platinum',
            'slug'  => 'precious-metals/platinum',
            'content' => 'Platinum market analysis and investment opportunities.',
        ],
        [
            'title' => 'Palladium',
            'slug'  => 'precious-metals/palladium',
            'content' => 'Palladium supply and demand insights.',
        ],
        // Individual gemstone pages
        [
            'title' => 'Diamonds',
            'slug'  => 'gemstones/diamonds',
            'content' => 'Diamond grading, valuation, and investment guide.',
        ],
        [
            'title' => 'Rubies',
            'slug'  => 'gemstones/rubies',
            'content' => 'Ruby quality factors and investment potential.',
        ],
        [
            'title' => 'Sapphires',
            'slug'  => 'gemstones/sapphires',
            'content' => 'Sapphire origins, colors, and investment value.',
        ],
        [
            'title' => 'Emeralds',
            'slug'  => 'gemstones/emeralds',
            'content' => 'Emerald quality assessment and investment guide.',
        ],
        // Main content pages
        [
            'title' => 'Market Insights',
            'slug'  => 'market-insights',
            'content' => 'Latest market analysis and investment trends.',
        ],
        [
            'title' => 'Top Dealers',
            'slug'  => 'top-dealers',
            'content' => 'Vetted precious metals and gemstone dealers.',
        ],
        [
            'title' => 'About',
            'slug'  => 'about',
            'content' => 'Learn about Precious Market Watch and our mission.',
        ],
        [
            'title' => 'Contact',
            'slug'  => 'contact',
            'content' => 'Get in touch with the Precious Market Watch team.',
        ],
        // Legal/Info pages
        [
            'title' => 'Editorial Standards',
            'slug'  => 'editorial-standards',
            'content' => 'Our commitment to accuracy, transparency, and ethical journalism.',
        ],
        [
            'title' => 'Affiliate Disclosure',
            'slug'  => 'affiliate-disclosure',
            'content' => 'How we earn commissions and our affiliate partnerships.',
        ],
        [
            'title' => 'Privacy Policy',
            'slug'  => 'privacy',
            'content' => 'Our privacy policy and data protection commitments.',
        ],
        [
            'title' => 'Terms of Service',
            'slug'  => 'terms',
            'content' => 'Terms of service and user agreement.',
        ],
        [
            'title' => 'Cookies Policy',
            'slug'  => 'cookies',
            'content' => 'Information about how we use cookies.',
        ],
        [
            'title' => 'Jewelry Investment',
            'slug'  => 'jewelry-investment',
            'content' => 'Guide to investing in fine jewelry.',
        ],
    ];

    foreach ( $pages as $page ) {
        $existing = get_posts( [
            'post_type'   => 'page',
            'title'       => $page['title'],
            'post_status' => 'publish',
            'numberposts' => 1,
        ] );

        if ( empty( $existing ) ) {
            wp_insert_post( [
                'post_title'   => $page['title'],
                'post_name'    => $page['slug'],
                'post_content' => $page['content'],
                'post_type'    => 'page',
                'post_status'  => 'publish',
            ] );
        }
    }
}

// ─────────────────────────────────────────────────────────────
// HELPER FUNCTION: Get term IDs by slugs
// ─────────────────────────────────────────────────────────────

function get_term_ids_by_slugs( $slugs ) {
    $term_ids = [];
    foreach ( $slugs as $slug ) {
        $term = get_term_by( 'slug', $slug, 'category' );
        if ( $term ) {
            $term_ids[] = $term->term_id;
        }
    }
    return $term_ids;
}
