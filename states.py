#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from aiogram.dispatcher.filters.state import StatesGroup, State


class BotStates(StatesGroup):
    CONVERT_TYPE = State()  # Выбрать из какого типа файлов конвертировать
    CONVERT_FORMAT = State()  # Выбрать формат куда конвертировать
    EDIT_VIDEO = State()  # Выбор как редактировать видео
    EDIT_VIDEO_OPTIONS = State()  # Дополнительные параметры для редактирования или файл

    EDIT_AUDIO = State()  # Выбор как редактировать аудио
    EDIT_AUDIO_OPTIONS = State()  # Дополнительные параметры для редактирования или файл

    ACTION = State()  # Выполнение задачи

    MAIL = State()  # Меню админа --> рассылка
