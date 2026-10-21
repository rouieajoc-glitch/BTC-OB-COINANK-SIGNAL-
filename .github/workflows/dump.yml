name: Dump SMC data
on: workflow_dispatch

jobs:
  dump:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install requests
      - run: python dump_smc.py
        env:
          COINANK_API_KEY: ${{ secrets.COINANK_API_KEY }}
