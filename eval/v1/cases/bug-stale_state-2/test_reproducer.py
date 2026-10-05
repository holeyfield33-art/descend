from app import solve

def test_reproducer():
    state = {'count': 20}
    assert solve(state) == 21
    assert state['count'] == 21
