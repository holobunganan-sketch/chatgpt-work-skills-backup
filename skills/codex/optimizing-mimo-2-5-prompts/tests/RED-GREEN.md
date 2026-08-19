# RED / GREEN record

The executable behavior was test-first.

## RED

Before `scripts/mimo_prompt_tool.py` existed, the eight regression tests all failed because the executable entry point was missing. This confirmed the tests were checking behavior that did not yet exist.

## GREEN target

The implementation must make these behaviors pass:

1. compiled prompts contain the complete task-contract sections;
2. medical profile enforces evidence/fact-inference separation;
3. long-context profile creates source-map and position-neutral rules;
4. compile can write to a file;
5. compiled prompts pass the linter;
6. weak, unstructured prompts fail with actionable lint codes;
7. cache planning puts stable material before volatile task/material content;
8. invalid task specs are rejected.

Run `python scripts/self_test.py` for current status.
