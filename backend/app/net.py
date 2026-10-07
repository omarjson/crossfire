"""Shared egress networking for sandboxed runtimes.

Some runtimes inject HTTPS_PROXY with raw credentials that break httpx's URL
parser, and terminate TLS at an intercepting proxy with a custom CA. These
helpers normalize both; they degrade gracefully to direct connections
elsewhere (no env vars -> proxy=None, system CA verification).
"""
from __future__ import annotations

import os
import re
from urllib.parse import quote


def egress_proxy_url() -> str | None:
    raw = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not raw:
        return None
    m = re.match(r"^(https?://)([^@]+)@(.+)$", raw)
    if not m:
        return raw
    return m.group(1) + quote(m.group(2), safe="") + "@" + m.group(3)


def tls_ca_bundle() -> str | bool:
    for cand in (
        os.environ.get("SSL_CERT_FILE"),
        "/run/hatch/egress-tls/ca-bundle.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    ):
        if cand and os.path.isfile(cand):
            return cand
    return True
