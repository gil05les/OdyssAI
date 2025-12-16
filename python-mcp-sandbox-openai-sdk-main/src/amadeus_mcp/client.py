import os
from dataclasses import dataclass
from typing import Optional

from amadeus import Client, ResponseError


@dataclass
class AmadeusClientConfig:
    api_key: str
    api_secret: str
    hostname: str = "test"  # "test" or "production"
    ssl: bool = True
    log_level: str = "warn"

    @staticmethod
    def from_env() -> "AmadeusClientConfig":
        return AmadeusClientConfig(
            api_key=os.environ.get("AMADEUS_CLIENT_ID", ""),
            api_secret=os.environ.get("AMADEUS_CLIENT_SECRET", ""),
            hostname=os.environ.get("AMADEUS_HOSTNAME", "test"),
            ssl=os.environ.get("AMADEUS_SSL", "true").lower() == "true",
            log_level=os.environ.get("AMADEUS_LOG_LEVEL", "warn"),
        )


def build_amadeus(config: Optional[AmadeusClientConfig] = None) -> Client:
    cfg = config or AmadeusClientConfig.from_env()
    if not cfg.api_key or not cfg.api_secret:
        raise RuntimeError(
            "Missing Amadeus credentials. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET."
        )
    try:
        return Client(
            client_id=cfg.api_key,
            client_secret=cfg.api_secret,
            hostname=cfg.hostname,
            ssl=cfg.ssl,
            log_level=cfg.log_level,
        )
    except ResponseError as err:
        raise RuntimeError(f"Failed to create Amadeus client: {err}") from err








