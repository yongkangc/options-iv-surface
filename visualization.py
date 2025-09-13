import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go
from scipy.interpolate import griddata
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class IVSurfaceVisualizer:
    def __init__(self, ticker: str, options_df: pd.DataFrame):
        self.ticker = ticker
        self.options_df = options_df
        self.spot_price = options_df['spotPrice'].iloc[0] if not options_df.empty else 100

    def prepare_surface_data(self, option_type: str = 'call'):
        """Prepare data for surface plotting"""
        df = self.options_df[self.options_df['optionType'] == option_type].copy()

        if df.empty:
            return None, None, None

        # Get unique values
        strikes = df['strike'].values
        times = df['timeToExpiration'].values
        ivs = df['impliedVolatility'].values

        # Create grid
        strike_range = np.linspace(strikes.min(), strikes.max(), 50)
        time_range = np.linspace(times.min(), times.max(), 50)
        strike_grid, time_grid = np.meshgrid(strike_range, time_range)

        # Interpolate IV values
        try:
            iv_grid = griddata(
                (strikes, times),
                ivs,
                (strike_grid, time_grid),
                method='cubic'
            )
        except:
            # Fallback to linear interpolation if cubic fails
            iv_grid = griddata(
                (strikes, times),
                ivs,
                (strike_grid, time_grid),
                method='linear'
            )

        return strike_grid, time_grid, iv_grid

    def plot_3d_surface_matplotlib(self, option_type: str = 'call', save_path: str = None):
        """Create 3D surface plot using matplotlib"""
        strike_grid, time_grid, iv_grid = self.prepare_surface_data(option_type)

        if strike_grid is None:
            print(f"No data available for {option_type} options")
            return

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Plot surface
        surf = ax.plot_surface(
            strike_grid,
            time_grid * 365,  # Convert to days
            iv_grid * 100,  # Convert to percentage
            cmap='viridis',
            alpha=0.8,
            edgecolor='none'
        )

        # Add data points
        df = self.options_df[self.options_df['optionType'] == option_type]
        ax.scatter(
            df['strike'],
            df['timeToExpiration'] * 365,
            df['impliedVolatility'] * 100,
            c='red',
            s=20,
            alpha=0.5,
            label='Market Data'
        )

        # Labels and title
        ax.set_xlabel('Strike Price ($)', fontsize=10)
        ax.set_ylabel('Days to Expiration', fontsize=10)
        ax.set_zlabel('Implied Volatility (%)', fontsize=10)
        ax.set_title(f'{self.ticker} Implied Volatility Surface ({option_type.capitalize()}s)', fontsize=12)

        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

        # Add spot price line
        ax.plot([self.spot_price, self.spot_price],
                [time_grid.min() * 365, time_grid.max() * 365],
                [iv_grid.min() * 100, iv_grid.max() * 100],
                'r--', linewidth=2, label=f'Spot: ${self.spot_price:.2f}')

        ax.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

        return fig

    def plot_3d_surface_plotly(self, option_type: str = 'call', save_html: str = None):
        """Create interactive 3D surface plot using plotly"""
        strike_grid, time_grid, iv_grid = self.prepare_surface_data(option_type)

        if strike_grid is None:
            print(f"No data available for {option_type} options")
            return

        # Create surface plot
        surface = go.Surface(
            x=strike_grid,
            y=time_grid * 365,  # Convert to days
            z=iv_grid * 100,  # Convert to percentage
            colorscale='Viridis',
            name='IV Surface',
            showscale=True,
            colorbar=dict(title='IV (%)')
        )

        # Add market data points
        df = self.options_df[self.options_df['optionType'] == option_type]
        scatter = go.Scatter3d(
            x=df['strike'],
            y=df['timeToExpiration'] * 365,
            z=df['impliedVolatility'] * 100,
            mode='markers',
            marker=dict(
                size=3,
                color='red',
                opacity=0.6
            ),
            name='Market Data'
        )

        # Create figure
        fig = go.Figure(data=[surface, scatter])

        # Update layout
        fig.update_layout(
            title=f'{self.ticker} Implied Volatility Surface ({option_type.capitalize()}s)',
            scene=dict(
                xaxis_title='Strike Price ($)',
                yaxis_title='Days to Expiration',
                zaxis_title='Implied Volatility (%)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.3)
                )
            ),
            width=1000,
            height=800,
            showlegend=True
        )

        if save_html:
            fig.write_html(save_html)
        else:
            fig.show()

        return fig

    def plot_volatility_smile(self, expiration_dates: list = None, save_path: str = None):
        """Plot volatility smile for specific expiration dates"""
        if expiration_dates is None:
            # Select a few expiration dates
            unique_dates = self.options_df['expirationDate'].unique()
            expiration_dates = unique_dates[:min(4, len(unique_dates))]

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        for option_type, ax in zip(['call', 'put'], axes):
            for exp_date in expiration_dates:
                df = self.options_df[
                    (self.options_df['optionType'] == option_type) &
                    (self.options_df['expirationDate'] == exp_date)
                ].sort_values('strike')

                if not df.empty:
                    ax.plot(
                        df['strike'],
                        df['impliedVolatility'] * 100,
                        marker='o',
                        label=f"{exp_date} ({df['daysToExpiration'].iloc[0]}d)"
                    )

            # Add spot price line
            ax.axvline(x=self.spot_price, color='red', linestyle='--',
                      alpha=0.5, label=f'Spot: ${self.spot_price:.2f}')

            ax.set_xlabel('Strike Price ($)')
            ax.set_ylabel('Implied Volatility (%)')
            ax.set_title(f'{self.ticker} Volatility Smile ({option_type.capitalize()}s)')
            ax.legend()
            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

        return fig

    def plot_term_structure(self, moneyness_levels: list = None, save_path: str = None):
        """Plot volatility term structure for different moneyness levels"""
        if moneyness_levels is None:
            moneyness_levels = [0.9, 0.95, 1.0, 1.05, 1.1]

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        for option_type, ax in zip(['call', 'put'], axes):
            df = self.options_df[self.options_df['optionType'] == option_type].copy()

            for moneyness in moneyness_levels:
                # Find options closest to target moneyness for each expiration
                term_structure = []

                for exp_date in df['expirationDate'].unique():
                    exp_df = df[df['expirationDate'] == exp_date]
                    # Find closest moneyness
                    idx = (exp_df['moneyness'] - moneyness).abs().idxmin()
                    if idx is not None and not pd.isna(idx):
                        term_structure.append({
                            'days': exp_df.loc[idx, 'daysToExpiration'],
                            'iv': exp_df.loc[idx, 'impliedVolatility'],
                            'actual_moneyness': exp_df.loc[idx, 'moneyness']
                        })

                if term_structure:
                    ts_df = pd.DataFrame(term_structure).sort_values('days')
                    ax.plot(
                        ts_df['days'],
                        ts_df['iv'] * 100,
                        marker='o',
                        label=f'K/S = {moneyness:.2f}'
                    )

            ax.set_xlabel('Days to Expiration')
            ax.set_ylabel('Implied Volatility (%)')
            ax.set_title(f'{self.ticker} Term Structure ({option_type.capitalize()}s)')
            ax.legend()
            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

        return fig

    def generate_report(self, output_dir: str = '.'):
        """Generate comprehensive IV surface report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create output directory
        import os
        report_dir = os.path.join(output_dir, f'{self.ticker}_iv_report_{timestamp}')
        os.makedirs(report_dir, exist_ok=True)

        # Generate all plots
        print(f"Generating IV surface report for {self.ticker}...")

        # 3D surfaces
        self.plot_3d_surface_matplotlib('call',
            save_path=os.path.join(report_dir, 'call_surface.png'))
        self.plot_3d_surface_matplotlib('put',
            save_path=os.path.join(report_dir, 'put_surface.png'))

        # Interactive HTML surfaces
        self.plot_3d_surface_plotly('call',
            save_html=os.path.join(report_dir, 'call_surface_interactive.html'))
        self.plot_3d_surface_plotly('put',
            save_html=os.path.join(report_dir, 'put_surface_interactive.html'))

        # Volatility smile
        self.plot_volatility_smile(
            save_path=os.path.join(report_dir, 'volatility_smile.png'))

        # Term structure
        self.plot_term_structure(
            save_path=os.path.join(report_dir, 'term_structure.png'))

        # Save data to CSV
        self.options_df.to_csv(
            os.path.join(report_dir, 'options_data_with_iv.csv'),
            index=False
        )

        print(f"Report saved to: {report_dir}")
        return report_dir