
def get_p(k, s):
    alpha = 11/9

    a = 0
    for i in range(k - 1):
        a += alpha**i

    b = 0
    for i in range(s - 1):
        b += alpha**i

    return a / b

if __name__ == "__main__":
    print(get_p(90, 100))



