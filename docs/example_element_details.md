# Prompt

Use psca_element_details for canonical http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/allergyintolerance-ca-ps and path AllergyIntolerance.code. Show the returned JSON.

# Response

I'll use the `psca_bindings` tool to get the element details for the AllergyIntolerance.code path.Here's the returned JSON from the `psca_bindings` tool for the AllergyIntolerance.code element:

```json
{
  "query_id": "PSCA-GQ-BIND-01",
  "question": "List bindings for path",
  "scope": {
    "ig": "ps-ca",
    "ig_version": "2.1.1"
  },
  "profile": {
    "canonical_url": "http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/allergyintolerance-ca-ps",
    "version": null,
    "name": "AllergyIntolerancePSCA",
    "sd_type": "AllergyIntolerance",
    "file_path": "data/artifacts/ps-ca/2.1.1/StructureDefinition/structuredefinition-profile-allergyintolerance-ca-ps.json"
  },
  "path": "AllergyIntolerance.code",
  "bindings": [
    {
      "strength": "preferred",
      "value_set": "https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode",
      "source": "differential"
    }
  ],
  "generated_at": "2026-02-06T15:55:20.369127+00:00"
}
```

This shows that the AllergyIntolerance.code element has a preferred binding to the Pharmaceutical/Biologic Product and Substance Code value set.