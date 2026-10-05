from app import solve

def test_reproducer():
    state = {'count': 11}
    assert solve(state) == 12
    assert state['count'] == 12
