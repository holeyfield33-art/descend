def solve(values):
    try:
        return values.read()
    finally:
        values.close()
