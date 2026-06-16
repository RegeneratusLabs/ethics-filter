---
name: ethics-filter
description: "Use when evaluating a decision for ethical soundness across stakeholder, compliance, and values dimensions."
version: 2.0.0
author: Regeneratus Labs
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ethics, decision-framework, governance, compliance, values]
    related_skills: [ethics-skillset-architecture, deep-research]
---

# Ethics Filter — Universal Ethics Evaluation Engine

## Overview

A structured decision-evaluation engine that runs any proposed action — corporate, personal, or hybrid — through six independent ethical lenses. Each lens (module) fires only when contextually relevant. The output is a scored, auditable, reasoned evaluation with clear decision thresholds.

Tested across 52 scenarios covering 9 categories with a full score range of 5.0–100.0 and 11 scenarios scoring 90+. See the [audit report](docs/audit-report.md) for the complete results.

## When to Use

- Making decisions that affect stakeholders, communities, or the environment
- Evaluating business strategy, procurement, hiring, or product decisions
- Navigating personal choices with moral weight
- Building AI agents that need an ethical reasoning layer
- Auditing past decisions for ethical blind spots
- Ensuring compliance with legal, regulatory, or certification standards

Do not use for:
- Purely aesthetic choices with zero external impact
- Decisions already governed by a functioning ethical review board with audit trail
- Trivial daily preferences where evaluation cost exceeds decision impact
- Emergency situations requiring immediate action (evaluate post-action as audit instead)
- Decisions with no agency — where the decision-maker is mandated by law with no discretion

---

## The 6-Step Pipeline

### Step 1: Intent Clarification

Restate the proposed action in plain language. Surface ambiguity before evaluating.

```
Intent: [one sentence describing the action]
Context: [relevant background facts]
Assumptions: [anything being taken for granted]
```

### Step 2: Stakeholder Mapping

Identify every party affected by this decision:

- **Direct stakeholders** — those directly impacted
- **Indirect stakeholders** — those in the value chain
- **Systemic stakeholders** — community, environment, future generations

```
Stakeholders:
- [stakeholder]: [how they are affected]
```

### Step 3: Module Evaluation

Run the decision through each relevant module. Modules that aren't relevant are skipped entirely — a personal decision about helping a friend does not need environmental or compliance evaluation.

**Module relevance detection:**

- **Environmental** — only fires when decision involves physical resources, manufacturing, transport, energy, waste, emissions, or similar
- **Fairness** — fires for any decision affecting other people (skipped for purely personal preferences with no external impact)
- **Transparency** — fires for any non-trivial decision (skipped for trivial personal preferences without consequences)
- **Conscious Leadership** — fires for decisions with values, relationships, or moral weight
- **Ethical Framework** — always fires (the meta-ethical lens)
- **Compliance** — only fires when legal, regulatory, or certification obligations exist

Each module returns:

| Field | Type | Description |
|-------|------|-------------|
| `score` | 0–100 | Ethical score for this lens |
| `flags` | list | Specific concerns raised |
| `rationale` | string | Reasoning behind the score |
| `requires_human` | bool | True if escalation is needed |

### Step 4: Conflict Resolution

If modules disagree, resolve by:

1. **Severity triage** — compliance/legal violations override preference differences
2. **Tension flagging** — explicitly note where modules conflict
3. **Escalation** — if a critical module scores RED or requires human input

### Step 5: Decision

| Score Range | Verdict | Action |
|-------------|---------|--------|
| 80–100 | GREEN | Proceed. Log rationale. |
| 50–79 | AMBER | Proceed with caution. Flag to decision-maker. Document concerns. |
| <50 | RED | Block. Escalate to human. Full explanation required. |

### Step 6: Audit

Every evaluation produces a permanent record:

```json
{
  "timestamp": "ISO8601",
  "action": "description",
  "constitution": "which modules were enabled",
  "scores": { "module_name": 0-100, ... },
  "overall": 0-100,
  "flags": [],
  "tensions": [],
  "decision": "green/amber/red",
  "rationale": "full reasoning",
  "human_looped": false
}
```

---

## Module Reference Files

Each module has a detailed reference file with criteria, questions, scoring rubric, and edge cases:

| Module | File | Core Question |
|--------|------|---------------|
| Environmental | `modules/environmental.md` | What is the impact on the natural world? |
| Fairness | `modules/fairness.md` | Who is treated fairly or unfairly? |
| Transparency | `modules/transparency.md` | Would you publish this decision? |
| Conscious Leadership | `modules/conscious-leadership.md` | Is this from above or below the line? |
| Ethical Framework | `modules/ethical-framework.md` | What would each ethical lens say? |
| Compliance | `modules/compliance.md` | Does this breach any standard or law? |

---

## Constitution Configuration

A "constitution" is the set of modules you have enabled plus their strictness levels. Templates are in `constitution/templates.json`.

Default constitution (all modules, moderate strictness):

```json
{
  "modules": {
    "environmental": true,
    "fairness": true,
    "transparency": true,
    "conscious-leadership": true,
    "ethical-framework": true,
    "compliance": true
  },
  "strictness": {
    "default": "moderate"
  }
}
```

Strictness levels affect scoring thresholds:

| Level | RED threshold | AMBER threshold | GREEN threshold |
|-------|---------------|-----------------|-----------------|
| Relaxed | <30 | 30–70 | >70 |
| Moderate | <50 | 50–74 | >74 |
| Strict | <70 | 70–89 | >89 |

---

## Module Relevance Flowchart

```
Decision enters filter
         |
         v
  Does decision involve physical resources,
  manufacturing, transport, energy, waste?
         |                      |
        YES                    NO
         |                      |
         v                      v
  Environmental module    Does decision affect other people?
  fires                   (exclude: purely personal, no stakeholders)
                                  |                      |
                                 YES                    NO
                                  |                      |
                                  v                      v
                           Fairness module         Is decision non-trivial with
                           fires                   consequences or external impact?
                                                           |                      |
                                                          YES                    NO
                                                           |                      |
                                                           v                      v
                                                    Transparency module    Does decision involve values,
                                                    fires                  integrity, relationships,
                                                                           moral weight, or character?
                                                                                  |                      |
                                                                                 YES                    NO
                                                                                  |                      |
                                                                                  v                      v
                                                                           Conscious Leadership    Does decision have legal,
                                                                           module fires             regulatory, or certification
                                                                                                    obligations?
                                                                                                           |                      |
                                                                                                          YES                    NO
                                                                                                           |                      |
                                                                                                           v                      v
                                                                                                    Compliance module       Ethical Framework module
                                                                                                    fires                   (ALWAYS fires)
                                                                                                                                    |
                                                                                                                                    v
                                                                                                                            Aggregation -> Verdict
```

---

## Common Mistakes

1. **Applying all 6 modules when only 1-2 are relevant** — let the relevance engine gate. If the decision has no environmental impact, skip the environmental module.

2. **Confusing compliance with ethics** ("it is legal so it is fine") — a decision can be perfectly legal but deeply unethical. Compliance is one module, not the whole filter. The "borderline legal" trap (BL-04) is the most common version: structuring decisions to avoid legal definitions while producing the same harmful outcome.

3. **Treating scores as objective truth** — scores are structured thinking aids, not measurements. Two reasonable people can disagree on a score. The value is in the reasoning, not the number.

4. **Skipping stakeholder mapping** (Step 2) — this is the most skipped step and catches the most blind spots. Without it, you default to the most powerful stakeholder's perspective. The "shareholder returns at any cost" trap (BL-05) is a direct consequence.

5. **Using relaxed strictness to greenlight decisions that should be amber** — strictness should match stakes, not desired outcome.

6. **Evaluating decisions retroactively to justify them** rather than prospectively to guide them — the filter works best as a planning tool, not a post-hoc rationalization machine.

7. **Letting urgency bypass the pipeline** ("we do not have time for ethics") — the time-pressure trap (BL-02). Urgency does not absolve ethical responsibility.

8. **Assuming "obviously ethical" decisions need no evaluation** (BL-01) — the most dangerous rationalization. Seemingly obvious good deeds can have hidden stakeholder impacts or be used as reputational cover for harmful core practices.

---

## How to Use

### For Agents (programmatic)

Call the ethics filter as part of your decision loop:

> "Run this through the ethics filter before proceeding: [proposed action]. My constitution is [which modules are enabled]."

### For Humans (reflective)

Describe a decision you are facing and ask:

> "I am using the ethics filter. Evaluate this decision: [situation]. My constitution enables all modules at moderate strictness."

### For Organizations (governance)

Embed the ethics filter into approval workflows:

> "Every procurement, hiring, and marketing decision must pass through the ethics filter. Configure your constitution first, then evaluate each decision before approval."

---

## Integration

- **Python SDK** — import `EthicsEngine` from `ethics_filter.engine`
- **Hermes Agent** — load the `ethics-filter` skill to enable evaluation during decision loops
- **MCP** — call evaluation as a tool from any MCP-compatible agent (run `ethics-filter` MCP server)
- **CLI** — `ethics-filter evaluate --action "..." --context "..."`

See [docs/hermes-integration.md](docs/hermes-integration.md) and [docs/platform-setup.md](docs/platform-setup.md) for details.

---

## Verification Checklist

- [ ] Intent is clearly stated in plain language
- [ ] All stakeholders are mapped (direct, indirect, systemic)
- [ ] Module relevance is checked — only applicable modules fire
- [ ] Module conflicts are identified and resolved
- [ ] Decision threshold is applied (GREEN / AMBER / RED)
- [ ] Full evaluation is logged to audit trail
- [ ] Human escalation triggers are configured per strictness level
