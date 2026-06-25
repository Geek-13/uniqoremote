from __future__ import annotations

import pytest


@pytest.fixture
def key_pair():
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

    private = X25519PrivateKey.generate()
    return private, private.public_key()
