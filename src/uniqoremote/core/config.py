from __future__ import annotations

import tomllib
import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class IdentityConfig:
    device_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    device_name: str = "UniqoRemote Client"


@dataclass
class NetworkConfig:
    bind_port: int = 21116
    rendezvous_server: str = ""


@dataclass
class DisplayConfig:
    default_width: int = 1920
    default_height: int = 1080
    max_fps: int = 30


@dataclass
class AIConfig:
    enabled: bool = False
    model: str = "deepseek-chat"
    api_key: str = ""


@dataclass
class Config:
    identity: IdentityConfig = field(default_factory=IdentityConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    ai: AIConfig = field(default_factory=AIConfig)


def load_config(path: Path) -> Config:
    config = Config()
    if not path.exists():
        return config

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    if "identity" in raw:
        id_raw = raw["identity"]
        if "device_id" in id_raw:
            config.identity.device_id = id_raw["device_id"]
        if "device_name" in id_raw:
            config.identity.device_name = id_raw["device_name"]

    if "network" in raw:
        net_raw = raw["network"]
        if "bind_port" in net_raw:
            config.network.bind_port = net_raw["bind_port"]
        if "rendezvous_server" in net_raw:
            config.network.rendezvous_server = net_raw["rendezvous_server"]

    if "display" in raw:
        disp_raw = raw["display"]
        if "default_width" in disp_raw:
            config.display.default_width = disp_raw["default_width"]
        if "default_height" in disp_raw:
            config.display.default_height = disp_raw["default_height"]
        if "max_fps" in disp_raw:
            config.display.max_fps = disp_raw["max_fps"]

    if "ai" in raw:
        ai_raw = raw["ai"]
        if "enabled" in ai_raw:
            config.ai.enabled = ai_raw["enabled"]
        if "model" in ai_raw:
            config.ai.model = ai_raw["model"]
        if "api_key" in ai_raw:
            config.ai.api_key = ai_raw["api_key"]

    return config
