"""Reshapes FastAPI's default error envelopes into ../../CONTRACT.md's
{ "error": "<message>" } shape, so routers can just `raise HTTPException(...)`
and stay framework-idiomatic. Plays the same role `nest`'s
`ContractErrorFilter` does for NestJS's own default envelope.

FastAPI's own defaults don't match the contract: `HTTPException` renders as
`{ "detail": "<message>" }`, and a Pydantic validation failure renders as
`{ "detail": [ ...per-field errors... ] }` with a 422, not 400 — both
rewritten here.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def not_found(kind: str, id_: int) -> HTTPException:
    """Shorthand for the 404 case every router hits the same way."""
    return HTTPException(status_code=404, detail=f"{kind} {id_} not found.")


async def _handle_http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


async def _handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"] if part != "body")
    return JSONResponse(status_code=400, content={"error": f"{field}: {first['msg']}"})


def register_error_handlers(app: FastAPI) -> None:
    # Starlette's own stubs type a registered handler's second parameter as
    # the base `Exception`, not the specific subclass `add_exception_handler`
    # actually dispatches — a known stub imprecision (the runtime behavior
    # is correct: FastAPI only ever calls each handler with the exception
    # type it's registered for), hence the ignores rather than widening
    # these handlers' own signatures to `Exception` and losing the
    # attribute-level typing (`exc.status_code`, `exc.detail`) below.
    app.add_exception_handler(HTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
