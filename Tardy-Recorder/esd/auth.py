import time
import logging
import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin
import requests
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)

@dataclass
class OAuthToken:
    access_token: str
    expires_at: float
    refresh_token: Optional[str] = None

    def is_expired(self) -> bool:
        # Refresh 30 seconds early
        return time.time() >= self.expires_at - 30

class AuthClient:
    def __init__(self, base_url: str, token_endpoint: str, scope: str):
        self.base_url = base_url.rstrip("/")
        self.token_endpoint = token_endpoint
        self.scope = scope
        self.client_id = os.getenv("ESD_CLIENT_ID")
        self.client_secret = os.getenv("ESD_CLIENT_SECRET")
        self.tenant = os.getenv("ESD_TENANT")

        if not self.client_id or not self.client_secret:
            raise RuntimeError("Missing ESD_CLIENT_ID/ESD_CLIENT_SECRET in environment")

        self._token: Optional[OAuthToken] = None

    def _token_url(self) -> str:
        return urljoin(self.base_url + "/", self.token_endpoint.lstrip("/"))

    def _request_token(self) -> OAuthToken:
        data = {
            "grant_type": "client_credentials",
            "scope": self.scope,
        }

        # Optional tenant hint
        if self.tenant:
            data["acr_values"] = f"tenant:{self.tenant}"

        logger.info("Requesting OAuth2 token")
        resp = requests.post(
            self._token_url(),
            data=data,
            auth=(self.client_id, self.client_secret),
            timeout=15
        )
        resp.raise_for_status()
        payload = resp.json()

        access_token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))
        refresh_token = payload.get("refresh_token")

        tok = OAuthToken(
            access_token=access_token,
            expires_at=time.time() + expires_in,
            refresh_token=refresh_token
        )

        logger.info("Obtained access token (expires in %s s)", expires_in)
        return tok

    def get_token(self) -> str:
        if self._token is None or self._token.is_expired():
            self._token = self._request_token()
        return self._token.access_token

    def auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.get_token()}"}
