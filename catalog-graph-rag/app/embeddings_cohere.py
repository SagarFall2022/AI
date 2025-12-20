import requests
from typing import List

class CohereEmbedder:
    """
    Cohere embeddings on Azure AI Inference.

    This endpoint requires:
      Authorization: Bearer <API_KEY>

    Tries both common paths:
      - /v1/embeddings
      - /embeddings
    And both common payload shapes:
      - {"model": ..., "input": "..."} or {"input": [..]}
      - {"model": ..., "texts": [..]}
    """

    def __init__(self, endpoint: str, key: str, deployment: str, dim: int):
        self.endpoint = endpoint.rstrip("/")
        self.deployment = deployment
        self.dim = dim

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        }

        self.urls = [
            f"{self.endpoint}/v1/embeddings",
            f"{self.endpoint}/embeddings",
        ]

    def embed(self, text: str) -> List[float]:
        payloads = [
            {"model": self.deployment, "input": text},
            {"model": self.deployment, "input": [text]},
            {"model": self.deployment, "texts": [text]},
        ]

        last = None
        for url in self.urls:
            for payload in payloads:
                try:
                    r = requests.post(url, headers=self.headers, json=payload, timeout=60)
                    if r.status_code == 404:
                        last = f"404 Not Found at {url}"
                        continue
                    if r.status_code >= 400:
                        last = f"{r.status_code} {r.text}"
                        continue

                    data = r.json()

                    # Response variants:
                    if "data" in data and data["data"]:
                        vec = data["data"][0].get("embedding")
                        if vec:
                            return self._check(vec)
                    if "embeddings" in data and data["embeddings"]:
                        return self._check(data["embeddings"][0])

                    last = f"Unexpected response: {data}"
                except Exception as e:
                    last = str(e)

        raise RuntimeError(f"Cohere embeddings failed after trying {self.urls}. Last error: {last}")

    def _check(self, vec: List[float]) -> List[float]:
        if len(vec) != self.dim:
            raise ValueError(f"Embedding dim mismatch: expected {self.dim}, got {len(vec)}")
        return vec
