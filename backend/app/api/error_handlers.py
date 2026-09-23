from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.exceptions import InvalidSearchParamsError


async def invalid_search_params_handler(
    request: Request, exc: InvalidSearchParamsError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": exc.message, "field": exc.field},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(InvalidSearchParamsError, invalid_search_params_handler)
