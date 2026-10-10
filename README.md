# saas-pricing-lab

Compare seat-based subscription prices using explicit customer counts and seats per account. This is a transparent pricing calculator for planning conversations, not a sales forecast.

## What it does

For each proposed plan and customer segment, monthly charge per account is `max(monthly minimum, seats per account × monthly seat price)`. The CLI totals monthly recurring revenue (MRR), annual run rate (`MRR × 12`), and average monthly revenue per account.

## Quick start

Requires Python 3.10 or newer. No packages to install.

```bash
python3 pricing_lab.py examples/scenarios.json
python3 pricing_lab.py examples/scenarios.json --json
python3 -m unittest discover -s tests -v
```

The input is a JSON object with `currency`, nonempty `segments`, and nonempty `plans` arrays. See [examples/scenarios.json](examples/scenarios.json) for a complete example. Prices should be quoted strings with at most two decimal places.

Example output (first plan):

```text
Currency: USD  Accounts: 138
Accessible: MRR 18450.00 | ARR 221400.00 | avg/account/month 133.70
  Small teams: 100 accounts x 5 seats = MRR 4500.00 (45.00/account/month)
  Growing teams: 30 accounts x 25 seats = MRR 6750.00 (225.00/account/month)
  Large teams: 8 accounts x 100 seats = MRR 7200.00 (900.00/account/month)
```

## Assumptions and limits

- Every segment buys each proposed plan in turn; customer counts and seat counts stay fixed across scenarios.
- The model does not estimate conversion, churn, discounts, taxes, usage fees, annual prepayment, or changes in demand when prices change.
- ARR is annualized MRR, not recognized revenue or a forecast.
- The currency label is displayed as provided; no exchange-rate conversion occurs.
- Inputs are validated for nonnegative, finite prices up to 1 trillion per seat or monthly minimum, and integer account/seat counts. Money is calculated with decimal arithmetic; calculations beyond its supported range fail with a clear input error.

## License

MIT. See [LICENSE](LICENSE).
