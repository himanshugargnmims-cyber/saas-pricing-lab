import unittest

from pricing_lab import PricingInputError, compare


class PricingLabTests(unittest.TestCase):
    def test_minimum_and_seat_price(self):
        result = compare({
            "currency": "INR",
            "segments": [
                {"name": "Small", "accounts": 2, "seats_per_account": 3},
                {"name": "Big", "accounts": 1, "seats_per_account": 10},
            ],
            "plans": [
                {"name": "Base", "seat_price_monthly": "10", "minimum_per_account_monthly": "50"},
            ],
        })
        plan = result["plans"][0]
        self.assertEqual(result["total_accounts"], 3)
        self.assertEqual(plan["segments"][0]["monthly_per_account"], "50.00")
        self.assertEqual(plan["segments"][1]["monthly_per_account"], "100.00")
        self.assertEqual(plan["mrr"], "200.00")
        self.assertEqual(plan["arr"], "2400.00")
        self.assertEqual(plan["average_monthly_per_account"], "66.67")

    def test_zero_accounts_has_no_average(self):
        result = compare({
            "currency": "USD",
            "segments": [{"name": "Pilot", "accounts": 0, "seats_per_account": 1}],
            "plans": [{"name": "Simple", "seat_price_monthly": "5.00"}],
        })
        self.assertEqual(result["plans"][0]["mrr"], "0.00")
        self.assertIsNone(result["plans"][0]["average_monthly_per_account"])

    def test_rejects_invalid_assumptions(self):
        base = {
            "currency": "USD",
            "segments": [{"name": "One", "accounts": 1, "seats_per_account": 2}],
            "plans": [{"name": "A", "seat_price_monthly": "1.00"}],
        }
        for bad in (-1, True, 1.5):
            with self.subTest(bad=bad), self.assertRaises(PricingInputError):
                compare({**base, "segments": [{"name": "One", "accounts": bad, "seats_per_account": 2}]})
        with self.assertRaises(PricingInputError):
            compare({**base, "plans": [{"name": "A", "seat_price_monthly": "NaN"}]})
        with self.assertRaises(PricingInputError):
            compare({**base, "plans": [{"name": "A", "seat_price_monthly": "1.001"}]})

    def test_large_prices_fail_cleanly(self):
        base = {
            "currency": "USD",
            "segments": [{"name": "One", "accounts": 1, "seats_per_account": 2}],
            "plans": [{"name": "A", "seat_price_monthly": "1.00"}],
        }
        for amount in ("1e28", "1e1000000"):
            with self.subTest(amount=amount), self.assertRaises(PricingInputError):
                compare({**base, "plans": [{"name": "A", "seat_price_monthly": amount}]})
        with self.assertRaises(PricingInputError):
            compare({**base, "segments": [{"name": "One", "accounts": 10**100, "seats_per_account": 2}]})


if __name__ == "__main__":
    unittest.main()
