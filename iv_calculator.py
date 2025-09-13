import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize_scalar, brentq
from typing import Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class ImpliedVolatilityCalculator:
    """Calculate implied volatility using Black-Scholes model"""

    @staticmethod
    def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes call option price"""
        if T <= 0:
            return max(S - K, 0)

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call_price

    @staticmethod
    def black_scholes_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes put option price"""
        if T <= 0:
            return max(K - S, 0)

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return put_price

    @staticmethod
    def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate vega (sensitivity to volatility)"""
        if T <= 0:
            return 0

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        return S * norm.pdf(d1) * np.sqrt(T)

    def implied_volatility_newton(
        self,
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = 'call',
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> Optional[float]:
        """Calculate IV using Newton-Raphson method"""
        if T <= 0:
            return None

        # Initial guess using Brenner-Subrahmanyam approximation
        sigma = np.sqrt(2 * np.pi / T) * (option_price / S)
        sigma = max(0.01, min(sigma, 3.0))  # Bound initial guess

        bs_func = self.black_scholes_call if option_type == 'call' else self.black_scholes_put

        for _ in range(max_iterations):
            price = bs_func(S, K, T, r, sigma)
            vega_val = self.vega(S, K, T, r, sigma)

            if abs(vega_val) < 1e-10:
                break

            price_diff = option_price - price

            if abs(price_diff) < tolerance:
                return sigma

            sigma = sigma + price_diff / vega_val
            sigma = max(0.001, min(sigma, 5.0))  # Keep sigma in reasonable bounds

        return None

    def implied_volatility_bisection(
        self,
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = 'call',
        tolerance: float = 1e-6
    ) -> Optional[float]:
        """Calculate IV using bisection method (more robust)"""
        if T <= 0:
            return None

        bs_func = self.black_scholes_call if option_type == 'call' else self.black_scholes_put

        def objective(sigma):
            return bs_func(S, K, T, r, sigma) - option_price

        try:
            # Find bounds where function changes sign
            low_vol, high_vol = 0.001, 5.0

            # Check if solution exists in range
            if objective(low_vol) * objective(high_vol) > 0:
                # Try Newton method as fallback
                return self.implied_volatility_newton(option_price, S, K, T, r, option_type)

            iv = brentq(objective, low_vol, high_vol, xtol=tolerance)
            return iv

        except Exception:
            return None

    def calculate_iv(
        self,
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = 'call',
        method: str = 'newton'
    ) -> Optional[float]:
        """Main method to calculate implied volatility"""
        # Validate inputs
        if option_price <= 0 or S <= 0 or K <= 0 or T <= 0:
            return None

        # Check for arbitrage violations
        if option_type == 'call':
            intrinsic = max(S - K, 0)
        else:
            intrinsic = max(K - S, 0)

        if option_price < intrinsic:
            return None

        # Calculate IV
        if method == 'newton':
            iv = self.implied_volatility_newton(option_price, S, K, T, r, option_type)
        else:
            iv = self.implied_volatility_bisection(option_price, S, K, T, r, option_type)

        # Validate result
        if iv and 0.01 <= iv <= 5.0:
            return iv
        return None


def calculate_iv_for_dataframe(df, risk_free_rate: float = 0.045):
    """Calculate IV for entire options dataframe"""
    calculator = ImpliedVolatilityCalculator()
    ivs = []

    for _, row in df.iterrows():
        iv = calculator.calculate_iv(
            option_price=row['midPrice'],
            S=row['spotPrice'],
            K=row['strike'],
            T=row['timeToExpiration'],
            r=risk_free_rate,
            option_type=row['optionType'],
            method='newton'
        )

        # If Newton fails, try bisection
        if iv is None:
            iv = calculator.calculate_iv(
                option_price=row['midPrice'],
                S=row['spotPrice'],
                K=row['strike'],
                T=row['timeToExpiration'],
                r=risk_free_rate,
                option_type=row['optionType'],
                method='bisection'
            )

        ivs.append(iv)

    df['impliedVolatility'] = ivs
    return df[df['impliedVolatility'].notna()]