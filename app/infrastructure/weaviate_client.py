"""
app/infrastructure/weaviate_client.py
--------------------------------------
Singleton Weaviate v4 client for the RAG knowledge-base.

The client connects to a Weaviate instance using credentials from
SecretSettings (WEAVIATE_URL / WEAVIATE_API_KEY).  When WEAVIATE_API_KEY
is not set the client connects without authentication, which is fine for
a locally-running Weaviate container.

Usage
-----
    from app.infrastructure.weaviate_client import weaviate_client, WeaviateClientWrapper
    client = weaviate_client.get_client()  # returns weaviate.WeaviateClient
"""
from __future__ import annotations

import weaviate
from weaviate.auth import AuthApiKey

from app.core.settings_secrets import secrets
from app.core.settings_constant import constants


class WeaviateClientWrapper:
    """
    Thin wrapper that lazily initialises and caches a ``weaviate.WeaviateClient``.

    The underlying client is only created on the first call to ``get_client()``.
    Call ``close()`` (e.g. in an application shutdown hook) to release the
    connection gracefully.
    """

    def __init__(self) -> None:
        self._client: weaviate.WeaviateClient | None = None

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def get_client(self) -> weaviate.WeaviateClient:
        """Return (and lazily create) the shared Weaviate client."""
        if self._client is None:
            self._client = self._connect()
        return self._client

    def _connect(self) -> weaviate.WeaviateClient:
        """Build and open a Weaviate v4 client from project settings."""
        url: str = secrets.weaviate_url
        api_key: str | None = secrets.weaviate_api_key

        connect_kwargs: dict = {}
        if api_key:
            connect_kwargs["auth_credentials"] = AuthApiKey(api_key=api_key)

        # weaviate-client v4 uses connect_to_weaviate_cloud for WCS
        # and connect_to_local for self-hosted / Docker setups.
        if "weaviate.io" in url or "weaviatecloud" in url:
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                **connect_kwargs,
            )
        else:
            # Parse host / port from the URL for local connections
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8080

            client = weaviate.connect_to_local(
                host=host,
                port=port,
                **connect_kwargs,
            )

        return client

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def ensure_collection(self) -> None:
        """
        Create the RAG knowledge-base collection in Weaviate if it does
        not already exist.

        The collection uses a cosine-distance (inner-product) HNSW index
        and stores the embedding externally (we supply vectors at insert time).
        """
        import weaviate.classes as wvc

        client = self.get_client()
        collection_name: str = constants.rag.collection_name

        if not client.collections.exists(collection_name):
            client.collections.create(
                name=collection_name,
                vectorizer_config=wvc.config.Configure.Vectorizer.none(),
                vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
                    distance_metric=wvc.config.VectorDistances.COSINE,
                ),
                properties=[
                    wvc.config.Property(
                        name="text",
                        data_type=wvc.config.DataType.TEXT,
                        description="Chunk of the source document",
                    ),
                    wvc.config.Property(
                        name="source",
                        data_type=wvc.config.DataType.TEXT,
                        description="Original filename or document identifier",
                    ),
                    wvc.config.Property(
                        name="chunk_index",
                        data_type=wvc.config.DataType.INT,
                        description="Zero-based position of this chunk in the document",
                    ),
                ],
            )
            print(f"[Weaviate] Created collection '{collection_name}'.")
        else:
            print(f"[Weaviate] Collection '{collection_name}' already exists.")

    def close(self) -> None:
        """Close the underlying connection (call on app shutdown)."""
        if self._client is not None:
            self._client.close()
            self._client = None


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------
weaviate_client = WeaviateClientWrapper()
