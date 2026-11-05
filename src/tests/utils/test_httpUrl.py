import pytest
from pydantic import BaseModel, ValidationError

from src.app.utils.httpUrl import HttpUrl


class UrlModel(BaseModel):
    url: HttpUrl


def test_http_url_accepts_valid_url_without_trailing_slash():
    model = UrlModel(url="https://facebook.com/john")
    assert model.url == "https://facebook.com/john"


def test_http_url_rejects_host_without_tld():
    with pytest.raises(ValidationError):
        UrlModel(url="https://localhost/path")


def test_http_url_rejects_invalid_scheme():
    with pytest.raises(ValidationError):
        UrlModel(url="not-a-url")


def test_optional_http_url_allows_none():
    class OptionalUrlModel(BaseModel):
        url: HttpUrl | None = None

    model = OptionalUrlModel(url=None)
    assert model.url is None
