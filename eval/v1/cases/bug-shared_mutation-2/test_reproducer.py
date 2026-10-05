from app import solve

def test_reproducer():
    items = [21, 20]
    assert solve(items) == [20, 21]
    assert items == [21, 20]
