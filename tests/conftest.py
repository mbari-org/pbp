import pathlib
from typing import Mapping

import numpy as np
import pytest

GOLDEN_DIR = pathlib.Path(__file__).parent / "golden"


def pytest_addoption(parser):
    parser.addoption(
        "--golden-update",
        action="store_true",
        default=False,
        help="(Re)generate the numeric golden files under tests/golden/",
    )


class Golden:
    """
    Compares numeric arrays against golden `.npz` files under `tests/golden/`.

    Use `pytest --golden-update` (or `just golden-update`) to (re)generate them.
    """

    def __init__(self, update: bool):
        self.update = update

    def check(
        self,
        name: str,
        arrays: Mapping[str, np.ndarray],
        rtol: float,
        atol: float = 0.0,
    ) -> None:
        path = GOLDEN_DIR / f"{name}.npz"
        actual = {k: np.asarray(v) for k, v in arrays.items()}

        if self.update:
            GOLDEN_DIR.mkdir(exist_ok=True)
            np.savez_compressed(path, **actual)
            return

        assert path.exists(), f"Missing {path}; run `pytest --golden-update` first."

        with np.load(path) as expected:
            assert sorted(expected.files) == sorted(actual.keys())
            for k, a in actual.items():
                e = expected[k]
                assert a.shape == e.shape, f"{name}/{k}: shape {a.shape} != {e.shape}"
                assert a.dtype == e.dtype, f"{name}/{k}: dtype {a.dtype} != {e.dtype}"
                np.testing.assert_allclose(
                    a, e, rtol=rtol, atol=atol, equal_nan=True, err_msg=f"{name}/{k}"
                )


@pytest.fixture
def golden(request) -> Golden:
    return Golden(request.config.getoption("--golden-update"))
