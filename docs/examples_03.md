# Prompt

“I’m reviewing an implementation and want to know what’s actually required vs just ‘nice’. For the PS-CA AllergyIntolerance profile, list must-support paths and any constraints. Then tell me what I should test first.”

# Response

I'll get the must-support elements and constraints for the PS-CA AllergyIntolerance profile.## PS-CA AllergyIntolerance Profile - Implementation Requirements

### Must-Support Elements

```json
{
  "must_support_paths": [
    {
      "path": "AllergyIntolerance.code",
      "min": 1,
      "max": "1"
    },
    {
      "path": "AllergyIntolerance.onsetDateTime",
      "min": null,
      "max": null
    },
    {
      "path": "AllergyIntolerance.patient",
      "min": null,
      "max": null
    },
    {
      "path": "AllergyIntolerance.patient.reference",
      "min": 1,
      "max": null
    },
    {
      "path": "AllergyIntolerance.reaction",
      "min": null,
      "max": null
    },
    {
      "path": "AllergyIntolerance.reaction.manifestation",
      "min": null,
      "max": null
    }
  ]
}
```

### Constraints
**No additional constraints** found for this profile beyond standard FHIR base constraints.

---

## What's Actually Required vs Nice-to-Have

### **REQUIRED (Must Always Be Present):**
1. **AllergyIntolerance.code** - The substance/allergen that causes the allergy (min=1, max=1)
2. **AllergyIntolerance.patient.reference** - A reference to which patient has this allergy (min=1)

### **Must-Support (Must Handle If Present):**
3. **AllergyIntolerance.onsetDateTime** - When the allergy started
4. **AllergyIntolerance.reaction** - Details about reactions that have occurred
5. **AllergyIntolerance.reaction.manifestation** - How the reaction presented (symptoms)

---

## Testing Priority - What to Test First

### **Priority 1: Critical Path Testing** ✅
Test these first - they'll break the profile if wrong:

1. **Code validation** - Create an AllergyIntolerance WITHOUT a code field → should FAIL
2. **Patient reference validation** - Create an AllergyIntolerance WITHOUT a patient reference → should FAIL
3. **Code cardinality** - Try to include multiple codes → should FAIL (max=1)
4. **Valid minimal record** - Create with just code + patient.reference → should SUCCEED

### **Priority 2: Must-Support Handling** 📋
Test that your system can handle these when present:

5. **Store and retrieve onsetDateTime** - Add onset date, save, retrieve → verify it's preserved
6. **Store and retrieve reaction data** - Add reaction with manifestation, save, retrieve → verify it's preserved
7. **Display all must-support elements** - Ensure your UI can show all these fields when populated

### **Priority 3: Real-World Scenarios** 🌍
8. **Code binding validation** - Use codes from the preferred ValueSet (pharmaceutical/biological product codes)
9. **Multiple reactions** - Test with multiple reaction entries (if your use case requires it)
10. **Update scenarios** - Test updating existing allergy records while maintaining required fields

### **Quick Validation Script Example:**
```
Test Case 1: Missing code → FAIL ❌
Test Case 2: Missing patient.reference → FAIL ❌
Test Case 3: Minimal valid (code + patient) → PASS ✅
Test Case 4: Full record with all must-support → PASS ✅
Test Case 5: Retrieve and verify must-support data preserved → PASS ✅
```

**Bottom line:** Start with the two required fields (code and patient.reference), then expand to must-support elements. Since there are no custom constraints, you mainly need to focus on cardinality and must-support compliance.

# Prompt

“For allergyintolerance-ca-ps, show the binding for AllergyIntolerance.code. Include strength, ValueSet canonical, and whether it came from differential or snapshot.”

# Response

I'll get the binding information for AllergyIntolerance.code from the PS-CA AllergyIntolerance profile.## Binding for AllergyIntolerance.code

```json
{
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

### Summary

- **Element:** `AllergyIntolerance.code`
- **Binding Strength:** `preferred`
- **ValueSet Canonical:** `https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode`
- **Source:** `differential` (defined by the PS-CA profile, not inherited from base FHIR)

### What This Means

Since the binding strength is **"preferred"**, implementers:
- **SHOULD** use codes from the Pharmaceutical/Biological Product and Substance Code ValueSet when possible
- **CAN** use codes from other code systems if the required concept isn't available in the preferred ValueSet
- Will still pass validation even if using codes outside this ValueSet, but using codes from this ValueSet is the recommended practice for PS-CA conformance

This is less restrictive than "required" (which would force you to use only these codes) but more guidance than "example" (which would just be a suggestion).

# Prompt

“Give me a ‘compliance evidence bundle’ for:

* Profile: PS-CA AllergyIntolerance
* Path: AllergyIntolerance.code
Include binding, strength, and the ValueSet URL.”

I'll create a compliance evidence bundle for the PS-CA AllergyIntolerance profile, specifically for the AllergyIntolerance.code path.# 📋 COMPLIANCE EVIDENCE BUNDLE

## Profile Information
- **Profile Name:** AllergyIntolerancePSCA
- **Canonical URL:** `http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/allergyintolerance-ca-ps`
- **Implementation Guide:** PS-CA (PrescribeIT - Canada)
- **IG Version:** 2.1.1
- **Resource Type:** AllergyIntolerance

---

## Element Under Review
**Path:** `AllergyIntolerance.code`

---

## 🎯 COMPLIANCE REQUIREMENTS

### 1. Cardinality
- **Minimum:** `1` (REQUIRED)
- **Maximum:** `1` (exactly one)
- **Interpretation:** This element is **mandatory** - every PS-CA AllergyIntolerance resource MUST have exactly one code
- **Source:** Differential (defined by PS-CA profile)

### 2. Must-Support Status
- **Must-Support:** ✅ **YES**
- **Obligation:** Systems must be able to:
  - Store this element when received
  - Retrieve this element when queried
  - Display this element in user interfaces
  - Populate this element when creating resources

### 3. Terminology Binding
- **Binding Strength:** `preferred`
- **ValueSet Canonical URL:** `https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode`
- **ValueSet Name:** Pharmaceutical/Biological Product and Substance Code
- **Source:** Differential (defined by PS-CA profile)

### 4. Constraints/Invariants
- **Custom Constraints:** None
- **Note:** Element follows base FHIR AllergyIntolerance.code constraints only

---

## ✅ COMPLIANCE CHECKLIST

### Implementation Requirements

- [ ] **Store capability:** Can store AllergyIntolerance.code (1..1 cardinality)
- [ ] **Retrieve capability:** Can return AllergyIntolerance.code in query responses
- [ ] **Display capability:** UI shows the allergy/substance code to users
- [ ] **Validation:** System rejects AllergyIntolerance resources without a code
- [ ] **Validation:** System rejects AllergyIntolerance resources with multiple codes
- [ ] **Preferred coding:** System uses codes from the Pharmaceutical/Biological Product ValueSet when available
- [ ] **Fallback coding:** System can accept codes from other systems if preferred ValueSet doesn't contain the needed concept

### Testing Scenarios

**Test 1: Missing Code (MUST FAIL)**
```json
{
  "resourceType": "AllergyIntolerance",
  "patient": { "reference": "Patient/123" }
  // Missing code element
}
```
Expected: ❌ Validation error

**Test 2: Valid Code from Preferred ValueSet (MUST PASS)**
```json
{
  "resourceType": "AllergyIntolerance",
  "patient": { "reference": "Patient/123" },
  "code": {
    "coding": [{
      "system": "https://fhir.infoway-inforoute.ca/CodeSystem/...",
      "code": "...",
      "display": "Penicillin"
    }]
  }
}
```
Expected: ✅ Valid

**Test 3: Code from Alternative System (SHOULD PASS)**
```json
{
  "resourceType": "AllergyIntolerance",
  "patient": { "reference": "Patient/123" },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "91936005",
      "display": "Allergy to penicillin"
    }]
  }
}
```
Expected: ✅ Valid (preferred binding allows alternatives)

**Test 4: Multiple Codes (MUST FAIL)**
```json
{
  "resourceType": "AllergyIntolerance",
  "patient": { "reference": "Patient/123" },
  "code": {...},
  "code": {...}  // Second code element
}
```
Expected: ❌ Validation error (max cardinality = 1)

---

## 📊 BINDING STRENGTH INTERPRETATION

**"Preferred" Binding Means:**
- ✅ **Recommended:** Use codes from the specified ValueSet when possible
- ✅ **Flexible:** Can use codes from other code systems if the concept isn't in the preferred ValueSet
- ✅ **Valid:** Resources with codes outside the ValueSet still validate
- ⚠️ **Best Practice:** Prefer the specified ValueSet for maximum interoperability

**Contrast with other binding strengths:**
- **Required:** MUST use codes only from the specified ValueSet
- **Extensible:** SHOULD use from ValueSet, but can extend if necessary
- **Example:** Just a suggestion, no enforcement

---

## 📁 EVIDENCE SOURCES

All compliance requirements extracted from:
- **File Path:** `data/artifacts/ps-ca/2.1.1/StructureDefinition/structuredefinition-profile-allergyintolerance-ca-ps.json`
- **Query Date:** 2026-02-05T23:38:25.067256+00:00
- **Evidence Type:** Differential (profile-specific requirements, not base FHIR)

---

## 🎓 SUMMARY FOR AUDITORS

The `AllergyIntolerance.code` element in PS-CA:
1. Is **mandatory** (must be present, exactly once)
2. Is **must-support** (systems must handle it)
3. Should use the **Pharmaceutical/Biological Product ValueSet** (preferred binding)
4. Has **no additional custom constraints** beyond base FHIR

**Compliance Risk:** HIGH - Missing this element or having multiple codes will cause validation failures.