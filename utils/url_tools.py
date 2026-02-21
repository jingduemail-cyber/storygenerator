from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def add_query_params(url: str, params: dict) -> str:
    u = urlparse(url)
    q = dict(parse_qsl(u.query, keep_blank_values=True))
    q.update({k: str(v) for k, v in params.items()})
    new_query = urlencode(q, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))