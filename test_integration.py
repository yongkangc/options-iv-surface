"""
Integration tests for the complete IV surface construction pipeline
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from options_data import OptionsDataFetcher, fetch_risk_free_rate
from iv_calculator import calculate_iv_for_dataframe
from visualization import IVSurfaceVisualizer


class TestOptionsDataFetcher:
    """Test options data fetching and preparation"""

    @patch('yfinance.Ticker')
    def test_fetch_spot_price(self, mock_ticker):
        """Test spot price fetching"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.info = {'currentPrice': 150.50}
        mock_ticker.return_value = mock_instance

        fetcher = OptionsDataFetcher('TEST')
        price = fetcher.fetch_spot_price()

        assert price == 150.50
        mock_ticker.assert_called_once_with('TEST')

    @patch('yfinance.Ticker')
    def test_fetch_spot_price_fallback(self, mock_ticker):
        """Test spot price fetching with fallback to history"""
        # Setup mock with no current price
        mock_instance = Mock()
        mock_instance.info = {}

        # Mock history data
        mock_history = pd.DataFrame({'Close': [148.75]})
        mock_instance.history.return_value = mock_history

        mock_ticker.return_value = mock_instance

        fetcher = OptionsDataFetcher('TEST')
        price = fetcher.fetch_spot_price()

        assert price == 148.75

    def test_prepare_options_data_filtering(self):
        """Test options data preparation and filtering"""
        fetcher = OptionsDataFetcher('TEST')
        fetcher.spot_price = 100

        # Create sample options data
        exp_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        sample_options = pd.DataFrame({
            'strike': [90, 95, 100, 105, 110, 150, 200],
            'bid': [12, 8, 5, 3, 1.5, 0.1, 0.01],
            'ask': [13, 9, 6, 4, 2.5, 0.2, 0.02],
            'volume': [100, 200, 500, 300, 150, 5, 0],
            'openInterest': [1000, 2000, 5000, 3000, 1500, 10, 0],
            'optionType': ['call'] * 7,
            'expirationDate': [exp_date] * 7
        })

        fetcher.options_chain = {exp_date: sample_options}
        prepared_df = fetcher.prepare_options_data()

        # Check filtering
        assert len(prepared_df) > 0, "Should have some valid options"
        assert len(prepared_df) < 7, "Should filter out zero volume/OI options"
        assert all(prepared_df['volume'] > 0), "All options should have volume"
        assert all(prepared_df['openInterest'] > 0), "All options should have OI"

        # Check calculated fields
        assert 'timeToExpiration' in prepared_df.columns
        assert 'moneyness' in prepared_df.columns
        assert 'midPrice' in prepared_df.columns

        # Check moneyness filtering (0.7 to 1.3)
        assert all(prepared_df['moneyness'] >= 0.7)
        assert all(prepared_df['moneyness'] <= 1.3)


class TestIVCalculation:
    """Test IV calculation on dataframes"""

    def test_calculate_iv_for_dataframe(self):
        """Test IV calculation for a sample dataframe"""
        # Create test data
        test_df = pd.DataFrame({
            'midPrice': [10.5, 5.2, 1.8, 8.3, 3.1],
            'spotPrice': [100] * 5,
            'strike': [90, 95, 100, 105, 110],
            'timeToExpiration': [0.25] * 5,
            'optionType': ['call', 'call', 'call', 'put', 'put']
        })

        result_df = calculate_iv_for_dataframe(test_df, risk_free_rate=0.05)

        # Check IV calculation
        assert 'impliedVolatility' in result_df.columns
        assert len(result_df) <= len(test_df), "Should not add rows"
        assert all(result_df['impliedVolatility'] > 0), "All IVs should be positive"
        assert all(result_df['impliedVolatility'] < 5), "IVs should be reasonable"

    def test_calculate_iv_handles_failures(self):
        """Test that IV calculation handles failures gracefully"""
        # Create test data with some problematic values
        test_df = pd.DataFrame({
            'midPrice': [0.01, -5, 100, 5.5],  # Very low, negative, very high prices
            'spotPrice': [100] * 4,
            'strike': [200, 100, 50, 100],
            'timeToExpiration': [0.25] * 4,
            'optionType': ['call', 'call', 'call', 'put']
        })

        result_df = calculate_iv_for_dataframe(test_df, risk_free_rate=0.05)

        # Should handle bad data gracefully
        assert len(result_df) >= 0, "Should return valid rows only"
        if len(result_df) > 0:
            assert all(result_df['impliedVolatility'].notna()), "Should filter NaN IVs"


class TestVisualization:
    """Test visualization components"""

    def setup_method(self):
        """Setup test data for visualization"""
        self.test_data = pd.DataFrame({
            'strike': np.repeat([90, 95, 100, 105, 110], 3),
            'timeToExpiration': np.tile([0.25, 0.5, 1.0], 5),
            'impliedVolatility': np.random.uniform(0.15, 0.35, 15),
            'optionType': ['call'] * 15,
            'spotPrice': [100] * 15,
            'expirationDate': np.tile(['2024-01-30', '2024-02-28', '2024-04-30'], 5),
            'daysToExpiration': np.tile([30, 60, 120], 5),
            'moneyness': np.repeat([0.9, 0.95, 1.0, 1.05, 1.1], 3)
        })

    def test_surface_data_preparation(self):
        """Test surface data preparation for plotting"""
        viz = IVSurfaceVisualizer('TEST', self.test_data)
        strike_grid, time_grid, iv_grid = viz.prepare_surface_data('call')

        assert strike_grid is not None, "Should return strike grid"
        assert time_grid is not None, "Should return time grid"
        assert iv_grid is not None, "Should return IV grid"

        # Check grid dimensions
        assert strike_grid.shape == time_grid.shape, "Grids should have same shape"
        assert strike_grid.shape == iv_grid.shape, "IV grid should match strike/time grids"

    def test_empty_data_handling(self):
        """Test visualization with empty data"""
        empty_df = pd.DataFrame()
        viz = IVSurfaceVisualizer('TEST', empty_df)

        strike_grid, time_grid, iv_grid = viz.prepare_surface_data('call')
        assert strike_grid is None, "Should return None for empty data"

    @patch('matplotlib.pyplot.show')
    def test_plot_generation(self, mock_show):
        """Test that plots can be generated without errors"""
        viz = IVSurfaceVisualizer('TEST', self.test_data)

        # Test matplotlib surface plot
        fig = viz.plot_3d_surface_matplotlib('call')
        assert fig is not None, "Should return figure object"

        # Test volatility smile
        fig = viz.plot_volatility_smile()
        assert fig is not None, "Should return figure object"

        # Test term structure
        fig = viz.plot_term_structure()
        assert fig is not None, "Should return figure object"


class TestEndToEndPipeline:
    """Test the complete pipeline from data fetching to visualization"""

    @patch('yfinance.Ticker')
    def test_full_pipeline(self, mock_ticker):
        """Test complete pipeline with mocked data"""
        # Setup mock ticker
        mock_instance = Mock()
        mock_instance.info = {'currentPrice': 100}
        mock_instance.options = ['2024-01-30', '2024-02-28']

        # Create mock options chain data
        calls = pd.DataFrame({
            'strike': [90, 95, 100, 105, 110],
            'bid': [11, 7, 4, 2, 0.5],
            'ask': [12, 8, 5, 3, 1.5],
            'volume': [100, 200, 500, 300, 150],
            'openInterest': [1000, 2000, 5000, 3000, 1500],
            'lastPrice': [11.5, 7.5, 4.5, 2.5, 1.0]
        })

        puts = pd.DataFrame({
            'strike': [90, 95, 100, 105, 110],
            'bid': [0.5, 2, 4, 7, 11],
            'ask': [1.5, 3, 5, 8, 12],
            'volume': [150, 300, 500, 200, 100],
            'openInterest': [1500, 3000, 5000, 2000, 1000],
            'lastPrice': [1.0, 2.5, 4.5, 7.5, 11.5]
        })

        mock_option_chain = Mock()
        mock_option_chain.calls = calls
        mock_option_chain.puts = puts

        mock_instance.option_chain.return_value = mock_option_chain
        mock_ticker.return_value = mock_instance

        # Run pipeline
        fetcher = OptionsDataFetcher('TEST')
        spot = fetcher.fetch_spot_price()
        assert spot == 100

        options_chain = fetcher.fetch_options_chain()
        assert len(options_chain) == 2

        options_df = fetcher.prepare_options_data()
        assert len(options_df) > 0

        # Calculate IVs
        options_with_iv = calculate_iv_for_dataframe(options_df, 0.05)
        assert 'impliedVolatility' in options_with_iv.columns

        # Create visualization (without actually showing)
        if len(options_with_iv) > 0:
            viz = IVSurfaceVisualizer('TEST', options_with_iv)
            assert viz.ticker == 'TEST'
            assert viz.spot_price == 100


class TestRiskFreeRate:
    """Test risk-free rate fetching"""

    @patch('yfinance.Ticker')
    def test_fetch_risk_free_rate(self, mock_ticker):
        """Test fetching risk-free rate from Treasury"""
        mock_instance = Mock()
        mock_history = pd.DataFrame({'Close': [4.25]})
        mock_instance.history.return_value = mock_history
        mock_ticker.return_value = mock_instance

        rate = fetch_risk_free_rate()
        assert rate == 0.0425, "Should convert percentage to decimal"

    @patch('yfinance.Ticker')
    def test_risk_free_rate_fallback(self, mock_ticker):
        """Test risk-free rate fallback value"""
        mock_instance = Mock()
        mock_instance.history.side_effect = Exception("API Error")
        mock_ticker.return_value = mock_instance

        rate = fetch_risk_free_rate()
        assert rate == 0.045, "Should return fallback rate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])