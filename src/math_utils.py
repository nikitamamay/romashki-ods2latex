import math

PRECISION_DIGIT_COUNT = 7


def do_floats_equal(a: float, b: float) -> bool:
    return abs(a - b) < 10 ** (-PRECISION_DIGIT_COUNT)


def round_N(x: float, n: int) -> float:
    return round(x * 10 ** n) / (10 ** n)


def round_tail(x: float) -> float:
    return round_N(x, PRECISION_DIGIT_COUNT)


def count_digits(x: float) -> int:
    return len(str(round_tail(x)).replace("-", "").replace(".", "").strip("0"))


def count_10(x: float) -> int:
    if (do_floats_equal(x, 0)):
        return 0
    return math.floor(math.log10(abs(x)))


def round_digits(x: float, digits_count: int) -> float:
    c10 = count_10(x)
    return round_tail(round_N(x, -c10 + digits_count - 1))



def round_N_str(x: float, n: int) -> str:
    less0 = "-" if x < 0 else ""
    x = round_N(abs(x), n)
    if do_floats_equal(x, 0):
        return "0"
    s = str(x) + "0" * 16
    dot_pos = s.find(".")
    if n <= 0:
        return less0 + s[:dot_pos]
    else:
        return less0 + s[:dot_pos + n + 1]


def round_digits_str(x: float, digits_count: int) -> str:
    c10 = count_10(x)
    return round_N_str(x, -c10 + digits_count - 1)




def integrate(a, b, n, f):
    l = (b - a) / n
    s = 0
    for i in range(n):
        s += f(a + l*i) * l
    return s


if __name__ == '__main__':
    x = -(math.pi + 450) / 10
    n = 6

    for n in range(8, -4, -1):
        # print(n, round_N_str(x, n))
        # print(n, round_N(x, n))
        print(n, round_digits_str(x, n))

