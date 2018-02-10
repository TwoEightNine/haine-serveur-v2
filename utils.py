import random
import string
import time
import hashlib
import json

MAX_USERS = 1000000000

ERROR_FORMAT = '{"error": %d, "message": "%s"}'
RESPONSE_FORMAT = '{"result": %s}'

RESPONSE_1 = RESPONSE_FORMAT % '1'
RESPONSE_EMPTY_LIST = RESPONSE_FORMAT % '[]'

ERROR_DICTIONARY = {
    1: "Missed parameter: %s",
    2: "User exists: %s",
    3: "Wrong login or password",
    4: "User with id %d does not exist",
    5: "Sticker %d does not exist",
    6: "Empty message",
    7: "Name requires: at least 4 symbols",
    8: "Password requires: at least 8 symbols, uppercase and lowercase letters, digits",
    400: "Bad request",
    404: "Not found",
    401: "Authorization required",
    403: "Forbidden",
    405: "Method not allowed",
    500: "Internal server error"
}


def get_time(widened=False):
    return int(time.time() * (1000 if widened else 1))


def sleep(t=.5):
    time.sleep(t)


def get_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()


def get_salt(size=16):
    alpha = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.SystemRandom().choice(alpha) for _ in range(size))


def as_str(s):
    return '"%s"' % s


def get_error_data(e) -> tuple:
    lst = str(e).split(':')[0].split(' ', 1)
    return int(lst[0]), lst[1]


def get_error_by_code(code):
    return ERROR_FORMAT % (code, ERROR_DICTIONARY[code])


def get_extended_error_by_code(code, fmt_tuple):
    return ERROR_FORMAT % (code, ERROR_DICTIONARY[code] % fmt_tuple)


def get_log_in_response(user_id, token):
    return json.dumps({'token': token, 'id': user_id})


def get_peer_id(user1_id, user2_id):
    return min(user1_id, user2_id) * MAX_USERS + max(user1_id, user2_id)


def get_user_ids(peer_id):
    return peer_id // MAX_USERS, peer_id % MAX_USERS


def is_password_satisfied(password):
    return len(password) >= 8 and password.upper() != password \
           and password.lower() != password
