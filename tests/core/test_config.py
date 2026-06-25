from __future__ import annotations

import tempfile
from pathlib import Path

from uniqoremote.core.config import Config, load_config

DEFAULT_TOML = b"""
[identity]
device_id = "test-device-001"
device_name = "Test PC"

[network]
bind_port = 21116
rendezvous_server = "rdp.example.com"

[display]
default_width = 1920
default_height = 1080
max_fps = 30

[ai]
enabled = true
model = "deepseek-chat"
"""


class TestConfig:
    def test_loads_valid_config(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(DEFAULT_TOML)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.identity.device_id == "test-device-001"
            assert config.identity.device_name == "Test PC"
            assert config.network.bind_port == 21116
            assert config.network.rendezvous_server == "rdp.example.com"
            assert config.display.default_width == 1920
            assert config.display.default_height == 1080
            assert config.display.max_fps == 30
            assert config.ai.enabled is True
            assert config.ai.model == "deepseek-chat"
        finally:
            config_path.unlink()

    def test_default_config_has_sensible_values(self) -> None:
        config = Config()
        assert config.identity.device_id != ""
        assert config.network.bind_port == 21116
        assert config.display.max_fps == 30
        assert config.ai.enabled is False

    def test_loads_partial_config_with_defaults(self) -> None:
        partial = b'[identity]\ndevice_id = "partial-device"\n'
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(partial)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.identity.device_id == "partial-device"
            assert config.network.bind_port == 21116
        finally:
            config_path.unlink()


def test_persist_device_id(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg1 = load_config(cfg_path)
    assert cfg1.identity.device_id != ""
    dev_id = cfg1.identity.device_id

    cfg2 = load_config(cfg_path)
    assert cfg2.identity.device_id == dev_id
