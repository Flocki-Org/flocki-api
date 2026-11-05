from datetime import UTC, datetime, timedelta

import jwt
import pytest

from src.app.config import settings
from src.app.users.services.TokenUtil import TokenUtil, ALGORITHM


def test_generate_token_contains_subject_and_expiry():
    token_util = TokenUtil()
    token = token_util.generate_token({"sub": "user@example.com"})

    decoded = jwt.decode(token, settings.flocki_secret_key, algorithms=[ALGORITHM])
    assert decoded["sub"] == "user@example.com"
    assert "exp" in decoded


def test_decode_token_round_trips_payload():
    token_util = TokenUtil()
    token = token_util.generate_token({"sub": "admin@flocki.org", "role": "admin"})

    decoded = token_util.decode_token(token)

    assert decoded["sub"] == "admin@flocki.org"
    assert decoded["role"] == "admin"


def test_decode_token_rejects_tampered_token():
    token_util = TokenUtil()
    token = token_util.generate_token({"sub": "user@example.com"})
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")

    with pytest.raises(jwt.InvalidTokenError):
        token_util.decode_token(tampered)


def test_generate_token_uses_configured_expiry():
    token_util = TokenUtil()
    before = datetime.now(UTC)
    token = token_util.generate_token({"sub": "user@example.com"})
    after = datetime.now(UTC)

    decoded = jwt.decode(token, settings.flocki_secret_key, algorithms=[ALGORITHM])
    exp = datetime.fromtimestamp(decoded["exp"], tz=UTC)

    # JWT exp is second-precision, so allow a one-second window around the configured TTL.
    min_exp = before + timedelta(minutes=settings.flocki_token_expiry_minutes) - timedelta(seconds=1)
    max_exp = after + timedelta(minutes=settings.flocki_token_expiry_minutes) + timedelta(seconds=1)
    assert min_exp <= exp <= max_exp
