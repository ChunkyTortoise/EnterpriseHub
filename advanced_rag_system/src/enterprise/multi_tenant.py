"""Multi-tenant document store with strict tenant isolation."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional


class TenantIsolationError(PermissionError):
    """Raised when a tenant attempts to access another tenant's data."""


@dataclass
class _Document:
    doc_id: str
    content: str
    tenant_id: str


class TenantDocumentStore:
    """
    In-memory document store with strict per-tenant namespace isolation.
    Thread-safe via a single reentrant lock.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, _Document]] = {}  # tenant_id -> {doc_id -> doc}
        self._lock = threading.RLock()

    def _assert_tenant(self, tenant_id: str, doc: _Document) -> None:
        if doc.tenant_id != tenant_id:
            raise TenantIsolationError(
                f"Tenant '{tenant_id}' cannot access document owned by '{doc.tenant_id}'"
            )

    def add_document(self, tenant_id: str, doc_id: str, content: str) -> None:
        with self._lock:
            self._store.setdefault(tenant_id, {})[doc_id] = _Document(doc_id, content, tenant_id)

    def get_document(self, tenant_id: str, doc_id: str) -> Optional[str]:
        with self._lock:
            tenant_docs = self._store.get(tenant_id, {})
            doc = tenant_docs.get(doc_id)
            if doc is None:
                return None
            self._assert_tenant(tenant_id, doc)
            return doc.content

    def list_documents(self, tenant_id: str) -> list[str]:
        with self._lock:
            return list(self._store.get(tenant_id, {}).keys())

    def delete_document(self, tenant_id: str, doc_id: str) -> bool:
        with self._lock:
            tenant_docs = self._store.get(tenant_id, {})
            doc = tenant_docs.get(doc_id)
            if doc is None:
                return False
            self._assert_tenant(tenant_id, doc)
            del tenant_docs[doc_id]
            return True

    def _get_raw(self, doc_id: str) -> Optional[_Document]:
        """Internal: get document regardless of tenant (for testing isolation)."""
        with self._lock:
            for tenant_docs in self._store.values():
                if doc_id in tenant_docs:
                    return tenant_docs[doc_id]
            return None
