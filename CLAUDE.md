# Claude Code Instructions for Options and Quantitative Finance

This document provides Claude Code with specific instructions for working with this implied volatility surface construction project and options trading systems in general.

## Project Context

This is a quantitative finance project focused on options analysis, specifically constructing implied volatility surfaces for equity options. The codebase demonstrates advanced options pricing theory and market microstructure understanding.

## Core Competencies Required

### Options Theory Expertise
- Deep understanding of Black-Scholes-Merton model and its assumptions
- Greeks calculation (Delta, Gamma, Vega, Theta, Rho, and higher-order Greeks)
- Volatility smile/skew dynamics and term structure
- American vs European options pricing differences
- Early exercise boundaries and optimal exercise strategies
- Dividend handling in options pricing

### Quantitative Methods
- Numerical methods for PDE solving (finite difference, Monte Carlo)
- Optimization techniques for implied volatility calculation
- Interpolation methods for volatility surface construction (SABR, SVI, parametric models)
- Calibration techniques for model parameters
- Risk-neutral vs real-world probability measures

### Market Knowledge
- Understanding of options market microstructure
- Bid-ask spread dynamics and liquidity considerations
- Pin risk and expiration effects
- Volatility trading strategies (straddles, strangles, butterflies, condors)
- Term structure arbitrage relationships
- Put-call parity and other no-arbitrage conditions

## Code Guidelines

### When Modifying IV Calculation
1. Always validate inputs to prevent numerical instabilities
2. Use both Newton-Raphson and bisection methods for robustness
3. Handle edge cases: deep ITM/OTM, near expiration, zero volatility
4. Consider American option adjustments when applicable
5. Implement proper bounds checking (0 < IV < 500%)

### When Working with Market Data
1. Always use mid-prices for IV calculation unless specified otherwise
2. Filter by volume and open interest to ensure liquid contracts
3. Consider early exercise premium for American options
4. Account for dividends between spot and expiration
5. Handle corporate actions and special dividends

### Performance Optimizations
1. Vectorize calculations using NumPy when possible
2. Cache frequently accessed market data
3. Use analytical approximations for initial IV guesses (Brenner-Subrahmanyam)
4. Implement parallel processing for large option chains
5. Consider using QuantLib or similar libraries for complex derivatives

## Best Practices

### Data Quality
- Always validate spot prices against multiple sources
- Check for stale quotes (timestamp validation)
- Remove options with bid-ask spreads > 50% of mid price
- Flag and handle outlier IVs (typically < 5% or > 300%)
- Consider term structure arbitrage violations

### Surface Construction
- Use appropriate interpolation for sparse data regions
- Implement arbitrage-free constraints
- Ensure smooth transitions across moneyness and time
- Consider using parametric models (SABR, SVI) for better extrapolation
- Validate butterfly and calendar spread arbitrage conditions

### Risk Management Integration
- Calculate position Greeks for portfolio management
- Implement VaR and stress testing capabilities
- Consider jump risk and tail events
- Model correlation between underlyings for portfolio analysis
- Implement proper position limits and risk controls

## Common Pitfalls to Avoid

1. **Dividend Confusion**: Always clarify if dividends are included in forward prices
2. **Time Conventions**: Be consistent with day count conventions (ACT/365 vs ACT/360)
3. **Interest Rates**: Use appropriate term structure, not flat rates
4. **Volatility Units**: Always specify if volatility is annualized and in decimal or percentage
5. **Option Style**: Never assume European when American options are standard (equity options)
6. **Corporate Actions**: Account for splits, special dividends, and mergers
7. **Weekend Effect**: Consider whether to include weekends in time to expiration

## Advanced Topics to Consider

### Model Extensions
- Stochastic volatility models (Heston, SABR)
- Jump diffusion models (Merton, Kou)
- Local volatility models (Dupire)
- Rough volatility models (rBergomi)
- Machine learning for IV prediction

### Greeks and Risk Analytics
- Volga (volatility of volatility)
- Vanna (correlation between spot and volatility)
- Charm (delta decay)
- Color (gamma decay)
- Speed (rate of change of gamma)

### Trading Strategy Implementation
- Delta-neutral portfolio construction
- Gamma scalping algorithms
- Volatility arbitrage identification
- Dispersion trading systems
- Event-driven volatility strategies

## Testing Requirements

### Unit Tests Should Cover
- Boundary conditions (ATM, deep ITM/OTM)
- Put-call parity validation
- Greeks calculation accuracy
- Numerical stability across parameter ranges
- Performance benchmarks for large datasets

### Integration Tests Should Validate
- Full surface construction pipeline
- Data fetching and cleaning
- Arbitrage-free conditions
- Cross-validation with market prices
- Historical backtesting accuracy

## Performance Benchmarks

For this IV surface construction:
- Single option IV calculation: < 1ms
- Full chain (100 options): < 100ms
- Surface interpolation: < 50ms
- Complete analysis for one ticker: < 5 seconds
- Parallel processing for multiple tickers

## Recommended Enhancements

1. **Real-time Streaming**: Integrate with market data feeds
2. **Historical Analysis**: Add time series of IV surfaces
3. **Strategy Backtesting**: Implement P&L simulation
4. **Risk Analytics**: Add portfolio-level Greeks aggregation
5. **Model Comparison**: Implement alternative pricing models
6. **Market Making**: Add quote generation algorithms

## Dependencies and Libraries

### Essential for Options
- `py_vollib`: Fast Black-Scholes implementation
- `QuantLib`: Comprehensive derivatives pricing
- `mibian`: Options pricing utilities
- `arch`: Volatility modeling

### Data and Visualization
- `yfinance`: Free market data (limitations apply)
- `plotly`: Interactive 3D surfaces
- `dash`: Web-based dashboards
- `streamlit`: Quick prototype UIs

## Code Review Checklist

When reviewing options-related code:
- [ ] Verify option type (call/put) handling
- [ ] Check exercise style (American/European)
- [ ] Validate interest rate and dividend inputs
- [ ] Ensure proper time to expiration calculation
- [ ] Verify moneyness calculation
- [ ] Check for numerical stability
- [ ] Validate against known benchmarks
- [ ] Ensure arbitrage-free conditions
- [ ] Review error handling for edge cases
- [ ] Confirm performance meets requirements

## Mathematical Notation Standards

When documenting formulas:
- S or S₀: Spot price
- K: Strike price
- T: Time to maturity
- t: Current time
- r: Risk-free rate
- q: Dividend yield
- σ: Volatility
- N(·): Cumulative normal distribution
- Φ(·): Standard normal PDF

Remember: Options trading involves complex mathematics and significant financial risk. Always validate calculations against multiple sources and implement proper risk controls.