from __future__ import annotations

import base64
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request

from .exceptions import AuthError, ShangCloudError, StateNotFoundError
from .models import UserBasicInfo
from .storage import RamKv, TempVarStorage
from .user import User, UserInstance


def _generate_random_string(length: int) -> str:
    return base64.b64encode(secrets.token_bytes(length)).decode()[:length]


class Client:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self._client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = "user:basic"
        self.base_url = "https://api.yearnstudio.cn"
        self.kv_storage: TempVarStorage = RamKv()

    @classmethod
    def init_client(cls, client_id: str, client_secret: str, redirect_uri: str) -> Client:
        return cls(client_id, client_secret, redirect_uri)

    def set_client_secret(self, client_secret: str) -> None:
        self._client_secret = client_secret

    def _generate_authorize_header(self) -> str:
        raw = f"{self.client_id}:{self._client_secret}"
        return base64.b64encode(raw.encode()).decode()

    def generate_oauth_url(self) -> str:
        state = _generate_random_string(10)
        self.kv_storage.set_temp_variable(state, "0")
        params = urllib.parse.urlencode({
            "response_type": "code",
            "state": state,
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
        })
        return f"{self.base_url}/oauth/authorize?{params}"

    def generate_user_instance(self, code: str, state: str) -> User:
        try:
            self.kv_storage.get_temp_variable(state)
        except KeyError:
            raise StateNotFoundError(f"State '{state}' not found or expired")
        self.kv_storage.delete_temp_variable(state)

        data = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/oauth/token",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {self._generate_authorize_header()}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                t_resp = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise AuthError(f"Auth failed with status: {e.code}") from e

        user = UserInstance()
        user.init_user(
            t_resp["access_token"],
            t_resp["refresh_token"],
            t_resp["token_type"],
            t_resp["expires_in"],
            self,
        )
        return user

    def _get_user_basic_info(self, access_token: str, token_type: str) -> UserBasicInfo:
        data = self._request("/api/user/info", {}, access_token, token_type)
        return UserBasicInfo(
            user_id=data["uid"],
            nickname=data["nickname"],
            mail=data["mail"],
            avatar=data["avatar"],
        )

    def _variable_action(self, action: str, key: str, value: str,
                         access_token: str, token_type: str) -> str:
        data = self._request(
            "/api/varibles",
            {"key": key, "action": action, "value": value},
            access_token,
            token_type,
        )
        if isinstance(data, dict) and data.get("error"):
            raise ShangCloudError(f"variable {action} failed: {data['error']}")
        if isinstance(data, dict):
            return data.get("value", "") or ""
        return ""

    def _request(self, path: str, body: dict, access_token: str, token_type: str) -> dict:
        json_body = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json_body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"{token_type} {access_token}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            raise ShangCloudError(
                f"Server returned error status: {e.code}, body: {body_text}"
            ) from e
