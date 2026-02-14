<?php
/**
 * Plugin Name: Precious Market Watch - Custom Post Types
 */

add_action('init', function () {

    $post_types = [
        'precious-metal' => [
            'label' => 'Precious Metals',
            'single' => 'PreciousMetal',
            'plural' => 'PreciousMetals',
        ],
        'gemstone' => [
            'label' => 'Gemstones',
            'single' => 'Gemstone',
            'plural' => 'Gemstones',
        ],
        'investment' => [
            'label' => 'Investments',
            'single' => 'Investment',
            'plural' => 'Investments',
        ],
        'market-insight' => [
            'label' => 'Market Insights',
            'single' => 'MarketInsight',
            'plural' => 'MarketInsights',
        ],
        'dealer' => [
            'label' => 'Dealers',
            'single' => 'Dealer',
            'plural' => 'Dealers',
        ],
    ];

    foreach ($post_types as $slug => $config) {
        register_post_type($slug, [
            'label' => $config['label'],
            'public' => true,
            'has_archive' => true,
            'rewrite' => ['slug' => $slug],
            'supports' => ['title', 'editor', 'excerpt', 'thumbnail'],
            'show_in_rest' => true,

            // GraphQL
            'show_in_graphql' => true,
            'graphql_single_name' => $config['single'],
            'graphql_plural_name' => $config['plural'],
        ]);
    }
});
