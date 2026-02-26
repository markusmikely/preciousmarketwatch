#!/bin/bash

# Clear and recreate pmw-agents directory structure
echo "Clearing pmw-agents directory..."

# Remove existing directory
rm -rf pmw-agents

# Create directory structure
mkdir -p pmw-agents/bridge/routers
mkdir -p pmw-agents/bridge/ws
mkdir -p pmw-agents/bridge/services
mkdir -p pmw-agents/bridge/models

mkdir -p pmw-agents/agents/nodes
mkdir -p pmw-agents/agents/tools
mkdir -p pmw-agents/agents/scoring
mkdir -p pmw-agents/agents/state
mkdir -p pmw-agents/agents/db/migrations

mkdir -p pmw-agents/dashboard/src/{store,components,pages}

mkdir -p pmw-agents/db/migrations

mkdir -p pmw-agents/.github/workflows

# Create all empty files
touch pmw-agents/bridge/Dockerfile
touch pmw-agents/bridge/requirements.txt
touch pmw-agents/bridge/main.py

touch pmw-agents/bridge/routers/workflows.py
touch pmw-agents/bridge/routers/topics.py
touch pmw-agents/bridge/routers/agents.py
touch pmw-agents/bridge/routers/auth.py
touch pmw-agents/bridge/routers/performance.py
touch pmw-agents/bridge/routers/social.py

touch pmw-agents/bridge/ws/manager.py

touch pmw-agents/bridge/services/wp_client.py
touch pmw-agents/bridge/services/redis_client.py

touch pmw-agents/bridge/models/schemas.py

touch pmw-agents/agents/Dockerfile
touch pmw-agents/agents/requirements.txt
touch pmw-agents/agents/main.py
touch pmw-agents/agents/orchestrator.py

touch pmw-agents/agents/nodes/task_loader.py
touch pmw-agents/agents/nodes/research.py
touch pmw-agents/agents/nodes/planning.py
touch pmw-agents/agents/nodes/content.py
touch pmw-agents/agents/nodes/media.py
touch pmw-agents/agents/nodes/publishing.py
touch pmw-agents/agents/nodes/social.py
touch pmw-agents/agents/nodes/performance_intel.py
touch pmw-agents/agents/nodes/judge.py

touch pmw-agents/agents/tools/metal_prices.py
touch pmw-agents/agents/tools/news_search.py
touch pmw-agents/agents/tools/serp_search.py
touch pmw-agents/agents/tools/wp_search.py
touch pmw-agents/agents/tools/image_gen.py
touch pmw-agents/agents/tools/ga4.py
touch pmw-agents/agents/tools/clarity.py
touch pmw-agents/agents/tools/search_console.py
touch pmw-agents/agents/tools/social_platforms.py

touch pmw-agents/agents/scoring/base.py
touch pmw-agents/agents/scoring/research_scorer.py
touch pmw-agents/agents/scoring/planning_scorer.py
touch pmw-agents/agents/scoring/content_scorer.py
touch pmw-agents/agents/scoring/social_scorer.py

touch pmw-agents/agents/state/types.py

touch pmw-agents/agents/db/connection.py
touch pmw-agents/agents/db/queries.py

touch pmw-agents/dashboard/src/App.tsx
touch pmw-agents/dashboard/src/store/index.ts

# Note: components and pages directories are kept empty for now
# They'll be populated later with actual files

touch pmw-agents/db/migrations/001_initial.sql
touch pmw-agents/db/migrations/002_social.sql
touch pmw-agents/db/migrations/003_performance.sql
touch pmw-agents/db/migrations/004_media.sql

touch pmw-agents/.env.example
touch pmw-agents/docker-compose.yml

echo "✅ pmw-agents directory structure created successfully!"
echo "Total files created: $(find pmw-agents -type f | wc -l)"
