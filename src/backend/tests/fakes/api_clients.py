from app.core.security import ApiClient, ApiClientKind


class FakeApiClientLookup:
    def __init__(self, clients_by_hash: dict[str, ApiClient]) -> None:
        self.clients_by_hash = clients_by_hash

    def find_active(self, key_hash: str, kind: ApiClientKind) -> ApiClient | None:
        client = self.clients_by_hash.get(key_hash)
        return client if client is not None and client.kind is kind else None
