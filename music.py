# -*- coding: utf-8 -*-

from goto_fm import app, get_user, get_price, database, telebot
from telebot import types
from telebot.apihelper import FILE_URL
from bson.objectid import ObjectId
from threading import Timer
from pytube import YouTube
from uuid import uuid4

import os
import time
import requests


def send_notifications(song: str, blacklist: list = None):
    if blacklist is None:
        blacklist = []
    users = database.users.find({})
    song_data = database.music.find_one({'_id': ObjectId(song)})
    markup = types.InlineKeyboardMarkup()

    markup.row(types.InlineKeyboardButton('❤', callback_data=f'like_{song}'),
               types.InlineKeyboardButton('💔', callback_data=f'dislike_{song}'))
    for user in users:
        if user['id'] not in blacklist:
            try:
                app.send_audio(user['id'], audio=song_data['file'], title=song_data['title'],
                               caption=f'Вам нравится этот трек?\n'
                                       f'*Название:* {song_data["title"]}',
                               reply_markup=markup,
                               parse_mode='Markdown')

            except Exception as ex:
                print('[X] ' + str(ex))
                continue


def play_song(song: str):
    song = database.music.find_one({'_id': ObjectId(song)})
    pos = len(song['mark_pos'])
    m_sum = pos + len(song['mark_neg']) + 1
    if m_sum < 1:
        return

    percent = (pos / m_sum) * 100
    rep = {
        percent < 25: -10,
        25 <= percent < 50: -5,
        percent == 50: 0,
        50 <= percent < 75: 10,
        75 <= percent <= 100: 20
    }[True]

    database.users.update({'id': song['owner']},
                          {'$inc': {'reputation': rep}})

    file_id = str(uuid4())
    with open(f'music/{file_id}.mp3', 'wb') as f:
        try:
            f.write(requests.get(app.get_file_url(song["file"]), proxies=telebot.apihelper.proxy).content)
        except Exception as ex:
            print('[X]', str(ex))

    os.system(f'foobar2000.exe /add "music/{file_id}.mp3"')


@app.message_handler(func=lambda m: False if m.text is None else m.text.startswith('https://www.youtube.com/watch?v='))
def download_youtube(m):
    user = get_user(m.chat.id)

    if user['balance'] < get_price(user['reputation']):
        app.send_message(m.chat.id, text='Недостаточно средств!')
        return

    video = YouTube(m.text)
    stream = video.streams.filter(only_audio=True).first()
    app.send_message(m.chat.id, text='_Загрузка..._', parse_mode='Markdown')
    file_id = str(uuid4())
    stream.download('temp', file_id)
    os.rename(f'temp/{file_id}.mp4', f'temp/{file_id}.mp3')
    with open(f'temp/{file_id}.mp3', 'rb') as f:
        file = app.send_audio(m.chat.id, f, caption='_Файл получен..._', parse_mode='Markdown', title=video.title)

    database.users.update({'id': m.chat.id},
                          {'$inc': {'balance': get_price(user['reputation'])}})

    song = database.music.insert({
        'file': file.audio.file_id,
        'title': file.audio.title,
        'mark_pos': [],
        'mark_neg': [],
        'owner': m.chat.id
    })

    os.remove(f'temp/{file_id}.mp4')
    app.send_message(m.chat.id, text='Ваш трек добавлен в голосование!')
    send_notifications(song, [m.chat.id])
    Timer(30, play_song, (song,)).start()


@app.message_handler(content_types=['audio'])
def handle_music(m):
    user = get_user(m.chat.id)

    if user['balance'] < get_price(user['reputation']):
        app.send_message(m.chat.id, text='Недостаточно средств!')
        return

    if m.audio.duration > 360:
        app.send_message(m.chat.id, text='Максимальная длина аудио - 6 мин.')
        return

    database.users.update({'id': m.chat.id},
                          {'$inc': {'balance': get_price(user['reputation'])}})

    song = database.music.insert({
                                  'file': m.audio.file_id,
                                  'title': m.audio.title,
                                  'mark_pos': [],
                                  'mark_neg': [],
                                  'owner': m.chat.id
                                 })

    app.send_message(m.chat.id, text='Ваш трек добавлен в голосование!')
    send_notifications(song, [m.chat.id])
    Timer(12, play_song, (song,)).start()


@app.callback_query_handler(func=lambda call: call.data.startswith('like_'))
def like_song(c):
    song = c.data[5:]
    song = database.music.find_one({'_id': ObjectId(song)})

    if c.message.chat.id in song['mark_pos']:
        pass

    elif c.message.chat.id in song['mark_neg']:
        database.music.update({'_id': ObjectId(song['_id'])},
                              {
                                  '$pull': {'mark_neg': c.message.chat.id},
                                  '$push': {'mark_pos': c.message.chat.id}
                              })

    else:
        database.music.update({'_id': ObjectId(song['_id'])},
                              {
                                  '$push': {'mark_pos': c.message.chat.id}
                              })

    song = database.music.find_one({'_id': ObjectId(song['_id'])})
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(f'❤ {len(song["mark_pos"])}', callback_data=f'like_{song["_id"]}'),
               types.InlineKeyboardButton(f'💔 {len(song["mark_neg"])}', callback_data=f'dislike_{song["_id"]}'))

    app.edit_message_reply_markup(chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=markup)
    app.answer_callback_query(c.id, show_alert=False, text='Лайк поставлен!')


@app.callback_query_handler(func=lambda call: call.data.startswith('dislike_'))
def like_song(c):
    song = c.data[8:]
    song = database.music.find_one({'_id': ObjectId(song)})

    if c.message.chat.id in song['mark_neg']:
        pass

    elif c.message.chat.id in song['mark_pos']:
        database.music.update({'_id': ObjectId(song['_id'])},
                              {
                                  '$pull': {'mark_pos': c.message.chat.id},
                                  '$push': {'mark_neg': c.message.chat.id}
                              })

    else:
        database.music.update({'_id': ObjectId(song['_id'])},
                              {
                                  '$push': {'mark_neg': c.message.chat.id}
                              })

    song = database.music.find_one({'_id': ObjectId(song['_id'])})
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(f'❤ {len(song["mark_pos"])}', callback_data=f'like_{song["_id"]}'),
               types.InlineKeyboardButton(f'💔 {len(song["mark_neg"])}', callback_data=f'dislike_{song["_id"]}'))

    app.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=markup)
    app.answer_callback_query(c.id, show_alert=False, text='Дизлайк поставлен!')
