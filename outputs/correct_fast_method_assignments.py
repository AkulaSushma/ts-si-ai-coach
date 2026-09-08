import json
import os

INTEL_DIR = "pyq/intelligence"

# Load questions
with open(os.path.join(INTEL_DIR, "questions.json")) as f:
    questions = json.load(f)

# Define which questions should keep their family's candidate fast method
# Mapping: question_id -> (candidate_method_id, new_state)
# For these, we will set state to UNVERIFIED_FAST_METHOD (will be promoted later)
FAST_KEEP = {
    "Q-PYQ-010016": "MET-PYQ-0033",  # ratio-cubes
    "Q-PYQ-010007": "MET-PYQ-0030",  # CI-SI 2-year
    "Q-PYQ-010029": "MET-PYQ-0031",  # equal SP gain/loss
    "Q-PYQ-010030": "MET-PYQ-0032",  # successive discounts
    "Q-PYQ-020028": "MET-PYQ-0034",  # still-water mean
}

# Families that have candidate fast methods
FAST_FAMILIES = {
    "FAM-PYQ-0004": "MET-PYQ-0033",
    "FAM-PYQ-0009": "MET-PYQ-0030",
    "FAM-PYQ-0010": ["MET-PYQ-0031", "MET-PYQ-0032"],  # two candidates
    "FAM-PYQ-0014": "MET-PYQ-0034",
}

# Load families to know which question belongs to which family
with open(os.path.join(INTEL_DIR, "families.json")) as f:
    families = json.load(f)
fam_by_id = {f["family_id"]: f for f in families}

# For each question, if it belongs to a fast family and is NOT in FAST_KEEP, clear candidate
updated = 0
for q in questions:
    if q.get("unresolved", False):
        continue
    fid = q.get("question_family_id")
    if fid not in FAST_FAMILIES:
        continue
    qid = q["question_id"]
    if qid in FAST_KEEP:
        # Keep candidate, ensure state is UNVERIFIED_FAST_METHOD (for now)
        if q["candidate_fast_method_id"] != FAST_KEEP[qid]:
            q["candidate_fast_method_id"] = FAST_KEEP[qid]
            updated += 1
        if q["fast_method_state"] != "UNVERIFIED_FAST_METHOD":
            q["fast_method_state"] = "UNVERIFIED_FAST_METHOD"
            updated += 1
    else:
        # Clear candidate
        if q["candidate_fast_method_id"] is not None:
            q["candidate_fast_method_id"] = None
            updated += 1
        if q["fast_method_state"] != "NO_FAST_METHOD_FOUND":
            q["fast_method_state"] = "NO_FAST_METHOD_FOUND"
            updated += 1
        # Also clear fast_method_verified_id if any
        if q.get("fast_method_verified_id") is not None:
            q["fast_method_verified_id"] = None
            updated += 1

print(f"Updated {updated} fields across questions.")

# Write back
with open(os.path.join(INTEL_DIR, "questions.json"), "w") as f:
    json.dump(questions, f, indent=1)

print("Correction complete. The following questions retain candidate fast methods:")
for qid, mid in FAST_KEEP.items():
    print(f"  {qid} -> {mid}")