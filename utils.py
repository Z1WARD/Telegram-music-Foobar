# -*- encoding: utf-8 -*-

from goto_fm import database


def get_user(uid: int) -> dict:
    user = database.users.find_one({'id': uid})

    if not user:
        user = {
            'id': uid,
            'reputation': 0,
            'balance': 0
        }

        database.users.insert(user)

    return user


def get_price(reputation: int) -> int:
    if reputation >= 120:
        return 0

    if reputation >= 90:
        return 1

    if reputation >= 35:
        return 2

    return 3
