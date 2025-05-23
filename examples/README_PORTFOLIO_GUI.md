# Schwab Portfolio GUI

A comprehensive GUI application for managing and monitoring your Schwab trading accounts.

## Features

- Real-time portfolio overview with positions and balances
- Order entry with support for stocks, options, and multi-leg strategies
- Live market data streaming
- Order monitoring and management
- Performance tracking and analytics
- Multi-account support

## Prerequisites

1. **Schwab Developer Account**: You need to register at [developer.schwab.com](https://developer.schwab.com)
2. **API Credentials**: Create an app to get your Client ID and Client Secret
3. **Python 3.8+**: Required for running the application

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Clear Demo Credentials

The portfolio GUI database may contain demo/test credentials. Clear them first:

```bash
python examples/setup_credentials.py
```

### 3. Configure Your API Credentials

You'll need:
- **Client ID**: From your Schwab developer app
- **Client Secret**: From your Schwab developer app  
- **Redirect URI**: For example `https://localhost:8443/callback`

### 4. Run the Application

```bash
python examples/portfolio_gui.py
```

### 5. Initial Setup

1. Click the "Connect" button in the toolbar
2. Enter your API credentials when prompted
3. Follow the OAuth authentication flow:
   - A browser will open to Schwab's login page
   - Log in with your Schwab account
   - Authorize the application
   - Copy the full redirect URL (even if it shows "connection refused")
   - Paste it back into the application

## Troubleshooting

### "400 Bad Request" Error

This typically means:
- Invalid or expired credentials
- Missing authentication token
- Demo/test credentials being used

**Solution**: Run `setup_credentials.py` to clear the database and re-authenticate.

### "No access token available" Error

This means you haven't completed the OAuth flow yet.

**Solution**: Click "Connect" and complete the authentication process.

### Token Expiration

Schwab tokens expire after a certain period. The app will try to refresh automatically, but if it fails:

**Solution**: Re-authenticate through Settings > Authentication > Re-authenticate

## Security Notes

- Your credentials are stored locally in an SQLite database
- Never share your Client Secret
- The database file (`portfolio_gui.db`) contains sensitive information
- Consider encrypting the database file for production use

## Database Location

The application stores data in: `examples/portfolio_gui.db`

To completely reset the application:
```bash
rm examples/portfolio_gui.db
```

## Features Overview

### Portfolio Tab
- Total account value and cash balances
- Day change and performance metrics
- Asset allocation pie chart
- Account summary cards

### Positions Tab
- Detailed position list with P&L
- Real-time quote updates
- Position analytics

### Orders Tab
- Open orders monitoring
- Order history
- Quick order modification/cancellation

### Activity Tab
- Transaction history
- Trade confirmations
- Account activity log

### Performance Tab
- Returns analysis
- Performance charts
- Benchmark comparisons

## Support

For issues related to:
- **API Access**: Contact Schwab Developer Support
- **Application Bugs**: Open an issue on GitHub
- **Authentication**: Ensure your app is properly configured at developer.schwab.com