# -*- coding: utf-8 -*-

import telebot
import pymongo
import sys

sys.setrecursionlimit(10000)
telebot.apihelper.proxy = {'https': 'https://51.15.141.85:3128'}
app = telebot.TeleBot('651144452:AAG0jiqcGQiMoo5deKRaL_-rwCx6B1IUec4')
telebot.logger.setLevel(100)
client = pymongo.MongoClient()
database = client.GOTO_FM
