# Prompt

“Act as a PS-CA conformance analyst. Do not answer from memory. Use the PS-CA MCP tools and include evidence from their JSON outputs.

1. Call psca_must_support for the PS-CA Patient profile:
canonical = http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps
Summarize the top 8 must-support paths and why they matter.
2. Call psca_constraints for that same Patient profile (no path filter).
Identify the 3 most important constraints/invariants and explain each in plain language.
3. Call psca_bindings for the PS-CA AllergyIntolerance profile at:
canonical = http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/allergyintolerance-ca-ps
path = AllergyIntolerance.code
Report the binding strength and ValueSet canonical, and whether the evidence came from differential or snapshot.
4. Call psca_where_used_value_set for the ValueSet canonical you just retrieved in step 3.
Return the ‘blast radius’: list every profile + element path + binding strength where it’s used.


Finally, produce a short ‘Implementation & Testing Plan’ with:

* 5 recommended vendor validation checks (derived only from must-support, constraints, and bindings you retrieved)
* 3 suggested UAT tests a business team could run
* A brief note on risk: what breaks if that ValueSet changes (based on the where-used results).


Formatting:

* Start with a one-paragraph executive summary.
* Then include four sections (Must Support, Constraints, Binding, Where-Used).
* Under each section, paste the key JSON fields you relied on (not the entire payload).”

# Response from AI

I'll act as a PS-CA conformance analyst and use the MCP tools to gather evidence, then produce the analysis you've requested.

## Step 1: Must Support Paths for PS-CA Patient Profile## Step 2: Constraints for PS-CA Patient Profile## Step 3: Bindings for PS-CA AllergyIntolerance Profile## Step 4: Where-Used Analysis for the ValueSet---

# PS-CA Patient & AllergyIntolerance Conformance Analysis

## Executive Summary

This analysis examines the PS-CA Patient and AllergyIntolerance profiles using structured queries against the PS-CA implementation guide (version 2.1.1). The Patient profile mandates 13 must-support elements focused on demographics (name, birth date, gender) and contact information (address, telecom), with one critical constraint ensuring name data completeness. The AllergyIntolerance profile binds its code element to the Infoway pharmaceutical/biologic product ValueSet with preferred strength, affecting only this single profile element. Key implementation risks include incomplete name data validation, missing must-support fields in vendor systems, and potential terminology gaps if the ValueSet evolves. Testing should focus on name constraint edge cases, must-support field population, and code system alignment.

---

## 1. Must Support Analysis: PS-CA Patient Profile

### Evidence Retrieved
```json
{
  "profile": {
    "canonical_url": "http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps",
    "name": "PatientPSCA"
  },
  "must_support_paths": [
    {"path": "Patient.name", "min": 1},
    {"path": "Patient.name.family"},
    {"path": "Patient.name.given"},
    {"path": "Patient.name.text"},
    {"path": "Patient.birthDate", "min": 1},
    {"path": "Patient.gender"},
    {"path": "Patient.address.line"},
    {"path": "Patient.address.city"},
    {"path": "Patient.address.postalCode"},
    {"path": "Patient.address.country"},
    {"path": "Patient.telecom.system"},
    {"path": "Patient.telecom.use"},
    {"path": "Patient.telecom.value"}
  ]
}
```

### Top 8 Must-Support Paths & Their Significance

1. **Patient.name** (min=1) – **Required patient identification**: Systems must capture at least one name to identify the patient. This is the foundation for patient matching and record linkage across Canadian health systems.

2. **Patient.birthDate** (min=1) – **Required demographic anchor**: Birth date is mandatory and critical for age-based clinical decision support, pediatric vs. adult protocols, and patient matching algorithms.

3. **Patient.name.family** – **Surname for matching**: Family name supports patient search and matching. Many Canadian jurisdictions use family name as a primary matching key.

4. **Patient.name.given** – **First name for identification**: Given name(s) complement family name for complete patient identification and reduce false matches.

5. **Patient.name.text** – **Display name fallback**: Supports cultures where structured given/family decomposition doesn't apply (e.g., Indigenous names, single-word names).

6. **Patient.gender** – **Clinical context**: Gender affects clinical protocols (e.g., pregnancy screening, gender-specific reference ranges) and supports demographic reporting requirements.

7. **Patient.address.postalCode** – **Geographic linkage**: Postal code enables public health surveillance, regional care coordination, and proximity-based provider searches.

8. **Patient.telecom.value** – **Contact capability**: Phone/email contact information is essential for appointment reminders, lab result notifications, and continuity of care.

---

## 2. Constraints Analysis: PS-CA Patient Profile

### Evidence Retrieved
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

### Top 3 Constraints (Only 1 Returned)

**Constraint core-pat-1** (severity: error)

**Plain Language Explanation**: Every patient name must contain at least one of the following: a family name, a given name, or a full text representation of the name. If none of these can be provided (for example, if the patient is unidentified or anonymous), systems must explicitly declare why the name is absent using a standardized "data absent reason" extension. This is an exclusive-or (xor) relationship—you provide name components OR a data-absent reason, but not both.

**Why It Matters**: This constraint prevents systems from creating patient records with completely blank names while allowing for legitimate edge cases (e.g., unidentified trauma patients, newborns not yet named). It forces explicit documentation of why name data is missing rather than silent omission.

**Implementation Impact**: Validators must check that at least one name component exists OR that the data-absent-reason extension is present. Systems cannot pass validation with an empty name element that lacks the extension.

---

## 3. Binding Analysis: PS-CA AllergyIntolerance Profile

### Evidence Retrieved
```json
{
  "profile": {
    "canonical_url": "http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/allergyintolerance-ca-ps",
    "name": "AllergyIntolerancePSCA",
    "sd_type": "AllergyIntolerance"
  },
  "path": "AllergyIntolerance.code",
  "bindings": [
    {
      "strength": "preferred",
      "value_set": "https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode",
      "source": "differential"
    }
  ]
}
```

### Binding Details

- **Element Path**: AllergyIntolerance.code
- **Binding Strength**: **preferred** (not required/extensible)
- **ValueSet Canonical**: `https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode`
- **Evidence Source**: differential (explicitly defined in the PS-CA profile differential, not inherited from base FHIR)

**Interpretation**: Systems SHOULD use codes from this Infoway pharmaceutical/biologic ValueSet when coding allergies, but MAY use codes from other systems if the appropriate concept isn't available in the preferred set. "Preferred" binding allows flexibility for edge cases (rare allergens, environmental triggers) while encouraging standardization on Canadian-managed terminology.

---

## 4. Where-Used Analysis: Blast Radius Assessment

### Evidence Retrieved
```json
{
  "value_set": "https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode",
  "usages": [
    {
      "profile": {
        "canonical_url": "http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/allergyintolerance-ca-ps",
        "name": "AllergyIntolerancePSCA",
        "sd_type": "AllergyIntolerance"
      },
      "path": "AllergyIntolerance.code",
      "strength": "preferred",
      "source": "differential"
    }
  ]
}
```

### Blast Radius Report

**Total Usages**: 1 profile element

| Profile | Element Path | Binding Strength | Source |
|---------|--------------|------------------|--------|
| AllergyIntolerancePSCA | AllergyIntolerance.code | preferred | differential |

**Impact Assessment**: This ValueSet has a **narrow blast radius**—it affects only a single element in a single profile. Changes to the ValueSet (adding/deprecating codes, restructuring hierarchies) will impact allergy/intolerance coding but won't cascade across multiple profiles or resources.

---

# Implementation & Testing Plan

## Vendor Validation Checks (Derived from Evidence)

1. **Must-Support Field Population Check**  
   *Evidence: 13 must-support paths identified*  
   Verify that systems can persist and retrieve all must-support elements: `Patient.name` (family, given, text), `birthDate`, `gender`, `address` (line, city, postalCode, country), `telecom` (system, use, value). Test with sample records ensuring no must-support field is silently dropped.

2. **Name Constraint Validation (core-pat-1)**  
   *Evidence: constraint requires name component OR data-absent-reason*  
   Submit test patients with: (a) only family name, (b) only given name, (c) only text name, (d) empty name with data-absent-reason extension. All should pass. Submit patient with completely empty name—must fail validation.

3. **BirthDate & Name Cardinality Enforcement**  
   *Evidence: min=1 on Patient.birthDate and Patient.name*  
   Attempt to create Patient resource without birthDate—must fail. Attempt to create Patient without any name element—must fail. These are mandatory fields per the profile.

4. **AllergyIntolerance Code ValueSet Alignment**  
   *Evidence: preferred binding to Infoway pharmaceutical/biologic VS*  
   Test allergy coding with: (a) codes from the Infoway ValueSet (should validate cleanly), (b) SNOMED allergy codes not in the ValueSet (should validate with warning/info since binding is preferred, not required). Confirm system doesn't reject valid out-of-ValueSet codes.

5. **Telecom System/Value Pairing**  
   *Evidence: telecom.system, telecom.use, telecom.value all must-support*  
   Verify that when telecom is provided, system can capture system (phone/email/etc.), use (home/work/mobile), and value together. Test edge case: telecom.value without telecom.system—should fail base FHIR invariant.

---

## User Acceptance Testing (UAT) Scenarios

1. **Patient Registration with Minimal Data**  
   *Business user registers new patient with only: family name "Smith", birth date "1985-06-15", gender "female". System should accept and display this record. Verifies must-support minimums are sufficient for real workflow.*

2. **Allergy Entry with Preferred Code**  
   *Clinician enters penicillin allergy, selects code from Infoway pharmaceutical ValueSet. System should save without warnings. Clinician then enters obscure environmental allergy (e.g., "mango latex"), selects SNOMED code not in Infoway VS. System should save and possibly show info note about non-preferred code but not block entry. Verifies preferred binding supports real clinical scenarios.*

3. **Anonymous Patient Handling**  
   *Registration clerk creates record for unidentified ER patient. Leaves name.family, name.given, name.text blank but adds data-absent-reason extension with reason="unknown". System should accept. Verifies constraint core-pat-1 supports legitimate edge cases without breaking validation.*

---

## Risk Assessment: ValueSet Change Impact

**If `pharmaceuticalbiologicproductandsubstancecode` ValueSet Changes:**

**Low-Medium Risk** due to narrow blast radius (only AllergyIntolerance.code in PS-CA) and preferred binding strength.

- **Code Deprecation**: If Infoway deprecates a pharmaceutical code currently in use, systems can continue using it (preferred binding allows out-of-ValueSet codes). Impact: users may see validation warnings but data remains valid.
  
- **Code Addition**: New allergens added to ValueSet improve standardization but don't break existing data. Impact: minimal, positive alignment.

- **Structural Change**: If ValueSet moves to different code system (e.g., RxNorm to something else), implementers should review but aren't forced to migrate existing data. Impact: moderate effort to update preferred picklists, but no data invalidity.

**Mitigation**: Monitor Infoway ValueSet release notes; preferred binding provides buffer time for code system transitions without breaking production systems.