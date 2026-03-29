from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# для Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.AUTH_TOKEN_URL, auto_error=False)
