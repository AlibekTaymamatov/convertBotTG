from typing import Union
from aiogram import types
import mimetypes
import config
import logging

logger = logging.getLogger("utils")


async def get_path(media: types.Message):
    file_id = get_file_id(media)
    file = await media.bot.get_file(file_id)
    return file.file_path.replace("/", "\\")


def get_extension(media: types.Message, working=True, name=False, fullname=False):
    if media.animation:
        file_name = (config.strings["animation"] or media.animation.file_name) + ".GIF"
    elif media.voice:
        file_name = config.strings["voice"] + (".VOICE_" if not working else ".ogg")
    elif media.photo:
        file_name = config.strings["photo"] + (".PHOTO_" if not working else ".jpeg")
    elif media.sticker:
        if media.sticker.is_animated:
            file_name = config.strings["sticker"] + ".tgs"
        else:
            file_name = config.strings["sticker"] + ".webp"
    elif media.audio:
        file_name = media.audio.file_name
    elif media.document:
        file_name = media.document.file_name
    elif media.video:
        file_name = media.video.file_name
    elif media.video_note:
        file_name = config.strings["video_note"] + (".VIDEO_NOTE_" if not working else ".mp4")
    else:
        file_name = config.strings["undefined"] + "не_указан.undefined"
    if not file_name:
        file_name = "file" + get_type(media)
    split = ("placeholder" + file_name).split(".")
    if len(split) <= 1:
        return ".undefined"
    extension = split[-1].upper()
    if name:
        return file_name.split(".", maxsplit=1)[0]
    if fullname:
        return file_name.split(".", maxsplit=1)[0] + "." + get_extension(media)
    if extension in config.ALIASES.keys():
        return config.ALIASES[extension]
    return extension


def get_file_id(message: types.Message):
    file_id = None
    if message.voice:
        file_id = message.voice.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    elif message.audio:
        file_id = message.audio.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.video_note:
        file_id = message.video_note.file_id
    elif message.sticker:
        file_id = message.sticker.file_id
    return file_id


def get_type(message: types.Message):
    type_ = None
    if message.voice:
        type_ = mimetypes.guess_extension(message.voice.mime_type)
    elif message.photo:
        type_ = mimetypes.guess_extension("image/jpeg")
    elif message.sticker:
        type_ = mimetypes.guess_extension("image/jpeg")
    elif message.audio:
        type_ = mimetypes.guess_extension(message.audio.mime_type)
    elif message.document:
        type_ = mimetypes.guess_extension(message.document.mime_type)
    elif message.video:
        type_ = mimetypes.guess_extension(message.video.mime_type)
    elif message.video_note:
        type_ = mimetypes.guess_extension("video/mp4")
    return type_


def get_file_size(message: types.Message):
    if message.voice:
        file_size = message.voice.file_size
    elif message.photo:
        file_size = message.photo[-1].file_size
    elif message.audio:
        file_size = message.audio.file_size
    elif message.document:
        file_size = message.document.file_size
    elif message.video:
        file_size = message.video.file_size
    elif message.sticker:
        file_size = message.sticker.file_size
    elif message.video_note:
        file_size = message.video_note.file_size
    else:
        file_size = 12321332134123123  # нет величины размера, защита от обхода ограничения
    return file_size


def get_list(types_: Union[dict, list]):
    if isinstance(types_, dict):
        types_ = types_.values()
    return list(filter(
        lambda x: not x.endswith("_"), types_
    ))


def check_all(media: types.Message, extensions: dict = None, size: int = None, type_: str = None, working: bool=False):
    file_size = get_file_size(media)
    if size:
        if file_size > size:
            return False, config.strings["too_big"].format(size / 1024 / 1024), None
    extension = get_extension(media, working=working)
    logger.debug("File extension is " + extension)
    if type_:
        if extension in config.TYPES_META[type_].values():
            size = config.SIZE_META[type_]
            if file_size > size:
                return False, config.strings["too_big"].format(size / 1024 / 1024), None
            return True, None, None
        else:
            return False, config.strings["bad_extension"].format(", ".join(get_list(config.TYPES_META[type_]))), None
    if extension in config.TXT_TYPES.values():
        type_ = "txt"
        size = config.MAX_FILE_SIZE_TXT
        big = file_size > size
    elif extension in config.PHOTO_TYPES.values():
        type_ = "photo"
        size = config.MAX_FILE_SIZE_PHOTO
        big = file_size > size
    elif extension in config.VIDEO_TYPES.values():
        type_ = "video"
        size = config.MAX_FILE_SIZE_VIDEO
        big = file_size > size
    elif extension in config.AUDIO_TYPES.values():
        type_ = "audio"
        size = config.MAX_FILE_SIZE_AUDIO
        big = file_size > size
    elif extension in config.EXEL_TYPES.values():
        type_ = "exel"
        size = config.MAX_FILE_SIZE_TXT
        big = file_size > size
    else:
        if extensions:
            return False, config.strings["bad_extension"].format(", ".join(get_list(extensions))), None
        else:
            return False, config.strings["unknown"], None
    if big:
        return False, config.strings["too_big"].format(size / 1024 / 1024), None
    return True, None, type_
