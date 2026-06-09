#!/usr/bin/env python3
"""Run all 52 scenarios through updated ethics filter with module relevance."""
import json, os

BASE = os.path.expanduser("~/.hermes/skills/ethics-filter")
with open(BASE + "/tests/scenarios_v2.json") as f:
    scenarios = json.load(f)
with open(BASE + "/constitution/templates.json") as f:
    templates = json.load(f)

# Module relevance engine (same as in scenarios_v2.py)
MODULE_RELEVANCE = {
    "environmental": {"relevant_when": [
        "physical resources", "manufacturing", "transport", "energy",
        "waste", "packaging", "supply chain", "travel", "raw materials",
        "chemicals", "emissions", "water", "land use", "construction",
        "product design", "sourcing", "fossil fuels", "renewable",
        "shipping", "fleet", "facilities", "office", "hardware",
        "food production", "agriculture", "forestry", "mining",
        "carbon", "footprint", "recycling", "plastic", "sustainable",
        "eco", "environment", "climate", "co2", "green", "pollution"
    ]},
    "fairness": {"relevant_when": [], "exclude_when": [
        "purely personal preference",
        "trivial internal decision affecting only the decision-maker",
        "no external stakeholders",
        "no other people affected",
        "affects only the decision-maker"
    ]},
    "transparency": {"relevant_when": [], "exclude_when": [
        "trivial personal preference without consequences",
        "purely personal preference",
        "no external stakeholders",
        "no deeper implications",
        "no wrong choice"
    ]},
    "conscious-leadership": {"relevant_when": [
        "values", "purpose", "long-term", "leadership", "culture",
        "team", "integrity", "dilemma", "difficult choice", "character",
        "role model", "conflict", "change management", "strategy",
        "hiring", "firing", "conversation", "accountability", "growth",
        "relationship", "family", "friend", "community", "care",
        "apology", "amends", "promotion", "career", "values",
        "ethical", "morals", "principle", "responsibility", "trust"
    ]},
    "ethical-framework": {"relevant_when": []},
    "compliance": {"relevant_when": [
        "legal", "regulation", "certification", "contract", "audit",
        "tax", "reporting", "license", "permit", "standard",
        "policy", "law", "compliance", "governance", "board",
        "disclosure", "filing", "statutory", "obligation",
        "b corp", "iso", "organic", "fair trade", "accredited",
        "employment", "privacy", "gdpr", "financial", "industry standard",
        "illegal", "crime", "unlawful", "toxic", "hazardous",
        "inspection", "regulatory", "statute", "liability",
        "negligence", "due diligence", "fiduciary", "oversight",
        "safety violation", "structural risk", "building code"
    ]}
}

def check_relevance(action, context, module):
    info = MODULE_RELEVANCE.get(module, {})
    text = (action + " " + context).lower()
    if not info.get("relevant_when"):
        for exclude in info.get("exclude_when", []):
            if exclude.lower() in text:
                return False
        return True
    return any(kw.lower() in text for kw in info["relevant_when"])

def get_enabled(action, context, preset):
    modules = preset.get("modules", {})
    text = (action + " " + context).lower()
    enabled = []
    for mod, active in modules.items():
        if not active:
            continue
        if mod == "ethical-framework":
            enabled.append(mod)
            continue
        if check_relevance(action, context, mod):
            enabled.append(mod)
    return enabled

def evaluate_scenario(sc):
    action = sc["action"]
    context = sc["context"]
    preset = templates["presets"].get(sc["constitution"], templates["presets"]["maximalist"])
    strictness = preset.get("strictness", "moderate")
    thresholds = templates["strictness_levels"].get(strictness)
    
    enabled = get_enabled(action, context, preset)
    pre_scores = sc["module_scores"]
    scores = {m: pre_scores[m] for m in enabled if m in pre_scores}
    
    if not scores:
        return None
    
    overall = sum(scores.values()) / len(scores)
    red_t = thresholds["red_threshold"]
    green_t = thresholds["green_threshold"]
    
    if overall < red_t:
        decision = "red"
    elif overall >= green_t:
        decision = "green"
    else:
        decision = "amber"
    
    flags = {"red": [], "amber": [], "green": []}
    for mod, score in scores.items():
        if score < red_t:
            flags["red"].append(mod)
        elif score >= green_t:
            flags["green"].append(mod)
        else:
            flags["amber"].append(mod)
    
    # Check expected outcome
    exp = sc.get("expected_range", {})
    score_ok = exp.get("overall_min", 0) <= overall <= exp.get("overall_max", 100)
    dec_ok = decision == exp.get("expected_decision", "")
    
    return {
        "id": sc["id"],
        "category": sc["category"],
        "title": sc["title"],
        "enabled": enabled,
        "scores": scores,
        "overall": round(overall, 1),
        "strictness": strictness,
        "decision": decision,
        "flags": flags,
        "score_ok": score_ok,
        "dec_ok": dec_ok
    }

# Run all
results = []
for sc in scenarios:
    r = evaluate_scenario(sc)
    if r:
        results.append(r)

# Save
with open(BASE + "/tests/results_v2.json", "w") as f:
    json.dump(results, f, indent=2)

# Print summary
print(f"\n{'='*70}")
print(f"  ETHICS FILTER v2 — FULL TEST RESULTS ({len(results)} evaluations)")
print(f"{'='*70}")

categories = {}
for r in results:
    cat = r["category"]
    if cat not in categories:
        categories[cat] = {"total": 0, "green": 0, "amber": 0, "red": 0, "score_ok": 0, "dec_ok": 0}
    categories[cat]["total"] += 1
    categories[cat][r["decision"]] += 1
    if r["score_ok"]:
        categories[cat]["score_ok"] += 1
    if r["dec_ok"]:
        categories[cat]["dec_ok"] += 1

all_g = sum(c["green"] for c in categories.values())
all_a = sum(c["amber"] for c in categories.values())
all_r = sum(c["red"] for c in categories.values())
all_so = sum(c["score_ok"] for c in categories.values())
all_do = sum(c["dec_ok"] for c in categories.values())
all_t = sum(c["total"] for c in categories.values())

print(f"\n{'Category':<30} {'Total':>5} {'GREEN':>6} {'AMBER':>6} {'RED':>6} {'ScoreOK':>7} {'DecOK':>6}")
print(f"{'-'*66}")
for cat in sorted(categories.keys()):
    c = categories[cat]
    print(f"{cat:<30} {c['total']:>5} {c['green']:>6} {c['amber']:>6} {c['red']:>6} {c['score_ok']:>7} {c['dec_ok']:>6}")
print(f"{'-'*66}")
print(f"{'TOTAL':<30} {all_t:>5} {all_g:>6} {all_a:>6} {all_r:>6} {all_so:>7} {all_do:>6}")

print(f"\n{'='*70}")
print(f"  DETAILED RESULTS")
print(f"{'='*70}")
print(f"{'ID':<6} {'Decision':<8} {'Score':<7} {'Enabled':<40} {'Flags'}")
print(f"{'-'*70}")

high_green = [r for r in results if r["decision"] == "green" and r["overall"] >= 90]
print(f"\n--- HIGHEST GREEN SCORES (90+) ---")
for r in sorted(high_green, key=lambda x: -x["overall"]):
    flag_str = ", ".join(r["flags"]["red"] + r["flags"]["amber"]) if any(r["flags"].values()) else "none"
    print(f"  {r['id']:<4} {r['title'][:50]} — {r['overall']}")

print(f"\n--- MODULE RELEVANCE (showing which modules fired per decision) ---")
for r in results:
    if r["category"] in ["everyday-trivial", "relevance-test"]:
        print(f"  {r['id']:<4} {r['title'][:45]:<45} modules: {', '.join(r['enabled']):<50} score: {r['overall']}")

print(f"\n--- FULL SCORE RANGE ---")
for r in sorted(results, key=lambda x: x["overall"]):
    print(f"  {r['id']:<4} {r['title'][:50]:<50} {r['overall']:>5.1f}  {r['decision'].upper():<6}  [{', '.join(r['enabled'])}]")

print(f"\nResults saved to: {BASE}/tests/results_v2.json")
