"""Compare seat-based subscription prices under fixed customer assumptions."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, DecimalException, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


CENT = Decimal("0.01")
MAX_MONTHLY_PRICE = Decimal("1000000000000.00")


class PricingInputError(ValueError):
    """Raised for invalid or ambiguous pricing assumptions."""


def _nonnegative_int(value: object, label: str, *, allow_zero: bool = True) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PricingInputError(f"{label} must be an integer")
    if value < (0 if allow_zero else 1):
        raise PricingInputError(f"{label} must be {'nonnegative' if allow_zero else 'positive'}")
    return value


def _money(value: object, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise PricingInputError(f"{label} must be a nonnegative amount")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise PricingInputError(f"{label} must be a nonnegative amount") from exc
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise PricingInputError(f"{label} must be finite, nonnegative, with at most 2 decimals")
    if amount > MAX_MONTHLY_PRICE:
        raise PricingInputError(f"{label} must be at most {MAX_MONTHLY_PRICE}")
    return amount


def _label(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PricingInputError(f"{field} must be nonblank text")
    return value.strip()


def _format(amount: Decimal) -> str:
    return str(amount.quantize(CENT, rounding=ROUND_HALF_UP))


def compare(data: dict) -> dict:
    """Calculate MRR/ARR for each plan, holding customers and seats constant."""
    try:
        return _compare(data)
    except DecimalException as exc:
        raise PricingInputError("pricing calculation exceeds the supported numeric range") from exc


def _compare(data: dict) -> dict:
    if not isinstance(data, dict):
        raise PricingInputError("input must be a JSON object")
    currency = _label(data.get("currency"), "currency")
    segments = data.get("segments")
    plans = data.get("plans")
    if not isinstance(segments, list) or not segments:
        raise PricingInputError("segments must be a nonempty list")
    if not isinstance(plans, list) or not plans:
        raise PricingInputError("plans must be a nonempty list")

    parsed_segments = []
    segment_names: set[str] = set()
    for item in segments:
        if not isinstance(item, dict):
            raise PricingInputError("each segment must be an object")
        name = _label(item.get("name"), "segment name")
        if name in segment_names:
            raise PricingInputError(f"duplicate segment name: {name}")
        segment_names.add(name)
        parsed_segments.append((
            name,
            _nonnegative_int(item.get("accounts"), f"{name} accounts"),
            _nonnegative_int(item.get("seats_per_account"), f"{name} seats_per_account", allow_zero=False),
        ))

    total_accounts = sum(accounts for _, accounts, _ in parsed_segments)
    results = []
    plan_names: set[str] = set()
    for item in plans:
        if not isinstance(item, dict):
            raise PricingInputError("each plan must be an object")
        name = _label(item.get("name"), "plan name")
        if name in plan_names:
            raise PricingInputError(f"duplicate plan name: {name}")
        plan_names.add(name)
        seat_price = _money(item.get("seat_price_monthly"), f"{name} seat_price_monthly")
        minimum = _money(item.get("minimum_per_account_monthly", 0), f"{name} minimum_per_account_monthly")
        by_segment = []
        total_mrr = Decimal("0")
        for segment_name, accounts, seats in parsed_segments:
            per_account = max(minimum, seat_price * seats)
            segment_mrr = per_account * accounts
            total_mrr += segment_mrr
            by_segment.append({
                "segment": segment_name,
                "accounts": accounts,
                "seats_per_account": seats,
                "monthly_per_account": _format(per_account),
                "mrr": _format(segment_mrr),
            })
        results.append({
            "name": name,
            "seat_price_monthly": _format(seat_price),
            "minimum_per_account_monthly": _format(minimum),
            "mrr": _format(total_mrr),
            "arr": _format(total_mrr * 12),
            "average_monthly_per_account": _format(total_mrr / total_accounts) if total_accounts else None,
            "segments": by_segment,
        })
    return {"currency": currency, "total_accounts": total_accounts, "plans": results}


def render_text(result: dict) -> str:
    lines = [f"Currency: {result['currency']}  Accounts: {result['total_accounts']}"]
    for plan in result["plans"]:
        lines.append(
            f"{plan['name']}: MRR {plan['mrr']} | ARR {plan['arr']} | "
            f"avg/account/month {plan['average_monthly_per_account'] or 'n/a'}"
        )
        for segment in plan["segments"]:
            lines.append(
                f"  {segment['segment']}: {segment['accounts']} accounts x "
                f"{segment['seats_per_account']} seats = MRR {segment['mrr']} "
                f"({segment['monthly_per_account']}/account/month)"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare seat-based SaaS pricing scenarios")
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input_json.read_text(encoding="utf-8"))
        result = compare(data)
    except (OSError, UnicodeError, json.JSONDecodeError, PricingInputError) as exc:
        print(f"saas-pricing-lab: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if args.json else render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
