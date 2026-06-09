---
name: ethics-filter
description: "The Universal Ethics Filter — a structured decision-evaluation engine for any agent, any business, any personal decision. Runs every action through 6 ethical modules and produces scored, auditable reasoning."
category: productivity
tags:
  - ethics
  - decision-making
  - governance
  - conscious-leadership
  - compliance
  - transparency
linked_files:
  - modules/environmental.md
  - modules/fairness.md
  - modules/transparency.md
  - modules/conscious-leadership.md
  - modules/ethical-framework.md
  - modules/compliance.md
  - constitution/templates.json
  - tests/test-scenarios.json
  - tests/blind-tests.json
  - references/testing-methodology.md
  - references/fairness-module-personal-context.md
  - references/research-sources.md
  - tests/scenarios_v2.json
  - tests/results_v2.json
---

# 🌐 Ethics Filter — Universal Ethics Evaluation Engine

## Overview

This skill provides a complete, structured ethics evaluation framework that any AI agent (or human) can use to evaluate decisions through 6 independent ethical lenses.

When loaded, the agent gains the ability to:
- Accept any decision or action proposal — corporate, personal, or hybrid
- Run it through the 6-step pipeline with **smart module relevance** (modules only fire when contextually applicable)
- Produce a scored, auditable, reasoned evaluation
- Flag concerns and escalate where needed

## Scope Principles (DO NOT NARROW)

This filter is **universal** — it applies to:
- **Corporate decisions**: procurement, hiring, marketing, compliance, governance, strategy
- **Personal decisions**: relationships, family, career, finance, consumption, community
- **Hybrid decisions**: whistleblowing, family business, values-aligned career choices

**Good instinct** when evaluating: start with the broadest lens and only narrow if the context demands it. Do NOT assume a decision is only relevant to small businesses, organic agriculture, or any specific domain. The moment you bias the filter toward one domain, you miss the ethical dimensions that matter most.

**Tested across 52 scenarios** (see v2 audit report) covering 9 categories — full score range 5.0–100.0, 11 scenarios scoring 90+. The filter correctly recognizes genuinely ethical behavior and catches deliberate harm regardless of domain.

---

## The 6-Step Pipeline

Every decision passes through exactly this sequence:

### Step 1: Intent Clarification
Restate the proposed action in plain language. What exactly is being proposed? Surface any ambiguity before evaluating.

Format:
```
Intent: [one sentence describing the action]
Context: [relevant background facts]
Assumptions: [anything being taken for granted]
```

### Step 2: Stakeholder Mapping
Identify every party affected by this decision, including:
- Direct stakeholders (those directly impacted)
- Indirect stakeholders (those in the value chain)
- Systemic stakeholders (community, environment, future generations)

Format:
```
Stakeholders:
- [stakeholder]: [how they are affected]
```

### Step 3: Module Evaluation
Run the decision through each **relevant** module. The system first checks whether each module applies to the decision context. Modules that aren't relevant are skipped entirely — a personal decision about helping a friend doesn't need environmental or compliance evaluation.

Each module returns:
- `score`: 0–100
- `flags`: list of concerns
- `rationale`: reasoning behind the score
- `requires_human`: boolean if escalation is needed

**Module Relevance Detection:**
- **Environmental**: Only fires when decision involves physical resources, manufacturing, transport, energy, waste, emissions, or similar
- **Fairness**: Fires for any decision affecting other people (skipped for purely personal preferences with no external impact)
- **Transparency**: Fires for any non-trivial decision (skipped for trivial personal preferences without consequences)
- **Conscious Leadership**: Fires for decisions with values, relationships, or moral weight
- **Ethical Framework**: Always fires — the meta-ethical lens
- **Compliance**: Only fires when legal, regulatory, or certification obligations exist

See the module reference files for detailed criteria per module.

### Step 4: Conflict Resolution
If modules disagree, resolve by:
1. **Severity triage** — compliance/legal violations override preference differences
2. **Tension flagging** — explicitly note where modules conflict
3. **Escalation** — if a critical module scores RED or human is required at threshold

### Step 5: Decision
- **🟢 GREEN** (score 75–100): Proceed. Log rationale.
- **🟡 AMBER** (score 50–74): Proceed with caution. Flag to decision-maker. Document concerns.
- **🔴 RED** (score <50): Block. Escalate to human. Full explanation required.

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

## How to Use This Skill

### For Agents (programmatic)
Call the ethics filter as part of your decision loop:

> "Run this through the ethics filter before proceeding: [proposed action]. My constitution is [which modules are enabled]."

### For Humans (reflective)
Describe a decision you're facing and ask:

> "I'm using the ethics filter. Evaluate this decision: [situation]. My constitution enables all modules at moderate strictness."

### For Organizations (governance)
Embed the ethics filter into approval workflows:

> "Every procurement/hiring/marketing decision must pass through the ethics filter. Configure your constitution first, then evaluate each decision before approval."

---

## Quick Reference

| Step | What You Do |
|------|------------|
| 1. Intent | State the action clearly |
| 2. Stakeholders | Map who's affected |
| 3. Modules | Run through enabled modules |
| 4. Conflicts | Resolve tensions between modules |
| 5. Decision | Green / Amber / Red |
| 6. Audit | Log the full evaluation |

---

## Constitution Configuration

A "constitution" is simply the set of modules you've enabled plus their strictness levels. Templates are in `constitution/templates.json`.

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
- **Relaxed** (RED <30, AMBER 30–70, GREEN >70)
- **Moderate** (RED <50, AMBER 50–74, GREEN >74)
- **Strict** (RED <70, AMBER 70–89, GREEN >89)

---

## Module Reference Files

Each module has a detailed reference file with its criteria, questions, scoring rubric, and edge cases:

| Module | File | Core Question |
|--------|------|--------------|
| 🌏 Environmental | `modules/environmental.md` | What is the impact on the natural world? |
| 🤝 Fairness | `modules/fairness.md` | Who is treated fairly or unfairly? |
| 🔓 Transparency | `modules/transparency.md` | Would you publish this decision? |
| 🧘 Conscious Leadership | `modules/conscious-leadership.md` | Is this from above or below the line? |
| ⚖️ Ethical Framework | `modules/ethical-framework.md` | What would each ethical lens say? |
| 📋 Compliance | `modules/compliance.md` | Does this breach any standard or law? |

## Support Files

| File | What it contains |
|------|-----------------|
| `references/testing-methodology.md` | How to validate the ethics filter with synthetic scenarios and blind tests |
| `references/fairness-module-personal-context.md` | Design for a personal/family context modifier discovered during testing |
| `references/research-sources.md` | Authoritative sources behind each module (B Corp, IFOAM, Markkula Center, etc.) |

## V2 Audit Report

The comprehensive test of 52 scenarios is at `~/.hermes/plans/ethics-filter-audit-report-v2.md`.
Key results: 23 GREEN, 14 AMBER, 15 RED. Full score range 5.0–100.0.
Module relevance confirmed working across all categories.
