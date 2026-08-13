# Development Guide

## Purpose

Explain how to extend the skill without degrading clarity, reuse, or stability.

## Extension Principles

1. Extend the system by adding reusable modules, not by expanding one-off exceptions.
2. Document every new page type or graphic module with the same contract structure.
3. Preserve the structure-first workflow and blueprint-first default.
4. Preserve graphic-first routing where relation or structure carries meaning.
5. Keep SVG boundaries explicit.
6. Keep anti-generic-consulting guardrails intact.
7. Keep file responsibilities narrow and readable.

## Adding A New Page Type

Create a new page type only when it is expected to recur.

Required documentation fields:

- name
- applicable scenarios
- not applicable scenarios
- visual center definition
- SVG usage scope
- PPT native retention
- text density cap
- required inputs
- optional inputs
- default output
- common misuse

Then:

1. append the new page type to `page-types.md`
2. mention any new routing rule in `workflow-core.md` if needed
3. add one compact example in `examples.md` if the new type is non-obvious

## Adding A New Graphic Module

Required documentation fields:

- module name
- applicable scenarios
- not applicable scenarios
- required inputs
- optional inputs
- default output
- common misuse
- main graphic task

Then:

1. append it to `graphic-modules.md`
2. update `page-blueprint-v2.md` only if a new field is required
3. keep SVG boundaries explicit

## Adding A New Style Theme

Add only when the style differs in operational rules, not just adjectives.

Document:

- intended scenario
- tone
- title behavior
- color behavior
- density preference
- special constraints

Append to `style-system.md`.

## Modifying The Blueprint Schema

Change the schema only when the new field is needed across many slide types.

Required actions:

1. update `page-blueprint-v2.md`
2. update `assets/templates/page_blueprint.template.json`
3. update `scripts/validate_blueprint.py`
4. keep backward compatibility where practical

## Validation Standard

Before packaging:

1. read `SKILL.md` for trigger clarity
2. confirm all referenced files exist
3. ensure all page types and modules use the same documentation pattern
4. validate the JSON blueprint template with `scripts/validate_blueprint.py`
5. remove any stale example or placeholder content

## Maintenance Rule

Favor fewer stronger modules over many overlapping modules. When two modules overlap heavily, merge them or sharpen their boundary.
