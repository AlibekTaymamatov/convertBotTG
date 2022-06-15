from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import config


def split(lst, split_by):
    return [lst[i:i + split_by] for i in range(0, len(lst), split_by)]


def buttons(func: callable, names_: dict, from_format=None, split_by=3):
    keyboard = InlineKeyboardMarkup(row_width=split_by)
    names_ = {v: k for k, v in names_.items()}  # перевернет словарь
    names_list = list(names_.keys())
    if from_format and from_format in names_list:
        names_list.remove(from_format)
    if from_format in config.NOT_ALLOWED.keys():
        for x in config.NOT_ALLOWED[from_format]:
            if x in names_list:
                names_list.remove(x)
    for x in config.NOT_ALLOWED["ONLY_ENTER"]:
        if x in names_list:
            names_list.remove(x)

    names_list = split(names_list, split_by)
    for name in names_list:
        block = [InlineKeyboardButton(names_[x], callback_data=func(x)) for x in name]
        keyboard.add(*block)
    return keyboard


def menu_buttons(names=config.MENU_KEYBOARD, main=False):
    keyboard = InlineKeyboardMarkup()
    for name, callback in names.items():
        keyboard.add(InlineKeyboardButton(name, callback_data=callback))
    if main:
        keyboard.add(MAIN_MENU)
    return keyboard


MAIN_MENU = InlineKeyboardButton(config.strings["main_menu"], callback_data="main_menu")
FROM_MESSAGE = InlineKeyboardButton(config.strings["from_message"], callback_data="from_message")
MAIN_MENU_KEYBOARD = InlineKeyboardMarkup()
MAIN_MENU_KEYBOARD_FROM_MESSAGE = InlineKeyboardMarkup()
MAIN_MENU_KEYBOARD_FROM_MESSAGE.add(FROM_MESSAGE)
MAIN_MENU_KEYBOARD_FROM_MESSAGE.add(MAIN_MENU)
MAIN_MENU_KEYBOARD.add(MAIN_MENU)
