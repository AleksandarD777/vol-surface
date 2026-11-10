# Volatility Surface constructor using Deribit API


## Setup 

Run the following commands, perhaps uv must be installed first

- git clone https://github.com/AleksandarD777/vol-surface.git
- cd vol-surface
- uv sync

## Running Tests

To run the tests implemented using pytest, in your terminal type:

```bash
uv run pytest
```

Run them before opening a pull request to catch regressions.

To add tests, create a file named `test_*.py` in `tests/` and write
functions named `test_*`; pytest discovers them automatically.