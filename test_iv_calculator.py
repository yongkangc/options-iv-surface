"""
Unit tests for Black-Scholes implied volatility calculator
"""

import pytest
import numpy as np
from iv_calculator import ImpliedVolatilityCalculator


class TestBlackScholes:
    """Test Black-Scholes pricing functions"""

    def setup_method(self):
        self.calc = ImpliedVolatilityCalculator()
        self.tolerance = 1e-6

    def test_call_option_atm(self):
        """Test ATM call option pricing"""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        price = self.calc.black_scholes_call(S, K, T, r, sigma)
        # Approximate expected value for ATM call
        assert 8 < price < 12, f"ATM call price {price} outside expected range"

    def test_put_option_atm(self):
        """Test ATM put option pricing"""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        price = self.calc.black_scholes_put(S, K, T, r, sigma)
        # Approximate expected value for ATM put
        assert 5 < price < 9, f"ATM put price {price} outside expected range"

    def test_put_call_parity(self):
        """Test put-call parity relationship"""
        S, K, T, r, sigma = 100, 110, 1, 0.05, 0.25
        call_price = self.calc.black_scholes_call(S, K, T, r, sigma)
        put_price = self.calc.black_scholes_put(S, K, T, r, sigma)

        # Put-Call Parity: C - P = S - K*exp(-rT)
        parity_lhs = call_price - put_price
        parity_rhs = S - K * np.exp(-r * T)

        assert abs(parity_lhs - parity_rhs) < self.tolerance, \
            f"Put-call parity violated: {parity_lhs} != {parity_rhs}"

    def test_deep_itm_call(self):
        """Test deep in-the-money call option"""
        S, K, T, r, sigma = 150, 100, 1, 0.05, 0.2
        price = self.calc.black_scholes_call(S, K, T, r, sigma)
        intrinsic = S - K
        assert price > intrinsic, "Call price should exceed intrinsic value"
        assert price < S, "Call price should be less than spot"

    def test_deep_otm_call(self):
        """Test deep out-of-the-money call option"""
        S, K, T, r, sigma = 50, 100, 1, 0.05, 0.2
        price = self.calc.black_scholes_call(S, K, T, r, sigma)
        assert price > 0, "OTM call should have positive value"
        assert price < 1, "Deep OTM call should have small value"

    def test_zero_time_to_expiry(self):
        """Test options at expiration"""
        S, K, T, r, sigma = 110, 100, 0, 0.05, 0.2

        call_price = self.calc.black_scholes_call(S, K, T, r, sigma)
        put_price = self.calc.black_scholes_put(S, K, T, r, sigma)

        assert abs(call_price - 10) < self.tolerance, "Call at expiry should equal intrinsic"
        assert abs(put_price - 0) < self.tolerance, "Put at expiry should be worthless"

    def test_vega_calculation(self):
        """Test vega calculation"""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
        vega = self.calc.vega(S, K, T, r, sigma)

        assert vega > 0, "Vega should be positive"
        assert vega < S, "Vega should be bounded"


class TestImpliedVolatility:
    """Test implied volatility calculation methods"""

    def setup_method(self):
        self.calc = ImpliedVolatilityCalculator()
        self.tolerance = 1e-4

    def test_iv_newton_call(self):
        """Test Newton-Raphson IV calculation for calls"""
        S, K, T, r = 100, 100, 1, 0.05
        true_sigma = 0.25

        # Calculate option price with known volatility
        option_price = self.calc.black_scholes_call(S, K, T, r, true_sigma)

        # Calculate implied volatility
        iv = self.calc.implied_volatility_newton(option_price, S, K, T, r, 'call')

        assert iv is not None, "IV calculation failed"
        assert abs(iv - true_sigma) < self.tolerance, \
            f"IV {iv} differs from true volatility {true_sigma}"

    def test_iv_newton_put(self):
        """Test Newton-Raphson IV calculation for puts"""
        S, K, T, r = 100, 110, 1, 0.05
        true_sigma = 0.30

        option_price = self.calc.black_scholes_put(S, K, T, r, true_sigma)
        iv = self.calc.implied_volatility_newton(option_price, S, K, T, r, 'put')

        assert iv is not None, "IV calculation failed"
        assert abs(iv - true_sigma) < self.tolerance, \
            f"IV {iv} differs from true volatility {true_sigma}"

    def test_iv_bisection_call(self):
        """Test bisection IV calculation for calls"""
        S, K, T, r = 100, 95, 0.5, 0.05
        true_sigma = 0.20

        option_price = self.calc.black_scholes_call(S, K, T, r, true_sigma)
        iv = self.calc.implied_volatility_bisection(option_price, S, K, T, r, 'call')

        assert iv is not None, "IV calculation failed"
        assert abs(iv - true_sigma) < self.tolerance, \
            f"IV {iv} differs from true volatility {true_sigma}"

    def test_iv_extreme_values(self):
        """Test IV calculation with extreme values"""
        S, K, T, r = 100, 100, 1, 0.05

        # Very high volatility
        high_sigma = 2.0
        option_price = self.calc.black_scholes_call(S, K, T, r, high_sigma)
        iv = self.calc.calculate_iv(option_price, S, K, T, r, 'call')
        assert iv is not None and 1.5 < iv < 2.5, "High volatility IV failed"

        # Very low volatility
        low_sigma = 0.05
        option_price = self.calc.black_scholes_call(S, K, T, r, low_sigma)
        iv = self.calc.calculate_iv(option_price, S, K, T, r, 'call')
        assert iv is not None and 0.01 < iv < 0.1, "Low volatility IV failed"

    def test_iv_arbitrage_violation(self):
        """Test IV calculation with arbitrage violations"""
        S, K, T, r = 100, 100, 1, 0.05

        # Option price below intrinsic value (arbitrage)
        option_price = 0.5  # Below intrinsic for ATM
        iv = self.calc.calculate_iv(option_price, S, K, T, r, 'call')
        assert iv is None, "Should return None for arbitrage violation"

    def test_iv_invalid_inputs(self):
        """Test IV calculation with invalid inputs"""
        # Negative price
        iv = self.calc.calculate_iv(-10, 100, 100, 1, 0.05, 'call')
        assert iv is None, "Should return None for negative price"

        # Zero time
        iv = self.calc.calculate_iv(10, 100, 100, 0, 0.05, 'call')
        assert iv is None, "Should return None for zero time"

        # Negative strike
        iv = self.calc.calculate_iv(10, 100, -100, 1, 0.05, 'call')
        assert iv is None, "Should return None for negative strike"


class TestIVConvergence:
    """Test convergence properties of IV calculations"""

    def setup_method(self):
        self.calc = ImpliedVolatilityCalculator()

    def test_iv_grid_convergence(self):
        """Test IV calculation across a grid of strikes and maturities"""
        S = 100
        strikes = np.linspace(80, 120, 9)
        maturities = [0.25, 0.5, 1.0, 2.0]
        r = 0.05
        true_sigma = 0.25

        errors = []
        for K in strikes:
            for T in maturities:
                # Test calls
                call_price = self.calc.black_scholes_call(S, K, T, r, true_sigma)
                call_iv = self.calc.calculate_iv(call_price, S, K, T, r, 'call')

                if call_iv is not None:
                    errors.append(abs(call_iv - true_sigma))

                # Test puts
                put_price = self.calc.black_scholes_put(S, K, T, r, true_sigma)
                put_iv = self.calc.calculate_iv(put_price, S, K, T, r, 'put')

                if put_iv is not None:
                    errors.append(abs(put_iv - true_sigma))

        # Check convergence accuracy
        assert len(errors) > 0, "No successful IV calculations"
        mean_error = np.mean(errors)
        max_error = np.max(errors)

        assert mean_error < 1e-4, f"Mean error {mean_error} too large"
        assert max_error < 1e-3, f"Max error {max_error} too large"

    def test_newton_vs_bisection(self):
        """Compare Newton and bisection methods"""
        test_cases = [
            (100, 100, 1, 0.05, 0.20),   # ATM
            (100, 90, 1, 0.05, 0.25),    # ITM
            (100, 110, 1, 0.05, 0.30),   # OTM
            (100, 100, 0.1, 0.05, 0.40), # Short maturity
            (100, 100, 2, 0.05, 0.15),   # Long maturity
        ]

        for S, K, T, r, true_sigma in test_cases:
            option_price = self.calc.black_scholes_call(S, K, T, r, true_sigma)

            iv_newton = self.calc.implied_volatility_newton(
                option_price, S, K, T, r, 'call'
            )
            iv_bisection = self.calc.implied_volatility_bisection(
                option_price, S, K, T, r, 'call'
            )

            if iv_newton is not None and iv_bisection is not None:
                assert abs(iv_newton - iv_bisection) < 1e-5, \
                    f"Newton {iv_newton} and bisection {iv_bisection} disagree"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])