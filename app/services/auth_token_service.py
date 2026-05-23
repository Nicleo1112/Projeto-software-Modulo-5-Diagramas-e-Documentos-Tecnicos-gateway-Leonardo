from fastapi import Header, HTTPException, status


def validar_token_jwt(token: str) -> dict:
    # Preparado para a validacao real com o Modulo 1.
    # Por enquanto, o Gateway apenas exige um token Bearer nao vazio.
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao vazio.",
        )

    return {
        "valido": True,
        "modo": "validacao_jwt_pendente",
    }


def exigir_token_bearer(authorization: str | None = Header(default=None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization nao informado. Use Authorization: Bearer TOKEN.",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Formato do token invalido. Use "Authorization: Bearer TOKEN".',
        )

    token = authorization.replace("Bearer ", "", 1).strip()
    return validar_token_jwt(token)
