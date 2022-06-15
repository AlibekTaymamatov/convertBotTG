#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from aiogram.utils.exceptions import MessageNotModified
from aiogram import Bot

import asyncio
import config
import threading


async def next_queue(task_queue_):
    """Оповестить всех о движении очереди"""
    tasks = list(task_queue_.queue)
    for task in tasks:
        position = task.message.text.split()[-1]
        if not position.isdigit():  # Если работа над задачей уже началась
            continue
        if position == "1":  # из-за многопоточности, невозможно получить точное количество
            continue  # https://docs.python.org/3/library/queue.html#queue.Queue.qsize
        try:
            await task.message.edit_text(config.strings["queue"].format(int(position) - 1))
        except MessageNotModified:
            pass


def tasks_handler(task_queue_, bot, main_loop):
    """Обрабатывае все задачи"""
    while True:
        task = task_queue_.get()  # блокирует свой поток если очередь пустая, до получения задачи из очереди
        Bot.set_current(bot)
        wait = asyncio.run_coroutine_threadsafe(task.run(), main_loop)  # сразу вернет обьект Future
        wait.result()  # останавливает на поток до завершения задачи
        wait = asyncio.run_coroutine_threadsafe(next_queue(task_queue_), main_loop)  # ждать завершения не
        wait.result()


def run_handler(task_queue_, bot, main_loop):
    thread = threading.Thread(target=tasks_handler, args=(task_queue_, bot, main_loop))
    thread.daemon = True  # Демонизирование потока, запуск его в фоне
    thread.start()  # Запуск потока
