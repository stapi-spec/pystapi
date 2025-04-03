# pystapi-client

[![CI](https://github.com/stapi-spec/pystapi/actions/workflows/ci.yaml/badge.svg)](https://github.com/stapi-spec/pystapi/actions/workflows/ci.yaml)
<!--TODO: Add PyPI badge when package is released-->
<!-- [![PyPI version](https://badge.fury.io/py/pystapi-client.svg)](https://badge.fury.io/py/pystapi-client) -->
[![Documentation](https://stapi-spec.github.io/pystapi/stapi-client/)](https://stapi-spec.github.io/pystapi/stapi-client/)

A Python client for working with [STAPI](https://stapi-spec.github.io/pystapi/) APIs.

## Installation

Install from PyPi.
Other than [stapi-pydantic](https://stapi-spec.github.io/pystapi/stapi-pydantic/) itself, the only dependencies for **pystapi-client** are the Python [httpx](https://www.python-httpx.org/) and [python-dateutil](https://dateutil.readthedocs.io) libraries.

```shell
python -m pip install pystapi-client
```

## Development

See the instructions in the [pystapi monorepo](https://github.com/stapi-spec/pystapi?tab=readme-ov-file#development).

## Documentation

See the [documentation page](https://stapi-spec.github.io/pystapi/stapi-client/) for the latest docs.

## Usage Example

The `pystapi_client.Client` class is the main interface for working with services that conform to the STAPI API spec.

```python
from pystapi_client import Client

# Initialize client
client = Client.open("https://api.example.com/stapi")

# List all products
products = list(client.get_products())

# Get specific product
product = client.get_product("test-spotlight")

# List all Opportunities for a Product
opportunities = client.get_product_opportunities("test-spotlight")

# List orders
orders = client.get_orders()

# Get specific order
order = client.get_order("test-order")
```
