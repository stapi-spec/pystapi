import warnings
from collections.abc import Iterator
from contextlib import contextmanager


class PystapiClientWarning(UserWarning):
    """Base warning class"""

    ...


class NoConformsTo(PystapiClientWarning):
    """Inform user when client does not have "conformsTo" set"""

    def __str__(self) -> str:
        return "Server does not advertise any conformance classes."


class DoesNotConformTo(PystapiClientWarning):
    """Inform user when client does not conform to extension"""

    def __str__(self) -> str:
        return "Server does not conform to {}".format(", ".join(self.args))


class MissingLink(PystapiClientWarning):
    """Inform user when link is not found"""

    def __str__(self) -> str:
        return "No link with rel='{}' could be found on this {}.".format(*self.args)


class FallbackToPystapi(PystapiClientWarning):
    """Inform user when falling back to Pystapi implementation"""

    def __str__(self) -> str:
        return "Falling back to Pystapi. This might be slow."


@contextmanager
def strict() -> Iterator[None]:
    """Context manager for raising all Pystapi-client warnings as errors

    For more fine-grained control or to filter warnings in the whole
    python session, use the :py:mod:`warnings` module directly.

    Examples:

    >>> from pystapi_client import Client
    >>> from pystapi_client.warnings import strict
    >>> with strict():
    ...     Client.open("https://perfect-api.test")

    For finer-grained control:

    >>> import warnings
    >>> from pystapi_client import Client
    >>> from pystapi_client.warnings import MissingLink
    >>> warnings.filterwarnings("error", category=FallbackToPystapi)
    >>> Client.open("https://imperfect-api.test")
    """

    warnings.filterwarnings("error", category=PystapiClientWarning)
    try:
        yield
    finally:
        warnings.filterwarnings("default", category=PystapiClientWarning)


@contextmanager
def ignore() -> Iterator[None]:
    """Context manager for ignoring all pystapi-client warnings

    For more fine-grained control or to set filter warnings in the whole
    python session, use the ``warnings`` module directly.

    Examples:

    >>> from pystapi_client import Client
    >>> from pystapi_client.warnings import ignore
    >>> with ignore():
    ...     Client.open("https://perfect-api.test")

    For finer-grained control:

    >>> import warnings
    >>> from pystapi_client import Client
    >>> from pystapi_client.warnings import MissingLink
    >>> warnings.filterwarnings("ignore", category=MissingLink)
    >>> Client.open("https://imperfect-api.test")
    """
    warnings.filterwarnings("ignore", category=PystapiClientWarning)
    try:
        yield
    finally:
        warnings.filterwarnings("default", category=PystapiClientWarning)
