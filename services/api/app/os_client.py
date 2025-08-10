from urllib.parse import urlparse
from opensearchpy import OpenSearch, RequestsHttpConnection
from .settings import settings

def get_client() -> OpenSearch:
    u = urlparse(str(settings.OS_HOST))
    host = u.hostname or "opensearch"
    port = u.port or (443 if u.scheme == "https" else 80)
    use_ssl = (u.scheme == "https")
    return OpenSearch(
        hosts=[{"host": host, "port": port, "scheme": u.scheme}],
        http_auth=(settings.OS_USER, settings.OS_PASSWORD),
        use_ssl=use_ssl,
        verify_certs=False,          # local dev: self-signed
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        connection_class=RequestsHttpConnection,
        timeout=15,
        max_retries=3,
        retry_on_timeout=True,
    )
