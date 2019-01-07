import time


def timeFunction(func, *args, **kwargs):
    """Times one execution of function.

    Args:
        func (function): Function that takes no arguments.

    Returns:
        wrapper (function): Function that executes func and prints the time
                it took to finish running (in seconds).
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        results = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f'Elapsed time: {elapsed:.2f} seconds.')
        return results
    return wrapper
