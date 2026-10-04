"""DSL determinism and isolation."""

from __future__ import annotations

from descend.dsl import generate_dsl, make_splits, grade


def test_same_seed_same_dsl():
    a = generate_dsl(42)
    b = generate_dsl(42)
    assert [op.name for op in a.operators] == [op.name for op in b.operators]
    assert [op.primitive for op in a.operators] == [op.primitive for op in b.operators]


def test_different_seeds_different_ops():
    a = generate_dsl(1)
    b = generate_dsl(2)
    names_a = {op.name for op in a.operators}
    names_b = {op.name for op in b.operators}
    # Very likely different; if collision, at least primitives differ often
    assert names_a != names_b or [o.primitive for o in a.operators] != [o.primitive for o in b.operators]


def test_hidden_deeper_than_train():
    dsl = generate_dsl(99)
    train_depths = {t.depth for t in dsl.train_templates}
    hidden_depths = {t.depth for t in dsl.hidden_templates}
    assert max(train_depths) <= 2
    assert min(hidden_depths) >= 3


def test_splits_deterministic():
    dsl = generate_dsl(7)
    s1 = make_splits(dsl, split_seed=7)
    s2 = make_splits(dsl, split_seed=7)
    assert s1.train == s2.train
    assert s1.hidden == s2.hidden


def test_grading_deterministic():
    gold = [{"input": "abc", "output": "cba"}]
    pred = [{"input": "abc", "output": "cba"}]
    g1 = grade(pred, gold)
    g2 = grade(pred, gold)
    assert g1 == g2
    assert g1["accuracy"] == 1.0
