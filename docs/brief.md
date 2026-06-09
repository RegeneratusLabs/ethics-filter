# Ethics Filter Skillset — Project Brief

## The Vision

A **universal ethics filter** that any AI agent — running inside a corporation, a small business, or someone's personal life — runs every significant decision through before acting.

Not "ethics for ethical businesses." **Ethics for everyone who wants to be on the right side of AI.**

Imagine Claude, ChatGPT, or any AI assistant running this filter before it makes a decision on your behalf. Businesses from sole traders to multinationals. Individuals making purchasing decisions, career moves, family choices. All guided by the same structured ethical reasoning.

The skillset is not theoretical. It's synthesised from decades of real human frameworks: B Corp standards, Markkula Center ethical decision-making, Conscious Leadership, systems thinking frameworks, and more.

---

## Where This Comes From (The Research)

Every module is grounded in established frameworks, not vibes:

| Framework | Source | What It Provides |
|---|---|---|
| **B Corp Impact Assessment** | B Lab (2006–present) | 5 impact areas: Governance, Workers, Community, Environment, Customers. 250 weighted questions across stakeholder governance. |
| **Markkula Center Ethical Decision-Making** | Santa Clara University | 5-step ethical framework: Recognize Issue, Get Facts, Evaluate Alternatives, Make Decision, Act & Reflect. 5 ethical lenses: Utilitarian, Rights, Fairness, Common Good, Virtue. |
| **Conscious Capitalism / Conscious Leadership** | John Mackey, Raj Sisodia (2007–present) / The 15 Commitments | Stakeholder orientation, purpose-driven culture, self-awareness, above/below the line framework. |
| **Holistic Management / Systems Thinking** | Savory Institute, HMI (1980s–present) | Whole-system decision-making framework that integrates social, economic, and environmental factors. Applicable beyond agriculture. |
| **ESG / Triple Bottom Line** | Global standards | People, Planet, Profit. Environmental stewardship, social equity, economic viability. |
| **F-A-T-H-E-R Ethical Leadership** | Barry D. Moore | Fairness, Accountability, Trust, Honesty, Equality, Respect. |
| **IFOAM Principles** | IFOAM – Organics International | Universal ethical principles: Health, Ecology, Fairness, Care. Applicable framework for any business considering its holistic impact. |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                 AGENT / HUMAN ACTION REQUEST           │
│  (e.g. "approve this supplier" / "buy this stock"     │
│   "should I take this job?" / "hire this candidate")  │
└──────────────────┬───────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────┐
│              THE ETHICS FILTER ENGINE                  │
│                                                       │
│   1. INTENT CLARIFICATION — what am I being asked?    │
│   2. STAKEHOLDER MAPPING — who is affected?           │
│   3. MODULE EVALUATION — run enabled modules          │
│   4. CONFLICT RESOLUTION — harmonise module outputs   │
│   5. DECISION — ✅ / ⚠️ / 🛑                          │
│   6. AUDIT LOG — why the decision was made            │
└──────────────────┬───────────────────────────────────┘
                   ▼
         ✅ Proceed / ⚠️ Flag / 🛑 Blocked
         ↓                     ↓
    Corporate audit trail    Personal reflection log
    Board reporting          Journal / learning
```

### How It Plugs In

**For AI Agents (direct integration):**
- **MCP (Model Context Protocol)** — expose as tools any agent can call
- **SDK import** — import directly into Python/TS agent projects (Claude, ChatGPT, Hermes, Sim, etc.)
- **CLI** — `ethics-filter evaluate --action "..." --context "..."`

**For Humans (personal use):**
- **Web app / chat interface** — describe a decision, get structured ethical analysis back
- **Slack/Discord bot** — type `/ethics "should I..."` and get reasoning
- **API** — POST a decision context, get scored evaluation

**For Businesses (corporate governance):**
- **Webhook** — POST evaluation into compliance workflows
- **Embedded SDK** — build into procurement, hiring, marketing approval pipelines
- **Board reporting** — aggregated ethics scores across all corporate decisions

---

## The Modules

### Module 1: 🌏 Environmental Stewardship
**Based on:** B Corp Environment, ESG, Triple Bottom Line, IFOAM Ecology principle

Questions:
- What is the carbon / waste / water impact of this decision?
- Is there a more environmentally sound alternative?
- Does this support circularity (reduce, reuse, recycle)?
- Is packaging / transport / sourcing minimised?
- Does it avoid harm to biodiversity and ecosystems?
- Does it consider the full lifecycle from source to end-of-life?

### Module 2: 🤝 Fairness & Stakeholder Impact
**Based on:** B Corp Workers + Community, IFOAM Fairness, Conscious Capitalism

Questions:
- Who are all stakeholders affected by this?
- Does it treat workers, suppliers, and customers fairly?
- Does it strengthen the local community or extract from it?
- Are supply chain relationships equitable?
- Does this support the business's stated purpose beyond profit?
- Is anyone being exploited or taken advantage of?

### Module 3: 🔓 Transparency & Accountability
**Based on:** B Corp Governance, F-A-T-H-E-R Leadership, Markkula Publicity Test

Questions:
- Would the business publish this decision publicly?
- Could the owner defend this in front of their customers?
- Is the reasoning traceable and auditable?
- Does it align with the business's stated values and mission?
- Is there any conflict of interest?
- Would this stand up to scrutiny?

### Module 4: 🧘 Conscious Leadership & Values Alignment
**Based on:** Conscious Leadership 15 Commitments, Values-Based Leadership, Ethical Leadership

Questions:
- Does this decision come from above the line (curiosity, commitment, ownership) or below the line (defensiveness, blame, denial)?
- Does it align with the business's stated core values?
- Does it serve the long-term vision or just short-term convenience?
- Is there a more creative, values-aligned alternative?
- Would this decision be made if nobody was watching?
- Does this reflect the kind of business the owner wants to be?

### Module 5: ⚖️ Ethical Decision Framework
**Based on:** Markkula Center 5-Step Framework, 7-Step Model, IDEA Framework, IFOAM Care principle

Questions:
- What is the ethical issue at stake here?
- What are the facts? (clarify assumptions, gather information)
- What are the options? (not binary — creative alternatives)
- Test options through multiple ethical lenses:
  - **Utilitarian**: greatest good for most people?
  - **Rights**: does it respect everyone's rights and dignity?
  - **Fairness**: is it equitable, especially for the most vulnerable?
  - **Common Good**: does it serve the broader community?
  - **Virtue**: does it reflect integrity and character?
- Can I defend this choice? Would I advise someone else to do it?

### Module 6: 📋 Compliance & Certification Guard
**Based on:** Certification standards generally, legal compliance, audit requirements

Questions:
- Does this action risk any existing certification the business holds (B Corp, fair trade, organic, etc.)?
- Are there regulatory or legal requirements being met?
- Is there an adequate audit trail?
- Would this pass a certification or regulatory audit?
- Are there timing implications (cert renewals, reporting deadlines, tax obligations)?

---

## The Decision Engine (Step by Step)

When an agent proposes an action, the ethics filter runs this pipeline:

```
STEP 1: INTENT CLARIFICATION
  └─ What exactly is being proposed? (The agent states it in plain language)

STEP 2: STAKEHOLDER MAPPING  
  └─ Who is affected by this? (owner, workers, customers, suppliers, community, environment, future generations)

STEP 3: MODULE EVALUATION
  └─ Run each enabled module in parallel:
      ├─ Module 1: Environmental Stewardship 🟢
      ├─ Module 2: Fairness & Stakeholder Impact 🟢
      ├─ Module 3: Transparency & Accountability 🟢
      ├─ Module 4: Conscious Leadership 🟢
      ├─ Module 5: Ethical Framework 🟢
      └─ Module 6: Compliance Guard 🟢

STEP 4: CONFLICT RESOLUTION
  └─ If modules disagree, the engine:
      ├─ Ranks by severity (compliance violations > preference differences)
      ├─ Flags the tension explicitly
      └─ Escalates to human if threshold exceeded

STEP 5: DECISION
  └─ ✅ GREEN (score 80-100): Proceed, log rationale
  └─ ⚠️ AMBER (score 50-79): Proceed with caution, flag to human, log flags
  └─ 🛑 RED (score <50): Block, escalate to human, full explanation

STEP 6: AUDIT
  └─ Every decision stored with:
      ├─ Timestamp & action description
      ├─ Scores per module (not just overall)
      ├─ Tensions between modules
      ├─ Whether human was looped in
      └─ Final resolution
```

---

## How It Ships

### Phase 1: The Hermes Skillset (this sprint)
A standalone Hermes skill with:
- `ethics-filter` — the core evaluation engine
- Each module as a sub-skill or configurable tool
- CLI interface: `ethics-filter evaluate --action "..." --context "..."`
- MCP server interface: expose as tools for any MCP-compatible agent (Claude, ChatGPT, etc.)
- Audit log to file/JSON

### Phase 2: Framework Adapters & Integrations
Drop-in connectors for:
- **Sim** — as a workflow block (drag-and-drop ethics evaluation)
- **Flowise** — as a custom node
- **n8n** — as an AI node
- **Activepieces** — as a piece
- **Claude / ChatGPT** — via MCP tool call or custom GPT action
- **Slack / Discord** — as an ethics bot for teams

### Phase 3: The Constitution Builder
A UI where anyone configures their own ethics constitution:
- **For personal use:** "Turn on Transparency, Conscious Leadership, and Ethical Framework — I want to reflect on major life decisions"
- **For small business:** "Enable Environment, Fairness, Transparency, and Compliance — I run an ethical coffee roastery"
- **For corporate:** "Enable all modules at strict level — every procurement and hiring decision runs through here. Board reports quarterly."
- Sliders for strictness per module
- Presets per industry and use case

---

## What Makes This Different

| Dimension | Existing Guardrails (Guardrails AI, NeMo, etc.) | This Skillset |
|---|---|---|
| Focus | AI safety (hallucinations, PII, jailbreaks) | **Holistic ethics** (environment, fairness, transparency, leadership, personal integrity) |
| Scope | LLM output safety | **Any decision** — corporate, personal, professional |
| Audience | Developers and security teams | **Everyone** — CEOs, managers, freelancers, parents, voters |
| Source material | Technical safety research | B Corp, Conscious Capitalism, Markkula Center, systems thinking, philosophy |
| Tone | "Block this toxic output" | **"Does this serve people, community, and the planet?"** |
| Modularity | One-size-fits-all guardrails | **Per-person, per-organization constitution** |
| Output | Block/review/allow | **Structured ethical reasoning** — score, rationale, alternatives, audit log |

---

## Build Order (This Sprint)

1. Core engine: `ethics-filter` — decision pipeline, scoring, audit logging
2. Module 5: Ethical Decision Framework (the meta-module that grounds everything)
3. Module 3: Transparency & Accountability (easiest to implement, highest impact)
4. MCP server interface (so any agent can call it TODAY)
5. CLI interface
6. Module 1: Environmental Stewardship
7. Module 2: Fairness & Stakeholder Impact
8. Module 4: Conscious Leadership
9. Module 6: Compliance Guard
10. Sim adapter (workflow block)
11. Constitution builder (simple JSON config initially)

---

## The Bigger Picture (After This Sprint)

Once the skillset exists and is proven inside Hermes and other frameworks, it becomes the ethical conscience layer for *any* AI agent interacting with the world. The universal ethics filter that every AI — corporate, personal, commercial — uses to ensure its decisions land on the right side of history.

Businesses plug it into their procurement, hiring, and compliance pipelines. Individuals plug it into their personal AI assistants. Claude, ChatGPT, and every other agent runs decisions through it by default.

That's the long game. But first we build something that works, that anyone can use, and that proves the model.
