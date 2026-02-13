from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional
import sys
import os
from datetime import datetime, timezone

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


# Router --------------------------------------------------------------------

INTENTS = {
    "element_details",
    "profile_summary",
    "must_support",
    "bindings",
    "constraints",
    "where_used_value_set",
    "unknown",
}


def _extract_slots(question: str, canonical: Optional[str], path: Optional[str], value_set: Optional[str], version: Optional[str]):
    # Use hints if provided
    slots = {"canonical": canonical, "path": path, "value_set": value_set, "version": version}
    q = question or ""
    # Extract canonical
    if not slots["canonical"]:
        for token in q.split():
            if "StructureDefinition" in token and token.startswith("http"):
                slots["canonical"] = token.strip(",;)")
                break
    # Extract value set
    if not slots["value_set"]:
        for token in q.split():
            if "ValueSet" in token:
                slots["value_set"] = token.strip(",;)")
                break
    # Extract path heuristic: token with dot and capitalized resource start
    if not slots["path"]:
        for token in q.replace(",", " ").split():
            if "." in token and token[0].isupper():
                slots["path"] = token.strip(",;)")
                break
    return slots


def _deterministic_intent(question: str, slots: dict) -> str:
    q = (question or "").lower()
    if slots.get("path") or "element" in q or "." in q:
        return "element_details"
    if "must support" in q:
        return "must_support"
    if "where used" in q or "where-used" in q or "across" in q:
        if slots.get("value_set"):
            return "where_used_value_set"
    if "binding" in q or "valueset" in q or "value set" in q:
        return "bindings"
    if "constraint" in q or "invariant" in q:
        return "constraints"
    if "summary" in q or "profile summary" in q:
        return "profile_summary"
    return "unknown"


def _ollama_route(question: str, slots: dict) -> Optional[dict]:
    url = os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/generate"
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
    prompt = f"""
You are a strict router for PS-CA IG facts. Decide the intent and slots.
Return ONLY JSON with keys: intent (one of element_details, profile_summary, must_support, bindings, constraints, where_used_value_set, unknown), canonical, path, value_set, version, confidence (0..1), notes.
Input question: {question}
Hints: canonical={slots.get('canonical')}, path={slots.get('path')}, value_set={slots.get('value_set')}, version={slots.get('version')}
"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            # ollama returns response field containing the content
            inner = outer.get("response", "")
            parsed = json.loads(inner)
            if not isinstance(parsed, dict):
                return None
            if parsed.get("intent") not in INTENTS:
                return None
            conf = parsed.get("confidence")
            if conf is None or not (0 <= conf <= 1):
                return None
            return parsed
    except Exception:
        return None


def _build_plan(intent: str, slots: dict) -> list:
    plan = []
    if intent == "element_details":
        if slots.get("canonical") and slots.get("path"):
            plan.append({"tool": "psca_element_details", "args": {k: slots.get(k) for k in ["canonical", "path", "version"]}})
    elif intent == "profile_summary":
        if slots.get("canonical"):
            plan.append({"tool": "psca_profile_summary", "args": {k: slots.get(k) for k in ["canonical", "version"]}})
    elif intent == "must_support":
        if slots.get("canonical"):
            plan.append({"tool": "psca_must_support", "args": {k: slots.get(k) for k in ["canonical", "version"]}})
    elif intent == "bindings":
        if slots.get("canonical") and slots.get("path"):
            plan.append({"tool": "psca_bindings", "args": {k: slots.get(k) for k in ["canonical", "path", "version"]}})
    elif intent == "constraints":
        if slots.get("canonical"):
            plan.append({"tool": "psca_constraints", "args": {k: slots.get(k) for k in ["canonical", "path", "version"]}})
    elif intent == "where_used_value_set":
        if slots.get("value_set"):
            plan.append({"tool": "psca_where_used_value_set", "args": {"value_set": slots.get("value_set"), "ig": "ps-ca", "ig_version": "2.1.1"}})
    return plan


def _execute_plan(plan: list) -> list:
    results = []
    tool_map = {
        "psca_element_details": psca_element_details,
        "psca_profile_summary": psca_profile_summary,
        "psca_must_support": psca_must_support,
        "psca_bindings": psca_bindings,
        "psca_constraints": psca_constraints,
        "psca_where_used_value_set": psca_where_used_value_set,
    }
    for call in plan:
        tool = call["tool"]
        args = call["args"] or {}
        fn = tool_map.get(tool)
        if not fn:
            results.append({"tool": tool, "args": args, "ok": False, "data": None, "error": "unknown tool"})
            continue
        try:
            data = fn(**{k: v for k, v in args.items() if v is not None})
            results.append({"tool": tool, "args": args, "ok": True, "data": data, "error": None})
        except Exception as e:  # noqa: BLE001
            results.append({"tool": tool, "args": args, "ok": False, "data": None, "error": str(e)})
    return results


@mcp.tool()
def psca_router(
    question: str,
    canonical: Optional[str] = None,
    path: Optional[str] = None,
    value_set: Optional[str] = None,
    version: Optional[str] = None,
    execute: bool = True,
):
    """Route a natural-language PS-CA question to the right tool(s)."""
    mode_requested = os.getenv("ROUTER_MODE", "").lower()
    slots = _extract_slots(question, canonical, path, value_set, version)
    used_mode = "deterministic"
    fallback_used = False
    confidence = None

    routing = None
    if mode_requested == "ollama":
        parsed = _ollama_route(question, slots)
        if parsed:
            used_mode = "ollama"
            routing_intent = parsed.get("intent", "unknown")
            slots["canonical"] = slots.get("canonical") or parsed.get("canonical")
            slots["path"] = slots.get("path") or parsed.get("path")
            slots["value_set"] = slots.get("value_set") or parsed.get("value_set")
            slots["version"] = slots.get("version") or parsed.get("version")
            confidence = parsed.get("confidence")
        else:
            fallback_used = True
            routing_intent = _deterministic_intent(question, slots)
    else:
        routing_intent = _deterministic_intent(question, slots)

    plan = _build_plan(routing_intent, slots)
    results = _execute_plan(plan) if execute and plan else []

    return {
        "query_id": "PSCA-MCP-ROUTER-01",
        "router": {
            "mode_requested": mode_requested or "deterministic",
            "mode_used": used_mode,
            "fallback_used": fallback_used,
            "confidence": confidence,
        },
        "input": {
            "question": question,
            "canonical": canonical,
            "path": path,
            "value_set": value_set,
            "version": version,
            "execute": execute,
        },
        "routing": {
            "intent": routing_intent,
            "extracted": slots,
            "tool_calls": plan,
        },
        "results": results,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    print("MCP server started (stdio). Waiting for client...", file=sys.stderr, flush=True)
    mcp.run(transport="stdio")
