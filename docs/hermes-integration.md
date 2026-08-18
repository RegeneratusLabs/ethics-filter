# Hermes Agent Integration

The Ethics Filter ships as a **Hermes plugin** (`plugin/` in this repo) that registers:

1. The `ethics-filter` skill (loadable as `plugin:ethics-filter`) with module rubrics and constitution templates as linked files
2. The `/ethics` slash command — evaluate a decision, get a readable verdict
3. The `ethics_evaluate` tool — evaluate a decision, get a scored, auditable verdict

The plugin is self-contained: it vendors the engine under `plugin/ethics_filter/`, so it works after install without a separate pip step.

## Install

### From GitHub

```bash
hermes plugins install RegeneratusLabs/ethics-filter --enable
```

`--enable` skips the confirmation prompt. If you want to pin an immutable version:

```bash
hermes plugins install RegeneratusLabs/ethics-filter --ref <full-40-char-sha> --enable
```

### From source

```bash
git clone git@github.com:RegeneratusLabs/ethics-filter.git
cp -r ethics-filter/plugin ~/.hermes/plugins/ethics-filter
hermes plugins enable ethics-filter
```

## Verify

```bash
hermes plugins list | grep ethics-filter
```

If you use profiles, each profile has its own plugins directory — copy `plugin/` into each profile's `~/.hermes/profiles/<name>/plugins/` and enable per profile.

## Usage

### Slash command

```
/ethics "Should we approve this supplier?" --context "organic farm, three quotes, first order"
/ethics "Hire this candidate" --constitution corporate-governance
```

Returns a readable verdict: decision, score, enabled modules, per-module scores, tensions, and whether human review is required.

### Tool

The `ethics_evaluate` tool is available to any agent loop. Parameters:

| Parameter | Type | Description |
|---|---|---|
| `action` | string (required) | The proposed action or decision |
| `context` | string | Background: stakeholders, constraints, facts |
| `constitution` | string | Preset: small-business-ethical (default), personal-reflection, corporate-governance, startup-quick, maximalist, minimal-safe |
| `scores` | object | Optional 0-100 per-module scores. Provide to get a deterministic scored verdict + audit record. |
| `auto_score` | boolean | Only relevant when `scores` is omitted. When true, the plugin asks the user's model to score; when false (default) it returns the evaluation brief. |

When `scores` is omitted the tool returns the evaluation brief (enabled modules, thresholds, rubric prompt, JSON schema) so the **host agent can score inline and always reply** — no hidden nested LLM call that can stall or lose the response if the client disconnects mid-evaluation. Set `auto_score: true` to have the plugin call the user's model to score instead (slower). The `/ethics` command behaves the same; add `--auto-score` to force scoring.

### Skill

Load the skill in any session to get the full methodology:

```
skill_view(name='plugin:ethics-filter')
```

The skill is also portable — the root `SKILL.md` in this repo works with any agent that reads markdown skills, and the module rubrics in `ethics_filter/modules/` are framework-agnostic.

## Audit trail

Every evaluation appends a JSONL record to `$ETHICS_FILTER_AUDIT` or `~/.ethics-filter/audit.jsonl`. Inspect it with the CLI:

```bash
ethics-filter audit --tail 10
```

## Keeping the plugin in sync

The bundled skill and vendored engine are generated from canonical sources. After changing `SKILL.md`, module files, or engine code, regenerate:

```bash
python scripts/sync_skill.py        # refresh plugin/ bundle
python scripts/sync_skill.py --hermes   # also refresh ~/.hermes/skills/ethics-filter
python scripts/sync_skill.py --check    # CI gate — exit 1 on drift
```
