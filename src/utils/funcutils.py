import functools

def try_x_times(x, fn):
    @functools.wraps(fn)
    def new_fn(*args, **kwargs):
        for i in range(x):
            try:
                return fn(*args, **kwargs)
            except:
                pass
        raise Exception
    return new_fn


def f(x):
    return x*x

if __name__ == "__main__":
    try_x_times(3, f)(2)    

