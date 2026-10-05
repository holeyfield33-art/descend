from app import solve

def test_reproducer():
    assert solve('café'.encode('utf-8')) == 'café'
