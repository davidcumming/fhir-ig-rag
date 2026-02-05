#!/usr/bin/env python3
"""Generate PS-CA golden question fixtures from local StructureDefinition JSON files.

The script:
- Scans `data/artifacts/ps-ca/2.1.1/StructureDefinition` for StructureDefinition JSONs.
- Extracts key metadata, mustSupport paths, bindings, and constraints (preferring
  differential content, falling back to snapshot).
- Builds a deterministic set of 12 "golden questions" that reference real
  canonicals and element paths from the dataset.
- Writes two artifacts:
    * docs/golden_questions_psca.md
    * tests/acceptance/psca_golden_questions.json

Standard library only; output is deterministic given the input files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "data" / "artifacts" / "ps-ca" / "2.1.1" / "StructureDefinition"
DOCS_PATH = ROOT / "docs" / "golden_questions_psca.md"
JSON_PATH = ROOT / "tests" / "acceptance" / "psca_golden_questions.json"
DESIRED_QUESTION_COUNT = 12
PREFERRED_TYPES = [
    "Patient",
    "Observation",
    "MedicationRequest",
    "DiagnosticReport",
    "Composition",
    "AllergyIntolerance",
    "Condition",
    "MedicationStatement",
]


def dedup_preserve(seq: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in seq:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def ensure_dirs() -> None:
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass(order=True)
class Binding:
    path: str
    strength: Optional[str]
    value_set: Optional[str]


@dataclass(order=True)
class Constraint:
    path: str
    key: str
    severity: Optional[str]
    human: Optional[str]
    expression: Optional[str]


@dataclass
class StructureProfile:
    path: Path
    url: str
    version: Optional[str]
    name: Optional[str]
    title: Optional[str]
    type: Optional[str]
    base_definition: Optional[str]
    primary_elements: List[Dict]
    snapshot_elements: List[Dict]
    must_support: List[str] = field(default_factory=list)
    bindings_primary: List[Binding] = field(default_factory=list)
    bindings_snapshot: List[Binding] = field(default_factory=list)
    constraints_primary: List[Constraint] = field(default_factory=list)
    constraints_snapshot: List[Constraint] = field(default_factory=list)
    differential_elements: List[Dict] = field(default_factory=list)


def collect_bindings(elements: Sequence[Dict]) -> List[Binding]:
    bindings: List[Binding] = []
    for el in elements:
        binding = el.get("binding")
        if binding and "valueSet" in binding:
            bindings.append(
                Binding(
                    path=el.get("path", ""),
                    strength=binding.get("strength"),
                    value_set=binding.get("valueSet"),
                )
            )
    # Deterministic order: by path then value_set
    bindings.sort(key=lambda b: (b.path, b.value_set or ""))
    return bindings


def collect_constraints(elements: Sequence[Dict]) -> List[Constraint]:
    constraints: List[Constraint] = []
    for el in elements:
        path = el.get("path", "")
        for cons in el.get("constraint", []):
            constraints.append(
                Constraint(
                    path=path,
                    key=cons.get("key", ""),
                    severity=cons.get("severity"),
                    human=cons.get("human"),
                    expression=cons.get("expression"),
                )
            )
    constraints.sort(key=lambda c: (c.path, c.key))
    return constraints


def extract_must_support(elements: Sequence[Dict]) -> List[str]:
    paths = [el.get("path", "") for el in elements if el.get("mustSupport") is True]
    return dedup_preserve(paths)


def load_profiles() -> List[StructureProfile]:
    profiles: List[StructureProfile] = []
    for path in sorted(INPUT_DIR.glob("*.json")):
        with path.open() as handle:
            data = json.load(handle)
        if data.get("resourceType") != "StructureDefinition":
            continue

        differential_elements = data.get("differential", {}).get("element", [])
        snapshot_elements = data.get("snapshot", {}).get("element", [])
        primary_elements = differential_elements if differential_elements else snapshot_elements

        profile = StructureProfile(
            path=path,
            url=data.get("url"),
            version=data.get("version"),
            name=data.get("name"),
            title=data.get("title"),
            type=data.get("type"),
            base_definition=data.get("baseDefinition"),
            primary_elements=primary_elements,
            snapshot_elements=snapshot_elements,
            must_support=extract_must_support(primary_elements),
            bindings_primary=collect_bindings(primary_elements),
            bindings_snapshot=collect_bindings(snapshot_elements),
            constraints_primary=collect_constraints(primary_elements),
            constraints_snapshot=collect_constraints(snapshot_elements),
            differential_elements=differential_elements,
        )
        profiles.append(profile)

    profiles.sort(key=lambda p: (p.type or "", p.name or ""))
    return profiles


def select_profiles(profiles: Sequence[StructureProfile]) -> List[StructureProfile]:
    """Pick one profile per preferred type (if present), then fill with remaining."""
    selected: List[StructureProfile] = []
    used_urls = set()
    by_type: Dict[str, List[StructureProfile]] = {}
    for p in profiles:
        by_type.setdefault(p.type or "", []).append(p)
    for t in PREFERRED_TYPES:
        if t in by_type and by_type[t]:
            choice = by_type[t][0]
            selected.append(choice)
            used_urls.add(choice.url)
    for p in profiles:
        if p.url in used_urls:
            continue
        selected.append(p)
        used_urls.add(p.url)
    return selected


def pick_binding(profile: StructureProfile) -> Optional[Binding]:
    candidates = profile.bindings_primary or profile.bindings_snapshot
    if not candidates:
        return None
    required = [b for b in candidates if b.strength == "required"]
    return (required or candidates)[0]


def pick_constraint(profile: StructureProfile) -> Optional[Constraint]:
    candidates = profile.constraints_primary or profile.constraints_snapshot
    if not candidates:
        return None
    return candidates[0]


def pick_diff_change(profile: StructureProfile) -> Optional[Dict]:
    for el in profile.differential_elements:
        interesting_keys = {"min", "max", "mustSupport", "slicing", "patternCodeableConcept", "patternCoding", "patternCode", "fixedCode"}
        if any(k in el for k in interesting_keys):
            return el
    return profile.differential_elements[1] if len(profile.differential_elements) > 1 else None


def summarize_diff(el: Dict) -> str:
    parts: List[str] = []
    if "min" in el:
        parts.append(f"min={el['min']}")
    if "max" in el:
        parts.append(f"max={el['max']}")
    if el.get("mustSupport"):
        parts.append("mustSupport=true")
    if "slicing" in el:
        rules = el["slicing"].get("rules")
        if rules:
            parts.append(f"slicing.rules={rules}")
    for key in ("patternCoding", "patternCode", "patternCodeableConcept", "fixedCode"):
        if key in el:
            parts.append(f"{key} present")
    return ", ".join(parts) if parts else "No differential constraints found"


def build_value_set_index(profiles: Sequence[StructureProfile]) -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = {}
    for profile in profiles:
        for binding in profile.bindings_snapshot or profile.bindings_primary:
            if not binding.value_set:
                continue
            index.setdefault(binding.value_set, []).append(binding.path)
    # Deterministic ordering
    for value_set in list(index.keys()):
        index[value_set] = sorted(set(index[value_set]))
    return dict(sorted(index.items(), key=lambda item: item[0]))


def pick_shared_value_set(index: Dict[str, List[str]], profiles: Sequence[StructureProfile]) -> Optional[str]:
    # Choose a value set used by more than one profile if possible; otherwise first available.
    profile_urls_by_vs: Dict[str, set] = {}
    for vs, paths in index.items():
        profile_urls_by_vs[vs] = set()
        for profile in profiles:
            for binding in profile.bindings_snapshot or profile.bindings_primary:
                if binding.value_set == vs:
                    profile_urls_by_vs[vs].add(profile.url)
    multi = [vs for vs, urls in profile_urls_by_vs.items() if len(urls) > 1]
    if multi:
        return sorted(multi)[0]
    return next(iter(index.keys()), None)


def build_golden_questions(profiles: Sequence[StructureProfile]) -> List[Dict]:
    questions: List[Dict] = []

    def add(question_text: str, profile: Optional[StructureProfile], element_path: Optional[str], expected_fields: List[str], notes: Optional[str] = None) -> None:
        if len(questions) >= DESIRED_QUESTION_COUNT:
            return
        qid = f"PSCA-GQ-{len(questions)+1:02d}"
        questions.append(
            {
                "id": qid,
                "question": question_text,
                "profile_canonical_url": profile.url if profile else None,
                "version": profile.version if profile else None,
                "element_path": element_path,
                "expected_fields": expected_fields,
                "notes": notes,
            }
        )

    selected_profiles = select_profiles(profiles)

    # MustSupport coverage (up to 3)
    ms_added = 0
    for profile in selected_profiles:
        if ms_added >= 3:
            break
        if profile.must_support:
            add(
                question_text=f"List all mustSupport elements in {profile.name}.",
                profile=profile,
                element_path=None,
                expected_fields=["must_support_paths", "profile_url", "profile_type"],
            )
            ms_added += 1

    # Binding coverage (up to 3)
    binding_added = 0
    for profile in selected_profiles:
        if binding_added >= 3 or len(questions) >= DESIRED_QUESTION_COUNT:
            break
        binding = pick_binding(profile)
        if binding:
            add(
                question_text=f"What binding applies to {binding.path} in {profile.name}?",
                profile=profile,
                element_path=binding.path,
                expected_fields=["bindings", "profile_url", "profile_version"],
            )
            binding_added += 1

    # Constraint coverage (up to 3)
    constraint_added = 0
    for profile in selected_profiles:
        if constraint_added >= 3 or len(questions) >= DESIRED_QUESTION_COUNT:
            break
        constraint = pick_constraint(profile)
        if constraint:
            add(
                question_text=f"List constraints on {constraint.path} in {profile.name} (e.g., {constraint.key}).",
                profile=profile,
                element_path=constraint.path,
                expected_fields=["constraints", "profile_url"],
            )
            constraint_added += 1

    # Cross-profile ValueSet usage (once)
    vs_index = build_value_set_index(selected_profiles)
    chosen_vs = pick_shared_value_set(vs_index, selected_profiles)
    if chosen_vs:
        add(
            question_text=f"Which profile elements bind to ValueSet {chosen_vs}?",
            profile=None,
            element_path=None,
            expected_fields=["bindings", "value_set_usage"],
        )

    # Lineage/baseDefinition (once)
    if selected_profiles:
        add(
            question_text=f"Show the baseDefinition chain for {selected_profiles[0].name} and the PS-CA canonical URL.",
            profile=selected_profiles[0],
            element_path=None,
            expected_fields=["base_definition", "profile_url", "lineage_chain"],
        )

    # Differential change (first available)
    for profile in selected_profiles:
        diff_el = pick_diff_change(profile)
        if diff_el:
            add(
                question_text=f"What changed vs base for {diff_el.get('path')} in {profile.name}?",
                profile=profile,
                element_path=diff_el.get("path"),
                expected_fields=["diff_changes", "profile_url", "profile_version"],
            )
            break

    # Fallback: if still short of the target, add remaining mustSupport items.
    if len(questions) < DESIRED_QUESTION_COUNT:
        for profile in selected_profiles:
            if len(questions) >= DESIRED_QUESTION_COUNT:
                break
            if profile.must_support:
                add(
                    question_text=f"List all mustSupport elements in {profile.name}.",
                    profile=profile,
                    element_path=None,
                    expected_fields=["must_support_paths", "profile_url", "profile_type"],
                )

    return questions


def evidence_bundle_schema_section() -> str:
    lines = [
        "```json",
        json.dumps(
            {
                "profile_url": "string",
                "profile_version": "string|null",
                "profile_name": "string",
                "profile_title": "string|null",
                "profile_type": "string",
                "base_definition": "string|null",
                "lineage_chain": ["string"],
                "element_path": "string|null",
                "must_support_paths": ["string"],
                "bindings": [
                    {"path": "string", "strength": "string", "valueSet": "string"}
                ],
                "constraints": [
                    {"path": "string", "key": "string", "severity": "string", "human": "string", "expression": "string"}
                ],
                "diff_changes": [
                    {"path": "string", "summary": "string"}
                ],
                "value_set_usage": [
                    {"valueSet": "string", "paths": ["string"]}
                ],
            },
            indent=2,
        ),
        "```",
    ]
    return "\n".join(lines)


def render_markdown(profiles: Sequence[StructureProfile], questions: Sequence[Dict]) -> str:
    lines: List[str] = []
    lines.append("# PS-CA Golden Questions (auto-generated)")
    lines.append("")
    lines.append("These golden questions are derived from the PS-CA StructureDefinition JSON files present in `data/artifacts/ps-ca/2.1.1/StructureDefinition` on this machine. They are regenerated deterministically by `scripts/gen_golden_questions_psca.py`.")
    lines.append("")
    lines.append("## What are golden questions?")
    lines.append("Golden questions are concrete, testable prompts we use to validate that tooling can extract specific evidence from PS-CA profiles (e.g., mustSupport flags, bindings, constraints, and lineage). Each question pairs with an expected EvidenceBundle payload so that downstream evaluators can assert completeness.")
    lines.append("")
    lines.append("## EvidenceBundle contract")
    lines.append("The EvidenceBundle is a JSON object with the exact fields and types shown below. Nullable fields should be set to `null` rather than omitted.")
    lines.append(evidence_bundle_schema_section())
    lines.append("")
    if len(questions) < DESIRED_QUESTION_COUNT:
        lines.append(f"Only {len(questions)} high-quality questions could be generated because the input set currently exposes {len(profiles)} StructureDefinition resources. Add more profiles to broaden coverage.")
        lines.append("")
    lines.append("## Golden questions")
    lines.append("")
    for q in questions:
        lines.append(f"### {q['id']}")
        lines.append(f"- Question: {q['question']}")
        lines.append("- Example tool inputs:")
        lines.append(f"  - profile_canonical_url: {q['profile_canonical_url']}")
        lines.append(f"  - version: {q['version']}")
        lines.append(f"  - element_path: {q['element_path']}")
        lines.append("- Expected evidence fields: " + ", ".join(q.get("expected_fields", [])))
        if q.get("notes"):
            lines.append(f"- Notes: {q['notes']}")
        lines.append("")
    return "\n".join(lines)


def lineage_chain(profile: StructureProfile) -> List[str]:
    chain = [profile.url]
    if profile.base_definition:
        chain.append(profile.base_definition)
    return chain


def build_value_set_usage(index: Dict[str, List[str]]) -> List[Dict]:
    return [
        {"valueSet": vs, "paths": paths}
        for vs, paths in index.items()
    ]


def add_value_set_usage_to_questions(questions: List[Dict], value_set_usage: List[Dict]) -> None:
    for q in questions:
        if "value_set_usage" in q.get("expected_fields", []):
            q["value_set_usage"] = value_set_usage


def add_diff_summaries(questions: List[Dict], profiles: Sequence[StructureProfile]) -> None:
    summaries: Dict[str, str] = {}
    for profile in profiles:
        for el in profile.differential_elements:
            summaries[el.get("path", "")] = summarize_diff(el)
    for q in questions:
        if "diff_changes" in q.get("expected_fields", []) and q.get("element_path") in summaries:
            q["diff_changes"] = [{"path": q["element_path"], "summary": summaries[q["element_path"]]}]


def add_lineage_info(questions: List[Dict], profiles: Sequence[StructureProfile]) -> None:
    url_to_chain = {p.url: lineage_chain(p) for p in profiles}
    for q in questions:
        url = q.get("profile_canonical_url")
        if url and "lineage_chain" in q.get("expected_fields", []):
            q["lineage_chain"] = url_to_chain.get(url, [])


def write_outputs(profiles: Sequence[StructureProfile], questions: List[Dict]) -> None:
    ensure_dirs()

    # Enrich questions with auxiliary evidence for documentation clarity.
    vs_index = build_value_set_index(profiles)
    add_value_set_usage_to_questions(questions, build_value_set_usage(vs_index))
    add_diff_summaries(questions, profiles)
    add_lineage_info(questions, profiles)

    markdown = render_markdown(profiles, questions)
    DOCS_PATH.write_text(markdown)

    json_payload = [
        {
            "id": q["id"],
            "question": q["question"],
            "profile_canonical_url": q["profile_canonical_url"],
            "version": q["version"],
            "element_path": q["element_path"],
            **({"notes": q["notes"]} if q.get("notes") else {}),
        }
        for q in questions
    ]
    JSON_PATH.write_text(json.dumps(json_payload, indent=2))


def main() -> None:
    profiles = load_profiles()
    if not profiles:
        raise SystemExit("No StructureDefinition resources found; nothing to do.")

    questions = build_golden_questions(profiles)
    write_outputs(profiles, questions)


if __name__ == "__main__":
    main()
