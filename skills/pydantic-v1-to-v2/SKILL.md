---
name: pydantic-v1-to-v2
description: Use when a test fails with Pydantic v1 style errors such as class Config,
.dict(), .json(), or parse_obj.
---
1. Replace `class Config:` with `model_config = ConfigDict(...)` from pydantic.
2. Replace `.dict()` with `.model_dump()` and `.json()` with `.model_dump_json()`.
3. Replace `parse_obj(x)` with `Model.model_validate(x)`.
4. Run the failing test again. Do not change the test's expected values.