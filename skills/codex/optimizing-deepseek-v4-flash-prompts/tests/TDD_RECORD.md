# TDD record

## RED

The test suite was created before the production tool existed. Running `python tests/test_tool.py` produced 9 failures because `scripts/deepseek_prompt_tool.py` was absent. This established that the tests exercised missing behavior rather than pre-existing implementation.

## GREEN

Run `python tests/test_tool.py` after implementation. The release package is accepted only when every test passes.
