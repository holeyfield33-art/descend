from app import solve

def test_reproducer():
    items = [12, 11]
    assert solve(items) == [11, 12]
    assert items == [12, 11]
