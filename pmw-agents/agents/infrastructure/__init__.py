"""
agents/infrastructure — top-level package.

Import get_infrastructure() from here everywhere in the codebase:

    from infrastructure import get_infrastructure
    infra = get_infrastructure()
"""

from infrastructure.infrastructure import Infrastructure, get_infrastructure

__all__ = ["Infrastructure", "get_infrastructure"]