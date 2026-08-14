# Module Relevance Pattern

A design pattern for modular evaluation systems where modules only fire when 
contextually relevant to the decision or item being evaluated.

## Problem

In a multi-module evaluation system (ethics filter, compliance checker, quality gate),
applying ALL modules to ALL inputs produces noise. A personal apology doesn't need 
environmental impact assessment. A breakfast choice doesn't need compliance checking.

Applying irrelevant modules:
- Inflates/deflates overall scores with noise
- Confuses users with irrelevant flags
- Wastes compute and context window
- Damages credibility

## Solution

Before scoring with any module, run a **relevance check**. Each module declares what
types of inputs it applies to. Only modules that match the current input context are
evaluated. Non-relevant modules are silently skipped.

## Implementation Pattern

```
MODULE_RELEVANCE = {
    "module-name": {
        "relevant_when": ["keyword1", "keyword2"],
        "exclude_when": ["trivial case", "edge case"],
        "description": "When this module applies"
    }
}

def check_relevance(action_text, context_text, module_config):
    # 1. Check exclude_when first
    # 2. If no relevant_when, default to relevant
    # 3. Check for keyword matches in relevant_when
    # Return boolean
```

## Keyword Strategy

Keywords should be:
- **Domain nouns** — words indicating subject area (energy, waste, legal, hiring)
- **Action verbs** — words indicating action type (manufacture, dump, report)
- **Critical terms** — words that MUST trigger (illegal, toxic, safety)

Avoid:
- Overly generic words (business, thing) that trigger too often
- Rare jargon the user won't naturally use

## Benefits

- **Noise reduction** — Users only see relevant feedback
- **Score accuracy** — Overall only reflects applicable dimensions
- **Credibility** — The filter feels intelligent, not mechanical
- **Extensibility** — New modules declare their own relevance criteria

## When NOT to Use

- When the framework is intentionally universal (everything always applies)
- When false positives are low-cost
- When input domain is highly controlled and known in advance
