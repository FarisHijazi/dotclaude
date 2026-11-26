import pytest

from fake_store import FakeStore
from window_counter import WindowCounter


def make():
    return WindowCounter(10, FakeStore())


def test_example_1():
    c = make()
    assert c.hit("a", 0.0) == 1
    assert c.hit("a", 5.0) == 2


def test_example_2():
    c = make()
    c.hit("a", 0.0)
    assert c.hit("a", 10.0) == 1


def test_example_5():
    with pytest.raises(ValueError):
        make().hit("", 1.0)
