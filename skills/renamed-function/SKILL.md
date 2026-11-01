---
name: renamed-function
description: Use when a test fails with AttributeError or ImportError for a name the
library renamed in a newer version.
---
1. Search the installed library for the new name (search_code on the library folder).
2. Replace the old name at the call site only. Do not edit the library.
3. Re-run the failing test. If it still fails, report the new error instead of guessing again.