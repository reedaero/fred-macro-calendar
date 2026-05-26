name: Update Eco Calendar

on:
  schedule:
    - cron: '0 0 * * 0'
  workflow_dispatch: 

jobs:
  build-and-run:
    runs-on: ubuntu-latest

    # Explicitly overrides repository locks for this specific run
    permissions:
      contents: write
      id-token: write

    env:
      FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: 'true'

    steps:
    - name: Checkout repository code
      uses: actions/checkout@v4
      with:
        persist-credentials: true

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests ics pytz

    - name: Run script
      env:
        FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
      run: python eco_ical.py

    - name: Auto-commit calendar file
      uses: stefanzweifel/git-auto-commit-action@v5
      with:
        commit_message: "Automated Sync: Updated major economic calendar"
        file_pattern: 'major_us_eco_calendar.ics'
