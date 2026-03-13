# app/infrastructure/wordpress_client.py
from ssl import Options
import httpx
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urljoin, urlencode
import asyncio 
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings 

logger = logging.getLogger(__name__)

 
# ── Exceptions ─────────────────────────────────────────────────────────────
 
 
class WordpressError(Exception):
    """Base exception for all WordPress client errors."""
 
 
class WordpressAuthError(WordpressError):
    """401 — bad credentials or application password revoked."""
 
 
class WordpressNotFoundError(WordpressError):
    """404 — post, page, or resource does not exist."""
 
 
class WordpressConflictError(WordpressError):
    """409 — e.g. duplicate slug on post creation."""
 
class WordpressClient:
    """Wordpress REST API client with authentication and pagination handling."""

    def __init__(
        self,
        base_url: str,
        username: str, 
        password: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")
        self.api_url = urljoin(self.base_url, "/wp-json/wp/v2")
        self.auth = (username, password)
        self.max_retries = max_retries
        # Create client sesssion
        self.client = httpx.AsyncClient(
            auth=self.auth,
            timeout=httpx.Timeout(timeout, connect=timeout, read=timeout, write=timeout),
            follow_redirects=True,
            headers={
                'User-Agent': 'PMW/1.0',
                'Accept': 'application/json',
            }
        )
    
    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Async context manager exit."""
        await self.close()

    def _build_url(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build a URL with optional query parameters."""
        url = urljoin(self.api_url, endpoint.lstrip("/"))
        if params:
            # Filter out None values
            filtered_params = {k: v for k, v in params.items() if v is not None}
            if filtered_params:
                url = f"{url}?{urlencode(filtered_params)}"
        return url

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make a request to the WordPress API, with error handling."""
        url = self._build_url(endpoint, params)

        try:
            response = await self.client.request(
                method=method,
                url=url,
                data=data,
                json=json,
                headers=headers,
            )

            # Handle Wordpress-specific errors
            if response.status_code >= 400:
                await self._handle_error_response(response)

            return response
        
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout for {method} {url}: {str(e)}")
            raise WordpressError(f"Request timeout: {str(e)}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {method} {url}: {str(e)}")
            raise WordpressError(f"HTTP error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error for {method} {url}: {str(e)}")
            raise WordpressError(f"Unexpected error: {str(e)}") from e

    async def _handle_error_response(self, response: httpx.Response):
        """Pass and handle Wordpress error response."""
        try:
            error_data = await response.json()
            message = error_data.get('message', 'Unknown Wordpress error')
            code = error_data.get('code', 'unknown_error')
        except:
            message = response.text or f"HTTP {response.status_code}"
            code = f"http_{response.status_code}"
        
        if response.status_code == 401:
            raise WordpressAuthError(f"Authentication failed: {message} (Code: {code})")
        elif response.status_code == 404:
            raise WordpressNotFoundError(f"Resource not found: {message} (Code: {code})")
        else:
            raise WordpressError(f"Wordpress API error: {message} (Code: {code})")

    # ========== PAGINATION HELPERS ==========
    async def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        per_page: int = 100,
        max_pages: Optional[int] = None
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        
        Paginate through Wordpress REST API results.

        Args:
            endpoint: API endpoint (e.g., 'posts', 'pages')
            params: Additional query parameters
            per_page: Items per page (max 100 for Wordpress)
            max_pages: Maximum number of pages to fetch (None for all)

        Yields:
            List of items for each page
        """
        page = 1
        pages_fetched = 0
        base_params = params or {}
        base_params['per_page'] = min(per_page, 100)

        while True:
            if max_pages and pages_fetched >= max_pages:
                break
            
            # Add page parameter
            page_params = {**base_params, 'page': page}

            try:
                response = await self._request(
                    method='GET',
                    endpoint=endpoint,
                    params=page_params,
                )

                # Check if we've gone beyond the last page
                if response.status_code == 400:
                    # Wordpress returns 400 for empty pages, so we're done
                    break

                items = response.json()

                # Empty page means we're done
                if not items:
                    break

                yield items

                # CHeck if this is the last page via headers 
                total_pages = int(response.headers.get('X-WP-TotalPages', 0))
                if page >= total_pages:
                    break

                page += 1
                
            except WordpressNotFoundError as e:
                # No more pages 
                break
            except Exception as e:
                logger.error(f"Error fetching page {page} for {endpoint}: {str(e)}")
                raise WordpressError(f"Error fetching page {page}: {str(e)}") from e
    
    async def get_all(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all items from a paginated endpoint."""
        all_items = []
        async for page_items in self.paginate(endpoint, params, per_page):
            all_items.extend(page_items)
        return all_items