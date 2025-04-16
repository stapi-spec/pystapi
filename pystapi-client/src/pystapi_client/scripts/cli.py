import itertools
import json

import click

from pystapi_client.client import Client
from pystapi_client.exceptions import APIError

CONTEXT_SETTINGS = dict(default_map={"cli": {"url": "http://localhost:8000"}})


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--url", type=str, required=True, help="Base URL for STAPI server")
@click.pass_context
def cli(ctx: click.Context, url: str) -> None:
    """Command line interface for STAPI client.  Group ensures client is created."""

    client = Client.open(url)
    ctx.obj = {"client": client}


@click.command()
@click.pass_context
@click.option("--max-items", "max_items", type=click.IntRange(min=1), help="Max number of products to display")
@click.option("--limit", type=click.IntRange(min=1), help="Limit number of products to request")
def products(ctx: click.Context, limit: int | None, max_items: int | None) -> None:
    """List products."""

    client: Client = ctx.obj["client"]

    products_iter = client.get_products(limit=limit)

    if max_items:
        products_iter = itertools.islice(products_iter, max_items)

    products_list = list(products_iter)
    if len(products_list) == 0:
        click.echo("No products found.")
        return

    # Serialize the products list into JSON format and output it
    click.echo(json.dumps([p.model_dump(mode="json") for p in products_list]))


@click.command()
@click.pass_context
@click.option("--id", type=str, required=True, help="Product ID to retrieve")
def product(ctx: click.Context, id: str) -> None:
    """Get product by ID."""

    client: Client = ctx.obj["client"]

    product = client.get_product(product_id=id)
    if not product:
        click.echo(f"Product {id} not found.", err=True)
        return

    click.echo(product.model_dump_json())


@click.command()
@click.pass_context
@click.option("--max-items", "max_items", type=click.IntRange(min=1), help="Max number of products to display")
@click.option("--limit", type=click.IntRange(min=1), help="Limit number of products to request")
def orders(ctx: click.Context, max_items: int | None, limit: int | None) -> None:
    """List orders."""

    client: Client = ctx.obj["client"]

    orders_iter = client.get_orders(limit=limit)

    if max_items:
        orders_iter = itertools.islice(orders_iter, max_items)

    orders_list = list(orders_iter)
    if len(orders_list) == 0:
        click.echo("No orders found.", err=True)
        return

    # Serialize the orders list into JSON format and output it
    click.echo(json.dumps([o.model_dump(mode="json") for o in orders_list]))


@click.command()
@click.pass_context
@click.option("--id", type=str, required=True, help="Order ID to retrieve")
def order(ctx: click.Context, id: str) -> None:
    """Get order by ID."""

    client: Client = ctx.obj["client"]

    try:
        order = client.get_order(order_id=id)
        click.echo(order.model_dump_json())
    except APIError as e:
        if e.status_code == 404:
            click.echo(f"Order {id} not found.", err=True)
        else:
            raise e


@click.command()
@click.pass_context
@click.option("--product-id", "product_id", type=str, required=True, help="Product ID for opportunities")
@click.option("--max-items", "max_items", type=click.IntRange(min=1), help="Max number of opportunities to display")
@click.option("--limit", type=click.IntRange(min=1), default=10, help="Max number of opportunities to display")
def opportunities(ctx: click.Context, product_id: str, limit: int, max_items: None) -> None:
    """List opportunities for a product."""

    client: Client = ctx.obj["client"]

    date_range = ("2025-01-03T15:18:11Z", "2025-04-03T15:18:11Z")
    geometry = {"type": "Point", "coordinates": [-122.4194, 37.7749]}

    opportunities_iter = client.get_product_opportunities(
        product_id=product_id, geometry=geometry, date_range=date_range, limit=limit
    )

    if max_items:
        opportunities_iter = itertools.islice(opportunities_iter, max_items)

    opportunities_list = list(opportunities_iter)
    if len(opportunities_list) == 0:
        click.echo("No opportunities found.", err=True)
        return

    click.echo(json.dumps([o.model_dump(mode="json") for o in opportunities_list]))


cli.add_command(products)
cli.add_command(product)
cli.add_command(opportunities)
cli.add_command(orders)
cli.add_command(order)

if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {e=}", err=True)
        raise e
