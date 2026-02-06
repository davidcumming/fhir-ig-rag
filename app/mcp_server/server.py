from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional
import sys

from mcp.server.fastmcp import FastMCP

API_BASE = "http://localhost:8000"

mcp = FastMCP("fhir-ig-rag")


def _http_get(path: str, params: dict) -> dict:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{API_BASE}{path}?{query}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = {"error": str(e)}
        return {"status": e.code, "detail": detail}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


@mcp.tool()
def psca_must_support(canonical: str, version: Optional[str] = None):
    """List mustSupport paths for a PS-CA profile."""
    return _http_get("/gq/must-support", {"canonical": canonical, "version": version})


@mcp.tool()
def psca_bindings(canonical: str, path: str, version: Optional[str] = None):
    """List bindings for a PS-CA profile element path."""
    return _http_get("/gq/bindings", {"canonical": canonical, "path": path, "version": version})


@mcp.tool()
def psca_constraints(canonical: str, path: Optional[str] = None, version: Optional[str] = None):
    """List constraints for a PS-CA profile (optionally filtered by path)."""
    return _http_get("/gq/constraints", {"canonical": canonical, "path": path, "version": version})


@mcp.tool()
def psca_where_used_value_set(
    value_set: str, ig: str = "ps-ca", ig_version: str = "2.1.1"
):
    """Find where a ValueSet is used across PS-CA profiles."""
    return _http_get(
        "/gq/value-set/where-used",
        {"value_set": value_set, "ig": ig, "ig_version": ig_version},
    )


@mcp.tool()
def psca_profile_summary(canonical: str, version: Optional[str] = None):
    """Summarize mustSupport/bindings/constraints for a profile."""
    return _http_get("/gq/profile-summary", {"canonical": canonical, "version": version, "include_all": False})


@mcp.tool()
def psca_profile_summary_all(canonical: str, version: Optional[str] = None):
    """Summarize a profile and include all rows (not just top 10)."""
    return _http_get("/gq/profile-summary", {"canonical": canonical, "version": version, "include_all": True})


@mcp.tool()
def psca_element_details(canonical: str, path: str, version: Optional[str] = None):
    """Get detailed information for a specific element of a profile."""
    return _http_get(
        "/gq/element-details",
        {"canonical": canonical, "path": path, "version": version},
    )


if __name__ == "__main__":
    print("MCP server started (stdio). Waiting for client...", file=sys.stderr, flush=True)
    mcp.run(transport="stdio")
