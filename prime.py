import random
import _thread
import os.path
import time

PRIME_LEN = 2048
DEFAULT_SAFE_2048 = 42996084587308853659973814684939889019765628197874605226030264746629091236330599666549875318212612031829511024440396464342648691577991833890563140387102818493525508471270342361352936629776054362738421828170255955761393123098102521470143629284337488254705041089874927401756138096186464198682293497409454662570337393410558180415100006913617169493379962859674636074408998785963274426613400362115957142286298014404337771779324960432946340624884089537068596532972151293551270481551099886836859728504702291073167904801075628639610812850401097540434467292419182764310323486917373365274421751734483875743936086632531541480503
STORE_TIME_MIN = 3600 * 24 * 30  # 30 days
FILE_NAME = 'actualPrime'
TIME_FILE_NAME = 'time'


def rabin_miller(n):
    s = n - 1
    t = 0
    while s & 1 == 0:
        s = s // 2
        t += 1
    k = 0
    while k < 128:
        a = random.randrange(2, n - 1)
        v = pow(a, s, n)
        if v != 1:
            i = 0
            while v != (n - 1):
                if i == t - 1:
                    return False
                else:
                    i = i + 1
                    v = (v ** 2) % n
        k += 2
    return True


def is_prime(n):
    low_primes = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97,
                  101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197,
                  199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313,
                  317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439,
                  443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571,
                  577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691,
                  701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829,
                  839, 853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967, 971, 977,
                  983, 991, 997]
    if n >= 3:
        if n & 1 != 0:
            for p in low_primes:
                if n == p:
                    return True
                if n % p == 0:
                    return False
            return rabin_miller(n)
    return False


def generate_large_prime(k):
    n = random.randint(2 ** (k - 2), 2 ** (k - 1)) + 2 ** k
    n += (5 - n % 6)
    assert (n % 6 == 5)

    while True:
        if is_prime(n):
            return n
        n += 6


def generate_safe_prime(k):
    res = 6
    t = time.time()
    print("generating", k, "bits")
    while not is_prime(res):
        q = generate_large_prime(k - 1)
        res = 2 * q + 1
    for i in range(10):
        assert (is_prime(res))
    print("generated", res)
    print("took:", time.time() - t, "sec")
    return res


def generate_and_write():
    safe_prime = generate_safe_prime(PRIME_LEN)
    with open(FILE_NAME, 'w+') as f:
        f.write(str(safe_prime))


def generate_async():
    if need_to_refresh():
        _thread.start_new_thread(generate_and_write, ())


def get_actual():
    prime = DEFAULT_SAFE_2048
    if not os.path.isfile(FILE_NAME):
        return prime
    with open(FILE_NAME, 'r') as f:
        try:
            prime_from_file = int(f.read())
            if len(bin(prime_from_file)[2:]) >= PRIME_LEN:
                prime = prime_from_file
        except Exception:
            pass
    return prime


def save_time():
    t = str(int(time.time()))
    with open(TIME_FILE_NAME, 'w+') as f:
        f.write(t)


def get_time():
    if not os.path.isfile(TIME_FILE_NAME):
        return 0
    try:
        with open(TIME_FILE_NAME, 'r') as f:
            return int(f.read())
    except Exception:
        pass


def need_to_refresh():
    return time.time() - get_time() > STORE_TIME_MIN
