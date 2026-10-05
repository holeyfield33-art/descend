from app import solve

def test_reproducer():
    from io import StringIO
    stream = StringIO('owned')
    assert solve(stream) == 'owned'
    assert stream.closed
