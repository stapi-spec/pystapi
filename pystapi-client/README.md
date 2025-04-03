# pystapi-client

PySTAPI Client is a Python library for interacting with [STAPI](https://github.com/stapi-spec/stapi-spec) endpoints. Below is a overview of the supported endpoints and examples.

## Installation

Install from PyPi.
The dependencies for **pystapi-client** are the Python [httpx](https://www.python-httpx.org/) and [dateutil](https://dateutil.readthedocs.io) libraries.

```shell
python -m pip install pystapi-client
```

## Currently Supported Endpoints

STAPI endpoints are available in PySTAPI Client.

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
