# pystapi

**pystapi** is the Python [monorepo](https://en.wikipedia.org/wiki/Monorepo) for the Satellite Tasking API (STAPI) specification.
It contains three Python packages:

- [stapi-pydantic](./stapi-pydantic.md): [Pydantic](https://docs.pydantic.dev) models that define the data structures in the STAPI specification
- [stapi-fastapi](./stapi-fastapi.md): [FastAPI](https://fastapi.tiangolo.com/) routes and functions for building a STAPI server
- [pystapi-client](./pystapi-client.md): a Python package and command-line interface (CLI) for interacting with a STAPI server
