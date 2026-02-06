# Prompt

Use the psca_bindings tool with canonical
http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/allergyintolerance-ca-ps
and path AllergyIntolerance.code. Show me the JSON result.

# Response form AI

I'll use the psca_bindings tool to get the bindings for that specific path.Here's the JSON result from the psca_bindings tool:

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
  "generated_at": "2026-02-05T23:33:39.984770+00:00"
}
```

The result shows that the `AllergyIntolerance.code` element has a **preferred** binding to the value set `https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode`, which is defined in the differential of the PS-CA AllergyIntolerance profile.

# Prompt

“Using the PS-CA tools, list the must-support elements for the PS-CA Patient profile. Then summarize what a vendor must implement in plain language.”

# Response

I'll use the psca_must_support tool to get the must-support elements for the PS-CA Patient profile.## Must-Support Elements for PS-CA Patient Profile

Here are the must-support paths:

```json
{
  "must_support_paths": [
    { "path": "Patient.address.city" },
    { "path": "Patient.address.country" },
    { "path": "Patient.address.line" },
    { "path": "Patient.address.postalCode" },
    { "path": "Patient.birthDate", "min": 1 },
    { "path": "Patient.gender" },
    { "path": "Patient.name", "min": 1 },
    { "path": "Patient.name.family" },
    { "path": "Patient.name.given" },
    { "path": "Patient.name.text" },
    { "path": "Patient.telecom.system" },
    { "path": "Patient.telecom.use" },
    { "path": "Patient.telecom.value" }
  ]
}
```

# Plain Language Summary for Vendors

When implementing the PS-CA Patient profile, vendors must be able to:

**Required Elements** (must always be present):
- **Birth date** - The patient's date of birth must always be captured
- **Name** - At least one name must be provided

**Must-Support Elements** (must be able to store, retrieve, and display):

1. **Patient Name** - Support capturing and displaying:
   - Family name (last name)
   - Given name(s) (first/middle names)
   - Full text representation of the name

2. **Address Information** - Support all components of a patient's address:
   - Street address lines
   - City
   - Postal/ZIP code
   - Country

3. **Contact Information** - Support telephone/email contact details including:
   - The actual contact value (phone number, email address)
   - The type of contact (phone, email, etc.)
   - How it should be used (home, work, mobile, etc.)

4. **Gender** - Support recording the patient's administrative gender

In practical terms, if your system receives Patient data with any of these must-support elements populated, you must be able to store them and return them when queried. If you're creating Patient resources, you should populate these elements when the information is available.

# Prompt

“Show me every constraint (invariant) that applies to the PS-CA Patient profile. Explain the top 3 constraints in business terms (what problem each prevents).”

I'll use the psca_constraints tool to get all the constraints for the PS-CA Patient profile.## All Constraints for PS-CA Patient Profile

There is **1 constraint** that applies to the PS-CA Patient profile:

```json
{
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
}
```

## Business Explanation of the Constraint

**Constraint: core-pat-1 (Patient Name Requirement)**

**What it prevents:** This constraint prevents the creation of patient records with completely empty or useless name information.

**The business problem it solves:**

In healthcare systems, being able to identify a patient by name is fundamental for safety and operations. This constraint ensures that you can't create a patient record without *some* meaningful name information. 

Specifically, it requires that when you create a patient name entry, you must provide at least one of:
- A **given name** (first name), OR
- A **family name** (last name), OR  
- A **text representation** of the full name

**However**, the constraint recognizes that in rare cases, name information might genuinely be unavailable (for example, an unidentified trauma patient or a newborn not yet named). In those cases, you can skip the name details BUT you must explicitly indicate *why* the name is missing using a "data absent reason" extension.

**Real-world impact:** This prevents errors like accidentally saving a blank name field, while still allowing flexibility for edge cases where names are legitimately unknown. It ensures every patient record has either usable name data or a documented reason why it's absent, which is critical for patient safety and record management.