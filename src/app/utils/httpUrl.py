from typing import Annotated, Any

from pydantic import BeforeValidator
from pydantic.v1 import BaseModel as _V1BaseModel
from pydantic.v1 import HttpUrl as _V1HttpUrl


class _HttpUrlCheck(_V1BaseModel):
    url: _V1HttpUrl


def _validate_http_url(value: Any) -> Any:
    # Pydantic v2 HttpUrl adds a trailing slash and allows hosts with no
    # top-level domain. The v1 type did neither, and it was a str.
    if value is None:
        return None
    return str(_HttpUrlCheck(url=value).url)


HttpUrl = Annotated[str, BeforeValidator(_validate_http_url)]
