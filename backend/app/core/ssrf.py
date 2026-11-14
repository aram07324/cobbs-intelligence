"""SSRF, DNS-rebinding and egress protection.

Blocks private, loopback, link-local, metadata and other non-routable targets.
Resolves hostnames and validates *all* resolved addresses before use.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.logging import get_logger

logger = get_logger(__name__)

BLOCKED_HOSTNAMES = {
    "metadata.google.internal",
    "metadata.google",
    "instance-data",
    "kubernetes.default",
    "kubernetes.default.svc",
}

METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),
    ipaddress.ip_address("fd00:ec2::254"),
}


class TargetValidationError(Exception):
    def __init__(self, message: str, *, code: str = "invalid_target"):
        self.code = code
        super().__init__(message)


@dataclass
class ResolvedTarget:
    original: str
    hostname: str | None
    port: int | None
    scheme: str | None
    addresses: list[str]
    is_ip_literal: bool


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> tuple[bool, str]:
    if ip in METADATA_IPS:
        return True, "metadata_ip"
    if ip.is_loopback:
        return True, "loopback"
    if ip.is_private:
        return True, "private"
    if ip.is_link_local:
        return True, "link_local"
    if ip.is_multicast:
        return True, "multicast"
    if ip.is_reserved:
        return True, "reserved"
    if ip.is_unspecified:
        return True, "unspecified"
    if isinstance(ip, ipaddress.IPv6Address) and ip.is_private:
        return True, "private_v6"
    return False, ""


def parse_target(raw: str) -> tuple[str | None, str, int | None]:
    raw = (raw or "").strip()
    if not raw or len(raw) > 2048:
        raise TargetValidationError("Empty or oversized target", code="invalid_hostname")

    scheme = None
    port = None
    host = raw

    if "://" in raw:
        parsed = urlparse(raw)
        scheme = (parsed.scheme or "").lower() or None
        if scheme and scheme not in ("http", "https", "dns"):
            raise TargetValidationError(f"Unsupported scheme: {scheme}", code="invalid_scheme")
        host = parsed.hostname or ""
        port = parsed.port
        if not host:
            raise TargetValidationError("URL missing hostname", code="invalid_hostname")
    else:
        if raw.count(":") == 1 and not raw.startswith("["):
            host, _, port_s = raw.partition(":")
            try:
                port = int(port_s)
            except ValueError as exc:
                raise TargetValidationError("Invalid port", code="invalid_port") from exc
        else:
            host = raw

    host = host.strip().lower().rstrip(".")
    if not host or len(host) > 253:
        raise TargetValidationError("Invalid hostname", code="invalid_hostname")
    if host in BLOCKED_HOSTNAMES:
        raise TargetValidationError("Blocked hostname", code="blocked_hostname")
    if " " in host:
        raise TargetValidationError("Invalid hostname", code="invalid_hostname")

    return scheme, host, port


def resolve_and_validate(host: str) -> list[str]:
    try:
        ip = ipaddress.ip_address(host)
        blocked, reason = _is_blocked_ip(ip)
        if blocked:
            raise TargetValidationError(
                f"Target address blocked ({reason})", code=f"blocked_{reason}"
            )
        return [str(ip)]
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise TargetValidationError(
            f"DNS resolution failed for {host}", code="dns_failure"
        ) from exc

    addresses: list[str] = []
    seen: set[str] = set()
    for info in infos:
        addr = info[4][0]
        if addr in seen:
            continue
        seen.add(addr)
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        blocked, reason = _is_blocked_ip(ip)
        if blocked:
            raise TargetValidationError(
                f"Resolved address {addr} blocked ({reason}) — possible DNS rebinding risk",
                code=f"dns_rebinding_{reason}",
            )
        addresses.append(addr)

    if not addresses:
        raise TargetValidationError("No usable addresses resolved", code="dns_failure")
    return addresses


def validate_target(raw: str) -> ResolvedTarget:
    scheme, host, port = parse_target(raw)
    is_literal = False
    try:
        ipaddress.ip_address(host)
        is_literal = True
    except ValueError:
        is_literal = False

    addresses = resolve_and_validate(host)
    return ResolvedTarget(
        original=raw,
        hostname=host,
        port=port,
        scheme=scheme,
        addresses=addresses,
        is_ip_literal=is_literal,
    )


def validate_redirect_location(location: str, *, original_host: str) -> ResolvedTarget:
    if not location:
        raise TargetValidationError("Empty redirect", code="invalid_redirect")
    if location.startswith("/") and not location.startswith("//"):
        return validate_target(f"https://{original_host}{location}")
    return validate_target(location)
