from __future__ import annotations

import weaviate
import weaviate.classes as wvc
from urllib.parse import urlparse
from weaviate.auth import AuthApiKey

from app.core.settings_secrets import secrets
from app.core.settings_constant import constants


class WeaviateClientWrapper:

    def __init__(self) -> None:
        self._client: weaviate.WeaviateClient | None = None

    # Private Methods
    def _create_collection(self, client: weaviate.WeaviateClient, name: str) -> None:
        client.collections.create(
            name=name,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_huggingface(
                model=constants.rag.embedding_model,
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
        print(f"[Weaviate] Created collection '{name}'.")

    def _connect(self) -> weaviate.WeaviateClient:
        url: str = secrets.weaviate_url
        api_key: str | None = secrets.weaviate_api_key

        connect_kwargs: dict = {
            "headers": {"X-HuggingFace-Api-Key": secrets.hf_token},
        }
        if api_key:
            connect_kwargs["auth_credentials"] = AuthApiKey(api_key=api_key)

        if "weaviate.io" in url or "weaviatecloud" in url:
            return weaviate.connect_to_weaviate_cloud(cluster_url=url, **connect_kwargs)

        parsed = urlparse(url)
        return weaviate.connect_to_local(
            host=parsed.hostname or "localhost",
            port=parsed.port or 8080,
            **connect_kwargs,
        )

    def _ensure_collection(self, client: weaviate.WeaviateClient) -> None:
        collection_name: str = constants.rag.collection_name
        if not client.collections.exists(collection_name):
            self._create_collection(client, collection_name)
        else:
            print(f"[Weaviate] Collection '{collection_name}' already exists.")

    # Public Methods
    def get_client(self) -> weaviate.WeaviateClient:
        """Return (and lazily create) the shared Weaviate client."""
        if self._client is None:
            self._client = self._connect()
            self._ensure_collection(self._client)
        return self._client

    def close(self) -> None:
        """Close the underlying connection (call on app shutdown)."""
        if self._client is not None:
            self._client.close()
            self._client = None


weaviate_client = WeaviateClientWrapper()
