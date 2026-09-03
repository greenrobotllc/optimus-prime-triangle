"""Shared pytest fixtures."""
from __future__ import annotations

import random

import numpy as np
import pytest


@pytest.fixture(scope="session")
def small_primes() -> list[int]:
    """Primes below 200 (sieve, independent of the code under test)."""
    limit = 200
    flags = bytearray([1]) * (limit + 1)
    flags[0] = flags[1] = 0
    for i in range(2, int(limit ** 0.5) + 1):
        if flags[i]:
            flags[i * i :: i] = bytearray(len(flags[i * i :: i]))
    return [i for i in range(limit + 1) if flags[i]]


@pytest.fixture(autouse=True)
def _seed_everything() -> None:
    random.seed(20)
    np.random.seed(20)
