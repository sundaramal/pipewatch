# pipewatch

A lightweight CLI tool to monitor and alert on data pipeline health using pluggable check definitions.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install -e .
```

---

## Usage

Define your checks in a YAML config file:

```yaml
# checks.yaml
checks:
  - name: orders_freshness
    type: freshness
    source: postgresql://localhost/mydb
    table: orders
    max_age_minutes: 60

  - name: revenue_row_count
    type: row_count
    source: postgresql://localhost/mydb
    table: revenue
    min_rows: 1000
```

Run pipewatch against your config:

```bash
pipewatch run --config checks.yaml
```

Example output:

```
✔  orders_freshness     PASSED  (last updated 12m ago)
✘  revenue_row_count    FAILED  (842 rows, expected ≥ 1000)

2 checks run · 1 passed · 1 failed
```

Send alerts to Slack or email by adding a `notifications` block to your config. See the [docs](docs/configuration.md) for all available check types and options.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

[MIT](LICENSE)