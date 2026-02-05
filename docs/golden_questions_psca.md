# PS-CA Golden Questions (auto-generated)

These golden questions are derived from the PS-CA StructureDefinition JSON files present in `data/artifacts/ps-ca/2.1.1/StructureDefinition` on this machine. They are regenerated deterministically by `scripts/gen_golden_questions_psca.py`.

## What are golden questions?
Golden questions are concrete, testable prompts we use to validate that tooling can extract specific evidence from PS-CA profiles (e.g., mustSupport flags, bindings, constraints, and lineage). Each question pairs with an expected EvidenceBundle payload so that downstream evaluators can assert completeness.

## EvidenceBundle contract
The EvidenceBundle is a JSON object with the exact fields and types shown below. Nullable fields should be set to `null` rather than omitted.
```json
{
  "profile_url": "string",
  "profile_version": "string|null",
  "profile_name": "string",
  "profile_title": "string|null",
  "profile_type": "string",
  "base_definition": "string|null",
  "lineage_chain": [
    "string"
  ],
  "element_path": "string|null",
  "must_support_paths": [
    "string"
  ],
  "bindings": [
    {
      "path": "string",
      "strength": "string",
      "valueSet": "string"
    }
  ],
  "constraints": [
    {
      "path": "string",
      "key": "string",
      "severity": "string",
      "human": "string",
      "expression": "string"
    }
  ],
  "diff_changes": [
    {
      "path": "string",
      "summary": "string"
    }
  ],
  "value_set_usage": [
    {
      "valueSet": "string",
      "paths": [
        "string"
      ]
    }
  ]
}
```

## Golden questions

### PSCA-GQ-01
- Question: List all mustSupport elements in PatientPSCA.
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps
  - version: None
  - element_path: None
- Expected evidence fields: must_support_paths, profile_url, profile_type

### PSCA-GQ-02
- Question: List all mustSupport elements in ObservationAlcoholUsePSCA.
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/observation-alcoholuse-ca-ps
  - version: None
  - element_path: None
- Expected evidence fields: must_support_paths, profile_url, profile_type

### PSCA-GQ-03
- Question: List all mustSupport elements in MedicationRequestPSCA.
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/medicationrequest-ca-ps
  - version: None
  - element_path: None
- Expected evidence fields: must_support_paths, profile_url, profile_type

### PSCA-GQ-04
- Question: What binding applies to Patient.address.type in PatientPSCA?
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps
  - version: None
  - element_path: Patient.address.type
- Expected evidence fields: bindings, profile_url, profile_version

### PSCA-GQ-05
- Question: What binding applies to Observation.status in ObservationAlcoholUsePSCA?
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/observation-alcoholuse-ca-ps
  - version: None
  - element_path: Observation.status
- Expected evidence fields: bindings, profile_url, profile_version

### PSCA-GQ-06
- Question: What binding applies to MedicationRequest.dosageInstruction.route in MedicationRequestPSCA?
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/medicationrequest-ca-ps
  - version: None
  - element_path: MedicationRequest.dosageInstruction.route
- Expected evidence fields: bindings, profile_url, profile_version

### PSCA-GQ-07
- Question: List constraints on Patient.name in PatientPSCA (e.g., core-pat-1).
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps
  - version: None
  - element_path: Patient.name
- Expected evidence fields: constraints, profile_url

### PSCA-GQ-08
- Question: List constraints on Observation in ObservationAlcoholUsePSCA (e.g., dom-2).
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/observation-alcoholuse-ca-ps
  - version: None
  - element_path: Observation
- Expected evidence fields: constraints, profile_url

### PSCA-GQ-09
- Question: List constraints on MedicationRequest in MedicationRequestPSCA (e.g., dom-2).
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/medicationrequest-ca-ps
  - version: None
  - element_path: MedicationRequest
- Expected evidence fields: constraints, profile_url

### PSCA-GQ-10
- Question: Which profile elements bind to ValueSet http://fhir.infoway-inforoute.ca/io/psca/ValueSet/pCLOCD?
- Example tool inputs:
  - profile_canonical_url: None
  - version: None
  - element_path: None
- Expected evidence fields: bindings, value_set_usage

### PSCA-GQ-11
- Question: Show the baseDefinition chain for PatientPSCA and the PS-CA canonical URL.
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps
  - version: None
  - element_path: None
- Expected evidence fields: base_definition, profile_url, lineage_chain

### PSCA-GQ-12
- Question: What changed vs base for Patient.identifier in PatientPSCA?
- Example tool inputs:
  - profile_canonical_url: http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps
  - version: None
  - element_path: Patient.identifier
- Expected evidence fields: diff_changes, profile_url, profile_version
