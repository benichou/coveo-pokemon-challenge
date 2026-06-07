"""Unit tests for src/schemas.py — Pydantic data shapes.

Focus: the percentage-to-fraction coercion on ExpectedLift. Sonnet 4.6
occasionally returns percentage-format numbers (76.0) instead of the
fraction-format the schema expects (0.76); the validator now coerces
percentages back to fractions defensively. Regression: see the failed
closed-loop cron run that motivated this test.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from schemas import ExpectedLift


class TestExpectedLiftFractionPassthrough:
    """Values already in [0, 1] should pass through unchanged."""

    def test_fraction_zero(self):
        lift = ExpectedLift(**{"from": 0.0, "target": 0.0})
        assert lift.from_ == 0.0
        assert lift.target == 0.0

    def test_fraction_one(self):
        lift = ExpectedLift(**{"from": 1.0, "target": 1.0})
        assert lift.from_ == 1.0
        assert lift.target == 1.0

    def test_fraction_typical(self):
        lift = ExpectedLift(**{"from": 0.62, "target": 0.78})
        assert lift.from_ == 0.62
        assert lift.target == 0.78


class TestExpectedLiftPercentageCoercion:
    """The actual regression — values > 1.0 are percentages and get
    divided by 100 to become fractions.

    Reproduces the failed closed-loop cron run that returned values
    {37.5, 50.0, 60.0, 62.5, 70.0, 76.0, 79.0} and broke Pydantic
    validation before the coercion was added.
    """

    def test_integer_percentage_to_fraction(self):
        lift = ExpectedLift(**{"from": 76, "target": 79})
        assert lift.from_ == pytest.approx(0.76)
        assert lift.target == pytest.approx(0.79)

    def test_float_percentage_to_fraction(self):
        lift = ExpectedLift(**{"from": 76.0, "target": 79.0})
        assert lift.from_ == pytest.approx(0.76)
        assert lift.target == pytest.approx(0.79)

    def test_decimal_percentage_to_fraction(self):
        # The actual values that broke production
        lift = ExpectedLift(**{"from": 37.5, "target": 62.5})
        assert lift.from_ == pytest.approx(0.375)
        assert lift.target == pytest.approx(0.625)

    def test_full_regression_payload(self):
        # Reproduces the exact 7-error payload from the failed cron run
        payloads = {
            "cross-source-synthesis": {"from": 40.0, "target": 50.0},
            "form-comparison": {"from": 37.5, "target": 62.5},
            "cross-pokemon-compare": {"from": 60.0, "target": 70.0},
            "overall_accuracy": {"from": 76.0, "target": 79.0},
        }
        for _category, payload in payloads.items():
            lift = ExpectedLift(**payload)
            assert 0.0 <= lift.from_ <= 1.0
            assert 0.0 <= lift.target <= 1.0
            assert lift.from_ == pytest.approx(payload["from"] / 100.0)
            assert lift.target == pytest.approx(payload["target"] / 100.0)


class TestExpectedLiftEdgeCases:
    """Negative values, exact 1.0 boundary, non-numeric input."""

    def test_exactly_one_passes(self):
        # 1.0 is a valid fraction (100% accuracy); not divided
        lift = ExpectedLift(**{"from": 1.0, "target": 1.0})
        assert lift.from_ == 1.0
        assert lift.target == 1.0

    def test_just_above_one_coerced(self):
        # 1.5 is treated as 1.5% → 0.015
        lift = ExpectedLift(**{"from": 1.5, "target": 2.0})
        assert lift.from_ == pytest.approx(0.015)
        assert lift.target == pytest.approx(0.02)

    def test_exactly_one_hundred_coerced(self):
        # 100.0 → 1.0 (the percentage edge case)
        lift = ExpectedLift(**{"from": 100.0, "target": 100.0})
        assert lift.from_ == 1.0
        assert lift.target == 1.0

    def test_negative_value_rejected(self):
        # Negative values still fail (ge=0.0 still enforced after coercion)
        with pytest.raises(ValidationError):
            ExpectedLift(**{"from": -0.1, "target": 0.5})

    def test_percentage_above_one_hundred_rejected(self):
        # 150.0 / 100 = 1.5 — still above le=1.0, validator rejects
        with pytest.raises(ValidationError):
            ExpectedLift(**{"from": 0.5, "target": 150.0})


class TestExpectedLiftFieldAliases:
    """The `from` field uses an alias because `from` is a Python keyword."""

    def test_from_alias_works(self):
        lift = ExpectedLift(**{"from": 0.5, "target": 0.7})
        assert lift.from_ == 0.5

    def test_from_python_name_works_too(self):
        # populate_by_name=True allows either alias or python name
        lift = ExpectedLift(from_=0.5, target=0.7)
        assert lift.from_ == 0.5
