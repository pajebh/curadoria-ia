from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError


BASE_URI = "https://curadoria.app/errors"


def problem(
    status: int,
    title: str,
    detail: str = "",
    instance: str = "",
    extra: dict | None = None,
) -> dict:
    body: dict = {
        "type": f"{BASE_URI}/{title.lower().replace(' ', '-')}",
        "title": title,
        "status": status,
    }
    if detail:
        body["detail"] = detail
    if instance:
        body["instance"] = instance
    if extra:
        body.update(extra)
    return body


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=problem(
            status=422,
            title="Dados inválidos",
            detail="A requisição contém campos inválidos.",
            instance=str(request.url.path),
            extra={"errors": exc.errors(include_url=False)},
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=problem(
            status=500,
            title="Erro interno",
            detail="Ocorreu um erro inesperado. Tente novamente em instantes.",
            instance=str(request.url.path),
        ),
    )
