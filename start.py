# -*- coding: utf-8 -*-

from goto_fm import app, get_user, get_price, database


@app.message_handler(commands=['start', 'help'])
def start(m):
    user = get_user(m.chat.id)
    database.users.update({'id': m.chat.id},
                          {'$inc': {'balance': 10}})
    app.send_message(m.chat.id,
                     text=f'*Меню*\n'
                          f'*Ваш рейтинг:* {user["reputation"]} ед.\n'
                          f'*Баланс:* {user["balance"]} GT.\n'
                          f'*Цена:* {get_price(user["reputation"])} GT.',
                     parse_mode='Markdown')

