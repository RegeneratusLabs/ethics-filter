# Personal/Family Context Modifier for Fairness Module

## Discovery
During self-audit testing (June 2026), the Fairness module scored personal/family decisions more harshly than intuitive:
- B2 (Inheritance Dispute): Scored RED at 43.8, expected AMBER
- B4 (Neighborhood Dispute): Scored RED at 36.2, expected AMBER

The issue: the Fairness module applies the same corporate-grade yardstick to personal relationships.

## The Modifier
In personal or family decisions, add +0-15 points to the fairness score to account for:

1. **Relationship continuity**: Long-term relationships have value beyond any single transaction. What seems unfair in one incident may be balanced across a relationship history.

2. **Legitimate non-ethical constraints**: Family decisions involve emotional bonds, shared history, care obligations, and practical constraints that aren't present in corporate contexts.

3. **Different proportionality**: A 30cm property line encroachment matters differently between neighbours than a contract breach between companies.

## When to Apply
- Inheritance disputes between family members
- Care arrangements for aging parents
- Neighbourhood property disputes
- Family business succession
- Personal relationship decisions with ethical dimensions

## When NOT to Apply
- Abuse, exploitation, or coercion (even in families, these score zero)
- Decisions affecting vulnerable people (children, elderly without capacity)
- Business decisions with family involvement (treat as corporate unless clearly personal)

## Implementation
```python
def apply_personal_context_modifier(base_score, context_tags):
    if "personal" in context_tags or "family" in context_tags:
        modifier = min(15, base_score * 0.3)  # Cap at 15 or 30% of base
        return min(100, base_score + modifier)
    return base_score
```

## Status
Not yet implemented in the Fairness module code. This reference documents the design for future implementation.
