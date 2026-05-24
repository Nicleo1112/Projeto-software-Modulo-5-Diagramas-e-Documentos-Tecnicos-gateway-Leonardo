from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


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
        "token": token,
    }


def exigir_token_bearer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization nao informado. Use Authorization: Bearer TOKEN.",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Formato do token invalido. Use "Authorization: Bearer TOKEN".',
        )

    token = credentials.credentials.strip()
    return validar_token_jwt(token)
