# Prompt

Use psca_profile_summary with canonical http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps and include_all=true. Show returned JSON.

# Response

I'll call the psca_profile_summary function with the parameters you specified.Here's the returned JSON from the `psca_profile_summary` call:

```json
{
  "query_id": "PSCA-MCP-PROFILE-SUMMARY-01",
  "scope": {
    "ig": "ps-ca",
    "ig_version": "2.1.1"
  },
  "profile": {
    "canonical_url": "http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps",
    "version": null,
    "name": "PatientPSCA",
    "sd_type": "Patient",
    "title": "Patient (PS-CA)",
    "base_definition": "http://hl7.org/fhir/StructureDefinition/Patient",
    "file_path": "data/artifacts/ps-ca/2.1.1/StructureDefinition/structuredefinition-profile-patient-ca-ps.json"
  },
  "counts": {
    "must_support_paths": 13,
    "bindings": 0,
    "constraints": 1
  },
  "top_limit": 10,
  "top": {
    "must_support_paths": [
      {
        "path": "Patient.address.city",
        "min": null,
        "max": null
      },
      {
        "path": "Patient.address.country",
        "min": null,
        "max": null
      },
      {
        "path": "Patient.address.line",
        "min": null,
        "max": null
      },
      {
        "path": "Patient.address.postalCode",
        "min": null,
        "max": null
      },
      {
        "path": "Patient.birthDate",
        "min": 1,
        "max": null
      },
      {
        "path": "Patient.gender",
        "min": null,
        "max": null
      },
      {
        "path": "Patient.name",
        "min": 1,
        "max": null
      },
      {
        "path": "Patient.name.family",
        "min": null,
        "max": null
      },
      {
        "path": "Patient.name.given",
        "min": null,
        "max": null
      },
      {
        "path": "Patient.name.text",
        "min": null,
        "max": null
      }
    ],
    "must_support_paths_paths": [
      "Patient.address.city",
      "Patient.address.country",
      "Patient.address.line",
      "Patient.address.postalCode",
      "Patient.birthDate",
      "Patient.gender",
      "Patient.name",
      "Patient.name.family",
      "Patient.name.given",
      "Patient.name.text"
    ],
    "bindings": [],
    "constraints": [
      {
        "path": "Patient.name",
        "key": "core-pat-1",
        "severity": "error",
        "human": "Either Patient.name.given and/or Patient.name.family and/or Patient.name.text SHALL be present or a Data Absent Reason Extension SHALL be present.",
        "expression": "(family.exists() or given.exists() or text.exists()) xor extension.where(url='http://hl7.org/fhir/StructureDefinition/data-absent-reason').exists()",
        "source": "differential"
      }
    ]
  },
  "has_more": {
    "must_support_paths": true,
    "bindings": false,
    "constraints": false
  },
  "generated_at": "2026-02-06T15:34:42.081225+00:00"
}
```

The summary shows that the Patient (PS-CA) profile has 13 mustSupport paths (though only the first 10 are shown due to the top_limit), no bindings, and 1 constraint. The constraint requires that a patient name must have at least one of: given name, family name, or text, or alternatively have a data-absent-reason extension.