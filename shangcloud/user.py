from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client

from .models import UserBasicInfo


class User(ABC):
    @abstractmethod
    def init_user(self, access_token: str, refresh_token: str, token_type: str,
                  expires_in: int, client: Client) -> None:
        pass

    @abstractmethod
    def save(self) -> None:
        pass

    @abstractmethod
    def is_expired(self) -> bool:
        pass

    @abstractmethod
    def get_basic_info(self) -> UserBasicInfo:
        pass


class UserInstance(User):
    def __init__(self) -> None:
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._token_type: str = ""
        self.expires_in: int = 0
        self.expiry_time: datetime = datetime.now()
        self._client: Client | None = None

    def init_user(self, access_token: str, refresh_token: str, token_type: str,
                  expires_in: int, client: Client) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_type = token_type
        self.expires_in = expires_in
        self._client = client
        self.expiry_time = datetime.now() + timedelta(seconds=expires_in)
        self.save()

    def save(self) -> None:
        pass

    def is_expired(self) -> bool:
        return datetime.now() + timedelta(seconds=60) > self.expiry_time

    def get_basic_info(self) -> UserBasicInfo:
        return self._client._get_user_basic_info(self._access_token, self._token_type)
