# RepoPilot-Agent: starter for the workshop

This folder is the pre-work starter only. The agent code is built during the workshop.

1. Install Python 3.12, Git and Docker Desktop (see the Attendee Pre-Work PDF).
2. Create and activate a virtual environment in this folder.
3. Install the pinned packages: `python -m pip install -r requirements.txt`
4. Copy `.env.example` to `.env` (the file already exists with placeholders). Replace `replace_me` with your own keys. Never commit `.env`.
5. Run the checks: `python -m pytest tests/test_prework.py -v`

Keep the virtual environment active in every terminal you use for the workshop, because the test runner calls `pytest` and `ruff` by name.
