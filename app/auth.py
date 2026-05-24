import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Mantem a API funcionando sem token em ambiente de desenvolvimento.
# Na Azure, use AUTH_REQUIRED=true quando o front ja estiver enviando token.
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"
bearer_scheme = HTTPBearer(auto_error=False)


def verificar_sessao_usuario(token: str) -> dict:
    if not JWT_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY nao configurada no servidor.",
        )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")
        email = payload.get("email")
        nome = payload.get("nome")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sem identificador de usuario.",
            )

        return {
            "valido": True,
            "user_id": user_id,
            "email": email,
            "nome": nome,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessao expirada. Faca login novamente.",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao invalido.",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if not AUTH_REQUIRED and not credentials:
        return {
            "valido": True,
            "user_id": "dev-user",
            "email": "dev@docula.local",
            "nome": "Usuario Desenvolvimento",
            "modo": "sem_autenticacao_obrigatoria",
        }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao nao informado.",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato do token invalido. Use Authorization: Bearer TOKEN.",
        )

    return verificar_sessao_usuario(credentials.credentials.strip())
