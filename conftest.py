"""
Pytest configuration and shared fixtures for testing
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def sample_options_data():
    """Generate sample options data for testing"""
    strikes = [90, 95, 100, 105, 110]
    expirations = [30, 60, 90]  # Days to expiration

    data = []
    spot_price = 100

    for days in expirations:
        exp_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        time_to_exp = days / 365.0

        for strike in strikes:
            moneyness = strike / spot_price

            # Generate reasonable IV based on moneyness (smile effect)
            base_iv = 0.20
            smile_adjustment = 0.1 * abs(np.log(moneyness))
            iv = base_iv + smile_adjustment

            # Calculate approximate option prices
            for option_type in ['call', 'put']:
                if option_type == 'call':
                    intrinsic = max(spot_price - strike, 0)
                    time_value = spot_price * iv * np.sqrt(time_to_exp) * 0.4
                else:
                    intrinsic = max(strike - spot_price, 0)
                    time_value = strike * iv * np.sqrt(time_to_exp) * 0.4

                mid_price = intrinsic + time_value
                spread = mid_price * 0.05  # 5% spread

                data.append({
                    'strike': strike,
                    'expirationDate': exp_date,
                    'daysToExpiration': days,
                    'timeToExpiration': time_to_exp,
                    'optionType': option_type,
                    'bid': mid_price - spread/2,
                    'ask': mid_price + spread/2,
                    'midPrice': mid_price,
                    'volume': np.random.randint(10, 1000),
                    'openInterest': np.random.randint(100, 10000),
                    'impliedVolatility': iv,
                    'spotPrice': spot_price,
                    'moneyness': moneyness
                })

    return pd.DataFrame(data)


@pytest.fixture
def black_scholes_test_cases():
    """Standard test cases for Black-Scholes calculations"""
    return [
        # (S, K, T, r, sigma, call_price, put_price)
        (100, 100, 1.0, 0.05, 0.20, 10.45, 5.57),  # ATM
        (100, 90, 1.0, 0.05, 0.25, 18.99, 4.65),   # ITM call / OTM put
        (100, 110, 1.0, 0.05, 0.25, 8.89, 13.65),  # OTM call / ITM put
        (100, 100, 0.25, 0.05, 0.30, 5.24, 4.00),  # Short maturity
        (100, 100, 2.0, 0.05, 0.15, 12.34, 3.86),  # Long maturity
    ]


@pytest.fixture
def iv_surface_data():
    """Generate data suitable for IV surface construction"""
    np.random.seed(42)

    strikes = np.arange(80, 121, 5)
    days_to_exp = [7, 14, 30, 60, 90, 120, 180]

    data = []
    spot_price = 100

    for days in days_to_exp:
        time_to_exp = days / 365.0

        for strike in strikes:
            moneyness = strike / spot_price

            # Create realistic IV surface with smile and term structure
            atm_iv = 0.18 + 0.02 * np.sqrt(time_to_exp)  # Term structure
            smile = 0.15 * (abs(np.log(moneyness)) ** 1.5)  # Smile effect
            iv = atm_iv + smile + np.random.normal(0, 0.01)  # Add noise

            for option_type in ['call', 'put']:
                data.append({
                    'strike': strike,
                    'daysToExpiration': days,
                    'timeToExpiration': time_to_exp,
                    'optionType': option_type,
                    'impliedVolatility': max(0.05, min(iv, 2.0)),  # Bound IV
                    'spotPrice': spot_price,
                    'moneyness': moneyness,
                    'expirationDate': (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                })

    return pd.DataFrame(data)


@pytest.fixture
def mock_yfinance_ticker(monkeypatch):
    """Mock yfinance Ticker for testing without API calls"""
    class MockTicker:
        def __init__(self, symbol):
            self.symbol = symbol
            self.info = {
                'currentPrice': 100.0,
                'regularMarketPrice': 100.0,
                'bid': 99.95,
                'ask': 100.05
            }
            self.options = ['2024-01-19', '2024-02-16', '2024-03-15']

        def history(self, period="1d"):
            return pd.DataFrame({'Close': [100.0]})

        def option_chain(self, date):
            strikes = [90, 95, 100, 105, 110]

            calls = pd.DataFrame({
                'strike': strikes,
                'bid': [11, 7, 4, 2, 0.5],
                'ask': [12, 8, 5, 3, 1.5],
                'volume': [100, 200, 500, 300, 150],
                'openInterest': [1000, 2000, 5000, 3000, 1500],
                'lastPrice': [11.5, 7.5, 4.5, 2.5, 1.0],
                'impliedVolatility': [0.18, 0.19, 0.20, 0.21, 0.22]
            })

            puts = pd.DataFrame({
                'strike': strikes,
                'bid': [0.5, 2, 4, 7, 11],
                'ask': [1.5, 3, 5, 8, 12],
                'volume': [150, 300, 500, 200, 100],
                'openInterest': [1500, 3000, 5000, 2000, 1000],
                'lastPrice': [1.0, 2.5, 4.5, 7.5, 11.5],
                'impliedVolatility': [0.22, 0.21, 0.20, 0.19, 0.18]
            })

            class MockOptionChain:
                def __init__(self):
                    self.calls = calls
                    self.puts = puts

            return MockOptionChain()

    monkeypatch.setattr("yfinance.Ticker", MockTicker)
    return MockTicker