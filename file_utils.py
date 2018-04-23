from base64 import b64decode
import os

STICKERS_DIR = os.path.join(os.path.dirname(__file__), 'stickers/')
AVATARS_DIR = os.path.join(os.path.dirname(__file__), 'avatar/')

STUB_PATH = 'haine.png'


def init_before():
    try:
        os.mkdir(STICKERS_DIR)
        os.mkdir(AVATARS_DIR)
    except FileExistsError:
        pass


def save_sticker(sticker, id):
    try:
        sticker = b64decode(sticker)
    except TypeError as e:
        print(e)
        return False
    if not is_png(sticker):
        return False
    with open(get_sticker_path(id), 'wb') as f:
        f.write(sticker)
    return True


def get_sticker_path(id):
    return STICKERS_DIR + str(id) + '.png'


def save_avatar(avatar, id):
    try:
        avatar = b64decode(avatar)
    except TypeError:
        return False
    if not is_jpg(avatar) and not is_png(avatar):
        return False
    with open(get_avatar_path(id), 'wb') as f:
        f.write(avatar)
    return True


def get_avatar_path(id, stub=False):
    path = AVATARS_DIR + str(id)
    if not stub:
        return path
    else:
        if os.path.isfile(path):
            return path
        else:
            return AVATARS_DIR + STUB_PATH


def remove_avatar(id):
    path = get_avatar_path(id)
    if os.path.isfile(path):
        os.remove(path)


def is_png(raw):
    return raw[:8] == b'\x89PNG\r\n\x1a\n'


def is_jpg(raw):
    return raw[:3] == b'\xff\xd8\xff'
