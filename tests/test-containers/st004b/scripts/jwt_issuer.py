#!/usr/bin/env python3
# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Serve a local JWKS and deterministic JWT variants for ST-004B."""

# Token-case constants intentionally mirror the verifier's external contract.
# pylint: disable=duplicate-code

from __future__ import annotations

import argparse
import json
import logging
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8090
RSA_KEY_SIZE_BITS = 2048
RSA_PUBLIC_EXPONENT = 65537
TOKEN_LIFETIME_SECONDS = 300
EXPIRED_TOKEN_AGE_SECONDS = 120
ISSUER = "http://jwt-issuer:8090"
WRONG_ISSUER = "http://wrong-issuer:8090"
AUDIENCE = "st004b-audience"
WRONG_AUDIENCE = "st004b-wrong-audience"
KEY_ID = "st004b-key"
SUBJECT = "st004b-verifier"
JWT_ALGORITHM = "RS256"
JWT_ALGORITHM_NONE = "none"
UTF_8_ENCODING = "utf-8"

HEALTH_PATH = "/health"
JWKS_PATH = "/.well-known/jwks.json"
MINT_PATH = "/mint"

CASE_QUERY_KEY = "case"
CASE_VALID = "valid"
CASE_EXPIRED = "expired"
CASE_WRONG_ISSUER = "wrong-issuer"
CASE_WRONG_AUDIENCE = "wrong-audience"
CASE_UNSIGNED = "unsigned"
SUPPORTED_CASES = {
    CASE_VALID,
    CASE_EXPIRED,
    CASE_WRONG_ISSUER,
    CASE_WRONG_AUDIENCE,
    CASE_UNSIGNED,
}

HEADER_CONTENT_LENGTH = "Content-Length"
HEADER_CONTENT_TYPE = "Content-Type"
MEDIA_TYPE_JSON = "application/json"

KEY_ALGORITHM = "alg"
KEY_AUDIENCE = "aud"
KEY_EXPIRATION = "exp"
KEY_ISSUED_AT = "iat"
KEY_ISSUER = "iss"
KEY_KEY_ID = "kid"
KEY_KEYS = "keys"
KEY_NOT_BEFORE = "nbf"
KEY_SUBJECT = "sub"
KEY_TOKEN = "token"
KEY_USE = "use"
KEY_ERROR = "error"
KEY_STATUS = "status"

PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=RSA_PUBLIC_EXPONENT,
    key_size=RSA_KEY_SIZE_BITS,
)
PUBLIC_JWK = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(PRIVATE_KEY.public_key()))
PUBLIC_JWK[KEY_KEY_ID] = KEY_ID
PUBLIC_JWK[KEY_USE] = "sig"
PUBLIC_JWK[KEY_ALGORITHM] = JWT_ALGORITHM


def _claims(token_case: str) -> dict[str, object]:
    """Build signed-token claims for one requested negative or valid case.

    Args:
        token_case: Named token variant requested through the mint endpoint.

    Returns:
        Claims with isolated issuer, audience, or expiry changes for the case.
    """
    current_time = int(time.time())
    issued_at = current_time
    expiration = current_time + TOKEN_LIFETIME_SECONDS
    issuer = ISSUER
    audience = AUDIENCE
    if token_case == CASE_EXPIRED:
        issued_at = current_time - (EXPIRED_TOKEN_AGE_SECONDS * 2)
        expiration = current_time - EXPIRED_TOKEN_AGE_SECONDS
    elif token_case == CASE_WRONG_ISSUER:
        issuer = WRONG_ISSUER
    elif token_case == CASE_WRONG_AUDIENCE:
        audience = WRONG_AUDIENCE
    return {
        KEY_ISSUER: issuer,
        KEY_AUDIENCE: audience,
        KEY_SUBJECT: SUBJECT,
        KEY_ISSUED_AT: issued_at,
        KEY_NOT_BEFORE: issued_at,
        KEY_EXPIRATION: expiration,
    }


def _mint_token(token_case: str) -> str:
    """Encode one token variant using the local test issuer key.

    Args:
        token_case: Supported token variant name.

    Returns:
        Encoded JWT for provider authentication checks.
    """
    claims = _claims(token_case)
    headers = {KEY_KEY_ID: KEY_ID}
    if token_case == CASE_UNSIGNED:
        return jwt.encode(
            claims,
            key="",
            algorithm=JWT_ALGORITHM_NONE,
            headers=headers,
        )
    return jwt.encode(
        claims,
        key=PRIVATE_KEY,
        algorithm=JWT_ALGORITHM,
        headers=headers,
    )


class JwtIssuerHandler(BaseHTTPRequestHandler):
    """Serve health, JWKS, and token-minting responses for the test issuer."""

    def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        """Write one JSON response with deterministic headers.

        Args:
            status: HTTP status returned to the caller.
            payload: JSON object serialized into the response body.
        """
        body = json.dumps(payload, sort_keys=True).encode(UTF_8_ENCODING)
        self.send_response(status)
        self.send_header(HEADER_CONTENT_TYPE, MEDIA_TYPE_JSON)
        self.send_header(HEADER_CONTENT_LENGTH, str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # pylint: disable=invalid-name
        """Handle health, JWKS, and token-minting GET requests."""
        parsed_url = urlsplit(self.path)
        if parsed_url.path == HEALTH_PATH:
            self._send_json(HTTPStatus.OK, {KEY_STATUS: "ready"})
            return
        if parsed_url.path == JWKS_PATH:
            self._send_json(HTTPStatus.OK, {KEY_KEYS: [PUBLIC_JWK]})
            return
        if parsed_url.path == MINT_PATH:
            query = parse_qs(parsed_url.query)
            token_case = str((query.get(CASE_QUERY_KEY) or [CASE_VALID])[0])
            if token_case not in SUPPORTED_CASES:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {KEY_ERROR: f"unsupported token case: {token_case}"},
                )
                return
            self._send_json(HTTPStatus.OK, {KEY_TOKEN: _mint_token(token_case)})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {KEY_ERROR: "not found"})

    # BaseHTTPRequestHandler defines a variadic callback whose parameter names
    # are implementation details; this override preserves that public shape.
    # pylint: disable-next=arguments-differ
    def log_message(self, message_format: str, *arguments: object) -> None:
        """Route HTTP server access messages through structured debug logging.

        Args:
            message_format: BaseHTTPRequestHandler interpolation template.
            arguments: Values inserted into the access-log template.
        """
        logging.getLogger(__name__).debug(message_format, *arguments)


def main() -> None:
    """Parse listener options and serve the local issuer until terminated."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    server = ThreadingHTTPServer((arguments.host, arguments.port), JwtIssuerHandler)
    logging.getLogger(__name__).debug(
        "starting ST-004B issuer host=%s port=%s",
        arguments.host,
        arguments.port,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
