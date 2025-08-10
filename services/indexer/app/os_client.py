import ssl
from typing import Any, Dict
from opensearchpy import OpenSearch


def build_client(host: str, user: str, password: str, timeout: int = 30, max_retries: int = 5, backoff: float = 0.5) -> OpenSearch:
    # Dev: self-signed certs; disable verification
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    client = OpenSearch(
        hosts=[host],
        http_compress=True,
        use_ssl=True,
        ssl_context=ctx,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        http_auth=(user, password),
        timeout=timeout,
        max_retries=max_retries,
        retry_on_timeout=True,
    )
    # backoff handled by urllib3 retry config; opensearch-py uses max_retries
    return client


def ping_ok(client: OpenSearch) -> bool:
    try:
        return bool(client.ping())
    except Exception:
        return False


def bulk(client: OpenSearch, body: str) -> Dict[str, Any]:
    # body must be NDJSON with trailing newline
    return client.bulk(body=body, refresh=False, request_timeout=30)
