"""
WordpressClient — WPGraphQL client for headless WordPress.

Replaces the REST API client. Uses the WPGraphQL plugin endpoint
at /graphql (default) for all reads and mutations.

Owns:
  - GraphQL query/mutation execution via httpx
  - Authentication (Application Password → Basic Auth header)
  - Response parsing and error handling
  - High-level helpers matching the operations topic_service and page_service need

Does NOT own:
  - Business logic (services own that)
  - HTTP connection pooling (uses its own httpx.AsyncClient)

Requires WPGraphQL plugin installed on WordPress:
  https://www.wpgraphql.com/

For custom post types (pmw_topic), also requires:
  - WPGraphQL registered in your CPT: 'show_in_graphql' => true
  - register_graphql_field() for each pmw_ meta field

Usage:
    client = WordpressClient(
        base_url="https://www.preciousmarketwatch.com/wp",
        username="pmw_admin",
        password="xxxx xxxx xxxx xxxx",
    )
    topics = await client.query_topics(status="PUBLISH")
    await client.update_topic_meta(topic_id=101, meta={...})
    await client.close()
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger("pmw.infra.wordpress")


# ── Exceptions ─────────────────────────────────────────────────────────────


class WordpressError(Exception):
    """Base exception for all WordPress client errors."""


class WordpressAuthError(WordpressError):
    """Authentication failed — bad credentials or revoked application password."""


class WordpressNotFoundError(WordpressError):
    """Requested resource does not exist in WordPress."""


class WordpressGraphQLError(WordpressError):
    """GraphQL query returned errors."""

    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []


# ── Client ─────────────────────────────────────────────────────────────────


class WordpressClient:
    """
    WPGraphQL client for headless WordPress.

    All reads and writes go through the /graphql endpoint.
    Authentication uses HTTP Basic Auth with WP Application Passwords.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        graphql_path: str = "/graphql",
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.graphql_url = f"{self.base_url}{graphql_path}"
        self.auth = (username, password)
        self.client = httpx.AsyncClient(
            auth=self.auth,
            timeout=httpx.Timeout(timeout, connect=timeout, read=timeout, write=timeout),
            follow_redirects=True,
            headers={
                "User-Agent": "PMW-Agents/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        """Close the underlying httpx session."""
        await self.client.aclose()
        logger.info("WordpressClient closed")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    # ── Core GraphQL executor ──────────────────────────────────────────────

    async def execute(
        self,
        query: str,
        variables: dict | None = None,
        operation_name: str | None = None,
    ) -> dict:
        """
        Execute a GraphQL query or mutation against WPGraphQL.

        Args:
            query: GraphQL query/mutation string.
            variables: Optional variables dict.
            operation_name: Optional operation name (for multi-operation documents).

        Returns:
            The 'data' dict from the GraphQL response.

        Raises:
            WordpressAuthError: 401/403 from WP.
            WordpressGraphQLError: GraphQL-level errors returned in the response body.
            WordpressError: Network or unexpected errors.
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        try:
            response = await self.client.post(self.graphql_url, json=payload)
        except httpx.TimeoutException as exc:
            raise WordpressError(f"GraphQL request timeout: {exc}") from exc
        except Exception as exc:
            raise WordpressError(f"GraphQL request failed: {exc}") from exc

        # HTTP-level auth errors
        if response.status_code in (401, 403):
            raise WordpressAuthError(
                f"WordPress authentication failed (HTTP {response.status_code}). "
                "Check WP_APP_USERNAME and WP_APP_PASSWORD."
            )
        if response.status_code >= 400:
            raise WordpressError(
                f"WordPress returned HTTP {response.status_code}: {response.text[:300]}"
            )

        # Parse JSON
        try:
            body = response.json()
        except Exception:
            raise WordpressError(f"Invalid JSON response from WordPress: {response.text[:300]}")

        # GraphQL-level errors
        if "errors" in body and body["errors"]:
            messages = [e.get("message", str(e)) for e in body["errors"]]
            raise WordpressGraphQLError(
                f"GraphQL errors: {'; '.join(messages)}",
                errors=body["errors"],
            )

        return body.get("data", {})

    # ══════════════════════════════════════════════════════════════════════
    # HIGH-LEVEL HELPERS — these replace the REST get_all / _request calls
    # that topic_service.py and page_service.py were using.
    # ══════════════════════════════════════════════════════════════════════

    # ── Topics (pmw_topic CPT) ─────────────────────────────────────────────

    async def query_topics(
        self,
        status: str = "PUBLISH",
        first: int = 100,
    ) -> list[dict]:
        """
        Fetch published pmw_topic posts with all meta fields.

        Requires WPGraphQL registration of the pmw_topic CPT with:
          'show_in_graphql' => true,
          'graphql_single_name' => 'pmwTopic',
          'graphql_plural_name' => 'pmwTopics',

        And register_graphql_field() for each pmw_ meta field.

        Returns:
            List of topic dicts matching the old REST API shape.
        """
        query = """
        query GetTopics($status: PostStatusEnum, $first: Int) {
            pmwTopics(
                where: { status: $status }
                first: $first
            ) {
                nodes {
                    databaseId
                    title
                    status
                    pmwTargetKeyword
                    pmwSummary
                    pmwIncludeKeywords
                    pmwExcludeKeywords
                    pmwAssetClass
                    pmwProductType
                    pmwGeography
                    pmwIsBuySide
                    pmwIntentStage
                    pmwPriority
                    pmwScheduleCron
                    pmwAgentStatus
                    pmwLastRunAt
                    pmwRunCount
                    pmwLastRunId
                    pmwLastWpPostId
                    pmwWpCategoryId
                    pmwAffiliatePageId
                }
            }
        }
        """
        data = await self.execute(query, variables={
            "status": status,
            "first": first,
        })

        nodes = (data.get("pmwTopics") or {}).get("nodes", [])

        # Normalise to the same shape topic_service expects
        topics = []
        for node in nodes:
            topics.append({
                "id": node.get("databaseId"),
                "title": {"rendered": node.get("title", "")},
                "meta": {
                    "pmw_target_keyword": node.get("pmwTargetKeyword", ""),
                    "pmw_summary": node.get("pmwSummary", ""),
                    "pmw_include_keywords": node.get("pmwIncludeKeywords", ""),
                    "pmw_exclude_keywords": node.get("pmwExcludeKeywords", ""),
                    "pmw_asset_class": node.get("pmwAssetClass", ""),
                    "pmw_product_type": node.get("pmwProductType", ""),
                    "pmw_geography": node.get("pmwGeography", "uk"),
                    "pmw_is_buy_side": node.get("pmwIsBuySide", False),
                    "pmw_intent_stage": node.get("pmwIntentStage", "consideration"),
                    "pmw_priority": node.get("pmwPriority", 5),
                    "pmw_schedule_cron": node.get("pmwScheduleCron", ""),
                    "pmw_agent_status": node.get("pmwAgentStatus", "idle"),
                    "pmw_last_run_at": node.get("pmwLastRunAt", ""),
                    "pmw_run_count": node.get("pmwRunCount", 0),
                    "pmw_last_run_id": node.get("pmwLastRunId", 0),
                    "pmw_last_wp_post_id": node.get("pmwLastWpPostId", 0),
                    "pmw_wp_category_id": node.get("pmwWpCategoryId", 0),
                    "pmw_affiliate_page_id": node.get("pmwAffiliatePageId", 0),
                },
            })

        logger.info(f"GraphQL: fetched {len(topics)} topics (status={status})")
        return topics

    async def get_topic_meta(self, topic_id: int) -> dict:
        """
        Fetch a single topic's meta fields by database ID.
        Returns the meta dict, or empty dict if not found.
        """
        query = """
        query GetTopic($id: ID!) {
            pmwTopic(id: $id, idType: DATABASE_ID) {
                databaseId
                pmwAgentStatus
                pmwRunCount
                pmwLastRunAt
                pmwLastRunId
                pmwLastWpPostId
            }
        }
        """
        data = await self.execute(query, variables={"id": topic_id})
        node = data.get("pmwTopic")
        if not node:
            return {}
        return {
            "pmw_agent_status": node.get("pmwAgentStatus", "idle"),
            "pmw_run_count": node.get("pmwRunCount", 0),
            "pmw_last_run_at": node.get("pmwLastRunAt", ""),
            "pmw_last_run_id": node.get("pmwLastRunId", 0),
            "pmw_last_wp_post_id": node.get("pmwLastWpPostId", 0),
        }

    async def update_topic_meta(self, topic_id: int, meta: dict) -> bool:
        """
        Update meta fields on a pmw_topic post via GraphQL mutation.

        Requires a custom mutation registered via register_graphql_mutation()
        or uses the WPGraphQL built-in updatePmwTopic mutation.

        Args:
            topic_id: WordPress database ID of the pmw_topic post.
            meta: Dict of meta fields to update. Keys use pmw_ prefix format
                  (e.g. "pmw_agent_status") — they're converted to camelCase
                  for the GraphQL mutation.

        Returns:
            True if mutation succeeded.
        """
        # Convert pmw_snake_case to pmwCamelCase for GraphQL
        gql_meta = {}
        for key, value in meta.items():
            camel = self._snake_to_camel(key)
            gql_meta[camel] = value

        # Build dynamic mutation input fields
        input_fields = ", ".join(f"{k}: {json.dumps(v)}" for k, v in gql_meta.items())

        mutation = f"""
        mutation UpdateTopicMeta {{
            updatePmwTopic(
                input: {{
                    id: "{topic_id}"
                    {input_fields}
                }}
            ) {{
                pmwTopic {{
                    databaseId
                }}
            }}
        }}
        """

        try:
            data = await self.execute(mutation)
            updated_id = (
                (data.get("updatePmwTopic") or {})
                .get("pmwTopic", {})
                .get("databaseId")
            )
            if updated_id:
                logger.debug(f"Topic {topic_id} meta updated: {list(meta.keys())}")
                return True
            return False
        except WordpressGraphQLError as exc:
            logger.warning(
                f"Topic meta update failed for {topic_id}: {exc}",
                extra={"errors": exc.errors},
            )
            return False

    # ── Pages ──────────────────────────────────────────────────────────────

    async def find_page_by_slug(self, slug: str) -> dict | None:
        """
        Find a WP page by slug. Returns {id, title, slug} or None.
        """
        query = """
        query FindPage($slug: String!) {
            pageBy(uri: $slug) {
                databaseId
                title
                slug
                status
            }
        }
        """
        # WPGraphQL pageBy uses URI — try slug directly
        # Fallback: query pages and filter
        try:
            data = await self.execute(query, variables={"slug": slug})
            page = data.get("pageBy")
            if page:
                return {
                    "id": page.get("databaseId"),
                    "title": page.get("title", ""),
                    "slug": page.get("slug", ""),
                }
        except WordpressGraphQLError:
            pass

        # Fallback: search pages by slug using where filter
        fallback_query = """
        query FindPageBySlug($slug: String!) {
            pages(where: { name: $slug }, first: 1) {
                nodes {
                    databaseId
                    title
                    slug
                }
            }
        }
        """
        data = await self.execute(fallback_query, variables={"slug": slug})
        nodes = (data.get("pages") or {}).get("nodes", [])
        if nodes:
            return {
                "id": nodes[0].get("databaseId"),
                "title": nodes[0].get("title", ""),
                "slug": nodes[0].get("slug", ""),
            }
        return None

    async def create_page(
        self,
        title: str,
        slug: str,
        status: str = "PUBLISH",
        content: str = "",
        meta: dict | None = None,
    ) -> int | None:
        """
        Create a new WordPress page via GraphQL mutation.

        Returns the new page's database ID, or None on failure.
        """
        # Build meta input if provided
        meta_input = ""
        if meta:
            # Meta stored as JSON string in a custom field
            meta_json = json.dumps(meta).replace('"', '\\"')
            meta_input = f', pmwIntelligenceData: "{meta_json}"'

        mutation = f"""
        mutation CreatePage {{
            createPage(
                input: {{
                    title: {json.dumps(title)}
                    slug: {json.dumps(slug)}
                    status: {status}
                    content: {json.dumps(content)}
                    {meta_input}
                }}
            ) {{
                page {{
                    databaseId
                    slug
                }}
            }}
        }}
        """
        try:
            data = await self.execute(mutation)
            page = (data.get("createPage") or {}).get("page", {})
            page_id = page.get("databaseId")
            if page_id:
                logger.info(f"Created page: slug={slug} id={page_id}")
            return page_id
        except WordpressGraphQLError as exc:
            logger.error(f"Page creation failed: {exc}", extra={"slug": slug})
            return None

    async def update_page(
        self,
        page_id: int,
        title: str | None = None,
        content: str | None = None,
        status: str | None = None,
        meta: dict | None = None,
    ) -> bool:
        """
        Update an existing WordPress page via GraphQL mutation.

        Returns True on success.
        """
        fields = []
        if title is not None:
            fields.append(f'title: {json.dumps(title)}')
        if content is not None:
            fields.append(f'content: {json.dumps(content)}')
        if status is not None:
            fields.append(f'status: {status}')
        if meta:
            meta_json = json.dumps(meta).replace('"', '\\"')
            fields.append(f'pmwIntelligenceData: "{meta_json}"')

        if not fields:
            return True  # Nothing to update

        fields_str = ", ".join(fields)
        mutation = f"""
        mutation UpdatePage {{
            updatePage(
                input: {{
                    id: "{page_id}"
                    {fields_str}
                }}
            ) {{
                page {{
                    databaseId
                }}
            }}
        }}
        """
        try:
            data = await self.execute(mutation)
            updated = (data.get("updatePage") or {}).get("page", {})
            if updated.get("databaseId"):
                logger.debug(f"Page {page_id} updated")
                return True
            return False
        except WordpressGraphQLError as exc:
            logger.warning(f"Page update failed for {page_id}: {exc}")
            return False

    # ── Posts (for internal link lookups) ──────────────────────────────────

    async def search_posts(
        self,
        search: str,
        first: int = 5,
    ) -> list[dict]:
        """
        Search published posts by keyword. Used for internal link discovery.
        Returns list of {id, title, slug, url, excerpt}.
        """
        query = """
        query SearchPosts($search: String!, $first: Int) {
            posts(
                where: { search: $search, status: PUBLISH }
                first: $first
            ) {
                nodes {
                    databaseId
                    title
                    slug
                    uri
                    excerpt
                }
            }
        }
        """
        data = await self.execute(query, variables={"search": search, "first": first})
        nodes = (data.get("posts") or {}).get("nodes", [])
        return [
            {
                "id": n.get("databaseId"),
                "title": n.get("title", ""),
                "slug": n.get("slug", ""),
                "url": n.get("uri", ""),
                "excerpt": n.get("excerpt", ""),
            }
            for n in nodes
        ]

    # ══════════════════════════════════════════════════════════════════════
    # COMPATIBILITY LAYER — thin wrappers so existing service code
    # continues to work during migration. These can be removed once
    # all services use the high-level helpers directly.
    # ══════════════════════════════════════════════════════════════════════

    async def get_all(
        self,
        endpoint: str,
        params: dict | None = None,
        per_page: int = 100,
    ) -> list[dict]:
        """
        Compatibility wrapper replacing the old REST get_all().

        Routes to the appropriate GraphQL query based on the endpoint path.
        Services should migrate to the high-level helpers directly.
        """
        params = params or {}

        # Route: /pmw-topics → query_topics
        if "pmw-topics" in endpoint and "/" not in endpoint.strip("/").replace("pmw-topics", ""):
            status = params.get("status", "publish").upper()
            return await self.query_topics(status=status, first=per_page)

        # Route: /pmw-topics/{id} → get single topic meta
        if "pmw-topics/" in endpoint:
            topic_id = int(endpoint.rstrip("/").split("/")[-1])
            meta = await self.get_topic_meta(topic_id)
            return [{"id": topic_id, "meta": meta}] if meta else []

        # Route: /pages with slug filter → find_page_by_slug
        if "pages" in endpoint and params.get("slug"):
            page = await self.find_page_by_slug(params["slug"])
            return [page] if page else []

        # Route: /posts with search → search_posts
        if "posts" in endpoint and params.get("search"):
            return await self.search_posts(
                search=params["search"],
                first=params.get("per_page", per_page),
            )

        logger.warning(f"Unmapped get_all endpoint: {endpoint} — returning empty")
        return []

    # ── Utility ────────────────────────────────────────────────────────────

    @staticmethod
    def _snake_to_camel(snake_str: str) -> str:
        """
        Convert pmw_snake_case to pmwCamelCase.
        e.g. "pmw_agent_status" → "pmwAgentStatus"
              "pmw_last_run_at" → "pmwLastRunAt"
        """
        parts = snake_str.split("_")
        # First part stays lowercase, rest are capitalised
        return parts[0] + "".join(p.capitalize() for p in parts[1:])