#!/usr/bin/env python3
"""Run all 52 scenarios through updated ethics filter with module relevance."""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "tests", "scenarios_v2.json")) as f:
    scenarios = json.load(f)
with open(os.path.join(BASE, "constitution", "templates.json")) as f:
    templates = json.load(f)

# Import engine for relevance detection and thresholds
from ethics_filter.engine import check_relevance, get_enabled_modules, get_thresholds
from ethics_filter.engine import MODULE_RELEVANCE, MODULE_NAMES


def get_enabled(action, context, preset):
    """Legacy wrapper: get list of enabled module names for a preset dict."""
    modules = preset.get("modules", {})
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
with open(os.path.join(BASE, "tests", "results_v2.json"), "w") as f:
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

print(f"\nResults saved to: tests/results_v2.json")
