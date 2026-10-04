"""Primitive string operations for the synthetic DSL."""

from __future__ import annotations

from typing import Callable, Dict, List


def reverse(s: str) -> str:
    return s[::-1]


def rotate_left(s: str, n: int = 1) -> str:
    if not s:
        return s
    n = n % len(s)
    return s[n:] + s[:n]


def rotate_right(s: str, n: int = 1) -> str:
    if not s:
        return s
    n = n % len(s)
    return s[-n:] + s[:-n]


def select_odd(s: str) -> str:
    return s[1::2]


def select_even(s: str) -> str:
    return s[0::2]


def duplicate(s: str) -> str:
    return s + s


def truncate(s: str, n: int = 3) -> str:
    return s[:n]


def swap_halves(s: str) -> str:
    mid = len(s) // 2
    return s[mid:] + s[:mid]


def concat_transformed(s: str, op1: Callable[[str], str], op2: Callable[[str], str]) -> str:
    return op1(s) + op2(s)


PRIMITIVES: Dict[str, Callable[..., str]] = {
    "reverse": reverse,
    "rotate_left": lambda s: rotate_left(s, 1),
    "rotate_right": lambda s: rotate_right(s, 1),
    "select_odd": select_odd,
    "select_even": select_even,
    "duplicate": duplicate,
    "truncate": truncate,
    "swap_halves": swap_halves,
}

PRIMITIVE_NAMES = list(PRIMITIVES.keys())
