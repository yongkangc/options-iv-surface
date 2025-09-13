#!/usr/bin/env python3
"""
Implied Volatility Surface Construction for Options
Tickers: NVDA, GOOGL, COIN, TSLA
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from options_data import OptionsDataFetcher, fetch_risk_free_rate
from iv_calculator import calculate_iv_for_dataframe
from visualization import IVSurfaceVisualizer


def process_ticker(ticker: str, risk_free_rate: float, output_dir: str = 'output'):
    """Process a single ticker to generate IV surface"""
    print(f"\n{'='*60}")
    print(f"Processing {ticker}")
    print(f"{'='*60}")

    try:
        # Fetch options data
        print(f"Fetching options data for {ticker}...")
        fetcher = OptionsDataFetcher(ticker)
        spot_price = fetcher.fetch_spot_price()
        print(f"Spot price: ${spot_price:.2f}")

        options_chain = fetcher.fetch_options_chain()
        print(f"Found {len(options_chain)} expiration dates")

        # Prepare data
        options_df = fetcher.prepare_options_data()
        if options_df.empty:
            print(f"No valid options data found for {ticker}")
            return None

        print(f"Total options contracts: {len(options_df)}")

        # Calculate implied volatility
        print("Calculating implied volatilities...")
        options_with_iv = calculate_iv_for_dataframe(options_df, risk_free_rate)
        print(f"Successfully calculated IV for {len(options_with_iv)} contracts")

        # Filter outliers
        options_with_iv = options_with_iv[
            (options_with_iv['impliedVolatility'] > 0.05) &
            (options_with_iv['impliedVolatility'] < 3.0)
        ]

        # Create visualizations
        print("Generating visualizations...")
        visualizer = IVSurfaceVisualizer(ticker, options_with_iv)

        # Generate comprehensive report
        report_dir = visualizer.generate_report(output_dir)

        # Print summary statistics
        print(f"\n{ticker} IV Statistics:")
        print("-" * 40)

        for option_type in ['call', 'put']:
            type_df = options_with_iv[options_with_iv['optionType'] == option_type]
            if not type_df.empty:
                print(f"\n{option_type.capitalize()}s:")
                print(f"  Mean IV: {type_df['impliedVolatility'].mean()*100:.2f}%")
                print(f"  Min IV:  {type_df['impliedVolatility'].min()*100:.2f}%")
                print(f"  Max IV:  {type_df['impliedVolatility'].max()*100:.2f}%")
                print(f"  Std IV:  {type_df['impliedVolatility'].std()*100:.2f}%")

        return options_with_iv

    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function to process all tickers"""
    # Configuration
    TICKERS = ['NVDA', 'GOOGL', 'COIN', 'TSLA']
    OUTPUT_DIR = 'iv_surface_output'

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Fetch risk-free rate
    print("Fetching risk-free rate...")
    risk_free_rate = fetch_risk_free_rate()
    print(f"Risk-free rate: {risk_free_rate*100:.2f}%")

    # Process each ticker
    results = {}
    for ticker in TICKERS:
        result = process_ticker(ticker, risk_free_rate, OUTPUT_DIR)
        if result is not None:
            results[ticker] = result

    # Generate summary report
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}")

    summary_data = []
    for ticker, df in results.items():
        for option_type in ['call', 'put']:
            type_df = df[df['optionType'] == option_type]
            if not type_df.empty:
                summary_data.append({
                    'Ticker': ticker,
                    'Type': option_type.capitalize(),
                    'Count': len(type_df),
                    'Mean IV (%)': f"{type_df['impliedVolatility'].mean()*100:.2f}",
                    'Min IV (%)': f"{type_df['impliedVolatility'].min()*100:.2f}",
                    'Max IV (%)': f"{type_df['impliedVolatility'].max()*100:.2f}",
                    'ATM IV (%)': f"{type_df[type_df['moneyness'].between(0.98, 1.02)]['impliedVolatility'].mean()*100:.2f}"
                    if not type_df[type_df['moneyness'].between(0.98, 1.02)].empty else 'N/A'
                })

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        print("\n" + summary_df.to_string(index=False))

        # Save summary
        summary_df.to_csv(os.path.join(OUTPUT_DIR, 'iv_surface_summary.csv'), index=False)
        print(f"\nAll reports saved to: {os.path.abspath(OUTPUT_DIR)}/")

    print("\nProcessing complete!")


if __name__ == "__main__":
    main()