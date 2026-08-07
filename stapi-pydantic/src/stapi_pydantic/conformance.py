from typing import Annotated

from pydantic import AliasChoices, BaseModel, Field

from .constants import STAPI_VERSION
from .shared import STAPI_RESPONSE_CONFIG

#: The URI of the STAPI core conformance class. Defined here rather than only in
#: ``stapi_fastapi.conformance`` so the models can use it as their ``conformsTo``
#: example without that example drifting from what a server advertises.
CORE_CONFORMANCE = f"https://stapi.example.com/v{STAPI_VERSION}/core"

#: An illustrative ``conformsTo`` value.
CONFORMS_TO_EXAMPLE = [CORE_CONFORMANCE]

#: The ``conformsTo`` field, declared once so its wire name cannot drift between
#: the models that publish it.
ConformsTo = Annotated[
    list[str],
    Field(
        validation_alias=AliasChoices("conformsTo", "conforms_to"),
        serialization_alias="conformsTo",
        examples=[CONFORMS_TO_EXAMPLE],
    ),
]


class Conformance(BaseModel):
    model_config = STAPI_RESPONSE_CONFIG

    conforms_to: ConformsTo = []
