import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class OptionsDataFetcher:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)
        self.spot_price = None
        self.options_chain = None

    def fetch_spot_price(self) -> float:
        """Fetch current spot price"""
        info = self.stock.info
        self.spot_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not self.spot_price:
            hist = self.stock.history(period="1d")
            if not hist.empty:
                self.spot_price = hist['Close'].iloc[-1]
        return self.spot_price

    def fetch_options_chain(self) -> Dict[str, pd.DataFrame]:
        """Fetch all available options data"""
        self.options_chain = {}

        try:
            expiration_dates = self.stock.options

            for exp_date in expiration_dates:
                opt = self.stock.option_chain(exp_date)

                calls = opt.calls.copy()
                puts = opt.puts.copy()

                calls['optionType'] = 'call'
                puts['optionType'] = 'put'
                calls['expirationDate'] = exp_date
                puts['expirationDate'] = exp_date

                self.options_chain[exp_date] = pd.concat([calls, puts], ignore_index=True)

        except Exception as e:
            print(f"Error fetching options for {self.ticker}: {e}")

        return self.options_chain

    def prepare_options_data(self) -> pd.DataFrame:
        """Prepare options data for IV calculation"""
        if not self.spot_price:
            self.fetch_spot_price()
        if not self.options_chain:
            self.fetch_options_chain()

        all_options = []

        for exp_date, options_df in self.options_chain.items():
            options_df = options_df.copy()

            # Calculate days to expiration
            exp_datetime = pd.to_datetime(exp_date)
            current_date = datetime.now()
            days_to_exp = (exp_datetime - current_date).days

            # Filter out options with very low volume or far OTM
            options_df = options_df[
                (options_df['volume'] > 0) &
                (options_df['openInterest'] > 0)
            ]

            if options_df.empty:
                continue

            # Add calculated fields
            options_df['daysToExpiration'] = days_to_exp
            options_df['timeToExpiration'] = days_to_exp / 365.0
            options_df['spotPrice'] = self.spot_price
            options_df['moneyness'] = options_df['strike'] / self.spot_price

            # Use mid price for better accuracy
            options_df['midPrice'] = (options_df['bid'] + options_df['ask']) / 2

            # Filter reasonable moneyness range (0.7 to 1.3)
            options_df = options_df[
                (options_df['moneyness'] >= 0.7) &
                (options_df['moneyness'] <= 1.3)
            ]

            all_options.append(options_df)

        if all_options:
            return pd.concat(all_options, ignore_index=True)
        else:
            return pd.DataFrame()


def fetch_risk_free_rate() -> float:
    """Fetch current risk-free rate (3-month Treasury yield)"""
    try:
        treasury = yf.Ticker("^IRX")  # 13-week Treasury Bill
        hist = treasury.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1] / 100  # Convert percentage to decimal
    except:
        pass

    # Fallback to a reasonable estimate
    return 0.045  # 4.5% as of late 2024