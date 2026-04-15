# Schwab Trader Test Suite

This directory contains the comprehensive test suite for the Schwab Trader Python library.

## Overview

The test suite is designed to verify all functionality of the library, including:

- Authentication (OAuth2 flow)
- Account management
- Order creation for all supported order types
- Order instructions for all instruction types
- Order management (placement, modification, cancellation)
- Market data and quotes
- Error handling and validation

## Test Structure

- `conftest.py`: Contains pytest fixtures for mocking the API client
- `helpers/model_factories.py`: Factories for creating test model instances
- `test_auth.py`: Tests for the authentication module
- `test_account.py`: Tests for account management functionality
- `test_order_creation.py`: Tests for creating various order types
- `test_order_instructions.py`: Tests for all supported order instructions
- `test_order_management.py`: Tests for order management operations
- `test_paper_trading.py`: Tests for paper trading functionality
- `test_portfolio.py`: Tests for portfolio management
- `test_quotes.py`: Tests for market data and quotes

## Running Tests

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Run the entire test suite:
```bash
pytest
```

3. Run tests with coverage:
```bash
pytest --cov=schwab
```

4. Generate HTML coverage report:
```bash
pytest --cov=schwab --cov-report=html
```

5. Run a specific test file:
```bash
pytest test_order_creation.py
```

6. Run a specific test:
```bash
pytest test_order_creation.py::TestOrderCreation::test_create_market_order
```

## Adding Tests

When adding new features to the library, be sure to add corresponding tests. Follow these guidelines:

1. Use the existing test structure and patterns
2. Use model factories from `helpers/model_factories.py` to create test instances
3. Import models directly from generated packages (`schwab.models.generated.trading_models`, etc.)
4. Mock external dependencies
5. Test both success and failure cases
6. Test edge cases where applicable
7. Aim for high test coverage (90%+)

## Mocking Strategy

The tests use pytest fixtures to mock the API client and its dependencies. The `mock_client` fixture in `conftest.py` provides a pre-configured client with:

- Mocked authentication
- Mocked session and requests
- Mocked API responses

This approach allows testing the library's functionality without making actual API calls.