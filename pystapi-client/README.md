# pystapi-client

PySTAPI Client is a Python library for interacting with [STAPI](https://github.com/stapi-spec/stapi-spec) endpoints. Below is a overview of the supported endpoints and examples.

## Installation

Install from PyPi.
The dependencies for **pystapi-client** are the Python [httpx](https://www.python-httpx.org/) and [dateutil](https://dateutil.readthedocs.io) libraries.

```shell
python -m pip install pystapi-client
```

## Currently Supported Endpoints

These endpoints are fully implemented and available in the current version of PySTAPI Client.

| Category | Endpoint | Description |
|----------|----------|-------------|
| Root | `/` | Root endpoint (for links and conformance) |
| Root | `/conformance` | Conformance information |
| Products | `/products` | List all products |
| Products | `/products/{product_id}` | Get specific product |
| Orders | `/orders` | List all orders |
| Orders | `/orders/{order_id}` | Get specific order |

## Usage Example

The `pystapi_client.Client` class is the main interface for working with services that conform to the STAPI API spec.

Pre-request: The app should be accessible at `http://localhost:8000`.

```python
from pystapi_client import Client

# Initialize client
client = Client.open("https://api.example.com/stapi")

# List all products
products = list(client.get_products())

# Get specific product
product = client.get_product(product_id="test-spotlight")

# List all Opportunities for a Product
opportunities = client.get_product_opportunities(product_id="test-spotlight")

# List orders
orders = client.get_orders()

# Get specific order
order = client.get_order(order_id="test-order")
```
