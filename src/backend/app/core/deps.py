from collections.abc import Callable, Iterator
from typing import Annotated, cast

from fastapi import Depends, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.container import Container
from app.core.errors import UnauthorizedError
from app.core.security import ApiClient, ApiClientKind, CurrentUser, UserRole, hash_api_key

bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


ContainerDep = Annotated[Container, Depends(get_container)]


def get_session(container: ContainerDep) -> Iterator[Session]:
    with container.session_factory.begin() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session, scope="function")]


def get_current_user(
    container: ContainerDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> CurrentUser:
    if credentials is None:
        raise UnauthorizedError()
    return container.tokens.decode(credentials.credentials)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[CurrentUser], CurrentUser]:
    def check_role(user: CurrentUserDep) -> CurrentUser:
        user.require(roles)
        return user

    return check_role


def require_api_client(kind: ApiClientKind) -> Callable[..., ApiClient]:
    def authenticate_client(
        container: ContainerDep,
        session: SessionDep,
        api_key: Annotated[str | None, Security(api_key_scheme)],
    ) -> ApiClient:
        if not api_key or container.api_clients is None:
            raise UnauthorizedError()
        client = container.api_clients(session).find_active(hash_api_key(api_key), kind)
        if client is None:
            raise UnauthorizedError()
        return client

    return authenticate_client
