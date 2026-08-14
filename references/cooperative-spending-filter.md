# Cooperative Treasury Spending Filter — Reference Implementation

A lightweight spending approval pipeline for producer cooperatives. Built for the **Hermes Agent Accelerated Business Hackathon** (NVIDIA x Stripe x Nous Research).

**Design doc** → **Working implementation at:**
`~/hermes-shared/projects/coop-agent/`

---

## Architecture

```
Producer voice/text request
        │
        ▼
┌──────────────────────────────┐
│  Market Price Intel          │ ← web_search + cron (weekdays 6am)
│  (AU wholesale prices per    │
│   product, organic/conv tiers)│
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│  Producer Profile Lookup     │ ← memory or JSON from CLI
│  - certification status      │
│  - approved input suppliers  │
│  - monthly budget / remaining │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│  Spending Filter (3 checks)  │ ← Python pipeline
│  1. Certification compatible │    (NOT the Ethics Filter — standalone)
│  2. Price within market      │
│  3. Budget remaining         │
└──────────┬───────────────────┘
           ▼
  GREEN ───► Stripe Link virtual card → order placed
  AMBER ───► Flag to treasurer → hold
  RED  ────► Blocked + compliance reason
```

**Key design choice:** The user explicitly requested a "simplified not so much ethics filter, but a spending filter pipeline depending on if you are organic or not." The pipeline is a standalone Python module — it does NOT import or route through the Ethics Filter's 6-module engine. It uses 3 hardcoded checks with deterministic logic, not LLM scoring. This makes it auditable, testable, and unbypassable by prompt injection.

---

## Python Pipeline

**Location:** `~/hermes-shared/projects/coop-agent/spending_filter/`

### Models (`models.py`)

| Class | Fields | Notes |
|---|---|---|
| `CertificationStatus` | ORGANIC, IN_TRANSITION, CONVENTIONAL | Enum |
| `Decision` | GREEN, AMBER, RED | Enum — pipeline result |
| `ProducerProfile` | producer_id, name, certification, products, approved_inputs, monthly_budget_cents, spent_this_month_cents, organic_approved_suppliers | Dataclass with `remaining_budget_cents` property |
| `SpendRequest` | producer_id, item_name, quantity, unit_price_cents, supplier, supplier_organic_approved | Dataclass with `total_cents` property |
| `SpendEvaluation` | decision, request, producer, checks, reasons, evaluated_at | Full audit record |

### Pipeline (`pipeline.py`)

The `SpendingPipeline` class runs 3 checks:

1. **Certification compatibility:** Organic producers require `supplier_organic_approved=True` and supplier must be in `organic_approved_suppliers`. IN_TRANSITION and CONVENTIONAL always pass.
2. **Price reasonableness:** If market price data exists for this item, unit price must be within `[min_cents, max_cents]`. No data = skip check.
3. **Budget:** If `monthly_budget_cents > 0`, total must not exceed `remaining_budget_cents`. Zero = unlimited.

**Decision logic:**
- All pass → GREEN
- Certification fails → RED (compliance override, even if other checks pass)
- Budget fails but cert+price OK → AMBER
- Price fails but cert OK → AMBER

### CLI (`cli.py`)

```bash
# From project root
python3 cli.py evaluate <request.json> <producer.json> [prices.json]

# Run demo (all 3 decision paths)
python3 cli.py demo
```

### Tests (`test_pipeline.py`) — 8 tests, all passing

```
PASS  test_green_organic_input_from_approved_supplier
PASS  test_red_organic_input_from_unapproved_supplier
PASS  test_green_conventional_producer_any_supplier
PASS  test_amber_over_budget
PASS  test_red_certification_violation_overrides_budget
PASS  test_price_out_of_range_amber
PASS  test_no_market_price_data_skips_price_check
PASS  test_in_transition_flexible
```

---

## Demo Scenarios

**Location:** `~/hermes-shared/projects/coop-agent/demo/`

| Scenario | Decision | Why |
|---|---|---|
| 50kg organic blood and bone from Bulk Ag Supplies | GREEN | Organic ✓, $3.50/kg in range ✓, $175 of $750 budget ✓ |
| 10L synthetic pesticide from Chem Corp | RED | Organic producer, Chem Corp not organic-approved ✗ |
| 20t organic compost for $800 (only $750 remaining) | AMBER | Certification ✓, price ✓, but over budget $50 ✗ |

**Producer profile (Green Valley Farm):** Organic certified, $1,200/mo budget, $450 already spent. Approved suppliers: Bulk Ag Supplies, Organic Inputs Co-op, Green Grow.

**Market prices:** 6 items tracked in `demo/prices.json` with min/max cents per unit, sourced from AU wholesale data.

---

## Stripe Integration

### Stripe Link CLI (virtual cards)

```bash
# Install globally
npm install -g @stripe/link-cli

# Version installed: 0.7.4
# Auth
link-cli auth login --client-name "Co-op Agent" --interval 5 --timeout 300

# Create spend request when filter returns GREEN
link-cli spend-request create \
  --payment-method-id <pm_id> \
  --merchant-name "<supplier>" \
  --amount <total_cents> \
  --line-item "name:<item>,unit_amount:<unit_cents>,quantity:<qty>" \
  --request-approval

# Retrieve credential — ALWAYS use --output-file, never stdout
link-cli spend-request retrieve <lsrq_id> \
  --include card \
  --output-file /tmp/link-card.json \
  --format json

# Clean up
rm -f /tmp/link-card.json
```

**Critical:** Stripe Link is US-only. For AU demo contexts, simulate or use test mode.

### Stripe CLI (Projects)

```bash
# Installed via apt: v1.42.14
# Projects plugin: install via `stripe plugin install projects`
# Provision SaaS, sync creds into .env
stripe projects add neon/postgres
stripe projects list
```

---

## Market Intel

**Script:** `~/hermes-shared/projects/coop-agent/market_intel/update_prices.py`
**Cron:** `coop-agent-market-intel` — weekdays 6am AEST
**Workdir:** `/home/josh/hermes-shared/projects/coop-agent`
**Script path (copied):** `~/.hermes/scripts/coop-update-prices.py`

The script reads `demo/prices.json`, prints a summary of tracked products and their price ranges. In production this would use web_search to refresh prices from wholesale market sources.

---

## Hermes Skill

**Name:** `coop-agent` (category: regeneratus)
**Location:** `~/.hermes/skills/regeneratus/coop-agent/SKILL.md` (symlinked from `~/hermes-shared/projects/coop-agent/SKILL.md`)
**Status:** Installed and enabled

The skill defines trigger phrases, workflows for market lookup / spend requests / invoicing, and references the spending filter CLI path.

---

## GREEN/AMBER/RED Decision Matrix

| Check | Pass | Fail |
|-------|------|------|
| Input compatible with cert? | Continue | RED — compliance violation, cannot override |
| Price within market range? | Continue | AMBER — needs treasurer negotiation |
| Budget remaining? | Continue | AMBER — needs treasurer budget increase |
| All 3 pass | GREEN | Execute via Stripe Link |

---

## Project Structure

```
coop-agent/
├── SKILL.md                        # Hermes skill definition
├── cli.py                          # CLI entry point for spending filter
├── spending_filter/
│   ├── __init__.py
│   ├── models.py                   # ProducerProfile, SpendRequest, etc.
│   ├── pipeline.py                 # 3-step evaluation pipeline
│   └── test_pipeline.py            # 8 tests, all passing
├── market_intel/
│   └── update_prices.py            # Cron-based price updater
├── demo/
│   ├── producer.json               # Demo producer (Green Valley Farm)
│   ├── prices.json                 # 6 items with market ranges
│   ├── green_request.json          # All checks pass
│   ├── red_request.json            # Certification blocks it
│   ├── amber_request.json          # Budget blocks it
│   └── demo_flow.md                # Video submission script
├── stripe-link-skill.md            # Stripe Link CLI wrapper skill
├── docs/pitch.md                   # Judge-facing pitch
└── README.md                       # Project overview
```

---

## Relationship to the Ethics Filter

The spending filter is a **domain-specific specialization**, not a subset of the Ethics Filter:

| Dimension | Ethics Filter | Spending Filter |
|-----------|--------------|-----------------|
| Scope | Universal (any decision) | Specific (co-op treasury) |
| Evaluation | LLM-scored modules | Deterministic check pipeline |
| Modality | Human + Agent | Agent-only (automated) |
| Output | Score 0–100 + rationale | GREEN/AMBER/RED + reasons |
| Override | None (advisory) | RED blocks execution |
| Test coverage | 52 scenarios (LLM-evaluated) | 8 unit tests (assertions) |

Both are part of the broader compliance toolkit. For agricultural certification enforcement, use the spending filter. For general ethical deliberation on co-op governance policies, use the Ethics Filter.
