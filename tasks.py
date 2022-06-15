#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import uuid
from typing import Union
# import subprocess
from io import BytesIO
from aioify import aioify
from PIL import Image
from aiogram import types
from aiogram.types import InputFile
import comtypes.client
import shutil
# import time
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from pydub import AudioSegment
import mimetypes
import logging
import config
import pandas as pd
from comtypes import CoInitialize

from utils import check_all, get_extension, get_file_id, get_file_size, get_list, get_path, get_type

logger = logging.getLogger("Tasks")

os.system("del /Q /S temp\\*")  # Очистка временных файлов если не были удалены автоматически


class Task:
    def __init__(self, message: types.Message, media: types.Message):
        self.message = message
        self.media = media
        self.media2 = None

    async def run(self):
        """Запускает задачу"""


class PhotoTask(Task):
    def __init__(self, message: types.Message, media: types.Message, to_format):
        super().__init__(message, media)
        self.photo = to_format == "PHOTO_"
        self.to_format = to_format if not self.photo else "JPEG"

    async def run(self):
        type_ = get_type(self.media)
        type_ = type_ if type_ else "JPG"
        await self.message.edit_text(
            config.strings["convert"].format(type_, self.to_format) + config.strings["working"]
        )
        path = await get_path(self.media)
        with open(path, "rb") as f:
            b = BytesIO(f.read())
        try:
            image = Image.open(b)
            image_stream = BytesIO()
            image_stream.name = f"{get_extension(self.media, name=True)}.{self.to_format}"
            await self.message.edit_text(
                config.strings["convert"].format(type_, self.to_format) + config.strings["exporting"]
            )
            try:
                image.save(image_stream, self.to_format)
            except OSError:
                image_stream.seek(0)
                image = image.convert('RGB')
                image.save(image_stream, self.to_format)
            except ValueError:
                image_stream.seek(0)
                image.info.pop('background', None)
                image.save(image_stream, self.to_format)
            image_stream.seek(0)
            await self.message.edit_text(
                config.strings["convert"].format(type_, self.to_format) + config.strings["uploading"]
            )
            if self.photo:
                await self.media.reply_photo(
                    image_stream, caption=config.strings["converted"].format(type_, self.to_format)
                )
            else:
                await self.media.reply_document(
                    image_stream, caption=config.strings["converted"].format(type_, self.to_format)
                )
            await self.message.delete()
        except Exception as e:
            logging.info(f"[PhotoTask]: {e}", exc_info=True)
            await self.message.edit_text(config.strings["not_supported"].format(self.to_format))


class AudioTask(Task):
    def __init__(self, message: types.Message, media: types.Message, to_format):
        super().__init__(message, media)
        self.to_format = to_format
        self.voice = self.to_format == "VOICE_"

    async def run(self):
        type_ = get_type(self.media)
        await self.message.edit_text(
            config.strings["convert"].format(type_, self.to_format) + config.strings["working"]
        )
        path = await get_path(self.media)
        try:
            with open(path, "rb") as f:
                au = BytesIO(f.read())
            au.seek(0)
            await self.message.edit_text(
                config.strings["convert"].format(type_, self.to_format) + config.strings["exporting"]
            )
            audio = AudioSegment.from_file(au)
            m = BytesIO()
            m.name = get_extension(self.media, name=True) + "." + self.to_format
            audio.split_to_mono()
            if self.voice:
                audio.export(m, format="ogg", bitrate="64k", codec="libopus")
            else:
                audio.export(m, format=self.to_format.lower())
            m.seek(0)
            await self.message.edit_text(
                config.strings["convert"].format(type_, self.to_format) + config.strings["uploading"]
            )
            if self.voice:
                await self.media.reply_voice(m, caption=config.strings["converted"].format(type_, self.to_format))
            else:
                await self.media.reply_document(m, caption=config.strings["converted"].format(type_, self.to_format))
            await self.message.delete()
        except Exception as e:
            logging.info(f"[AudioTask]: {e}", exc_info=True)
            await self.message.edit_text(config.strings["not_supported"].format(self.to_format))


class VideoTask(Task):
    def __init__(self, message: types.Message, media: types.Message, to_format: str):
        super().__init__(message, media)
        self.video_note = to_format == "VIDEO_NOTE_"
        self.to_format = to_format if not self.video_note else "MP4"

    async def run(self):
        filename = str(uuid.uuid4().hex)
        type_ = get_type(self.media)
        out_file = os.path.join("temp", filename + "." + self.to_format)
        await self.message.edit_text(
            config.strings["convert"].format(type_, self.to_format) + config.strings["working"]
        )
        path = await get_path(self.media)
        await self.message.edit_text(
            config.strings["convert"].format(type_, self.to_format) + config.strings["exporting"]
        )
        result = os.system(f"ffmpeg -i {path} -vcodec copy -acodec copy {out_file}")
        if result != 0:  # если успешно, оно вернёт 0
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported"].format(self.to_format))
        if self.video_note:
            out_file_crop = os.path.join("temp", "crop" + filename + "." + self.to_format)
            await self.crop(out_file, out_file_crop)
            os.system(f"del /f {out_file}")
            out_file = out_file_crop
        await self.message.edit_text(
            config.strings["convert"].format(type_, self.to_format) + config.strings["uploading"]
        )
        if self.video_note:
            await self.media.reply_video_note(
                InputFile(out_file, filename=get_extension(self.media, name=True) + "." + self.to_format),
            )
        else:
            await self.media.reply_document(
                InputFile(out_file, filename=get_extension(self.media, name=True) + "." + self.to_format),
                caption=config.strings["converted"].format(type_, self.to_format)
            )
        await self.message.delete()
        os.system(f"del /f {out_file}")

    @staticmethod
    @aioify
    def crop(out_file, out_file_crop):
        video = VideoFileClip(out_file)
        video.reader.close()
        w, h = video.size
        m = min(w, h)
        box = [(w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2]
        video = video.crop(*box)
        video.write_videofile(out_file_crop)


class TextTask(Task):
    def __init__(self, message: types.Message, media: types.Message, to_format: str, from_message=False):
        super().__init__(message, media)
        self.as_text = to_format == "AS_TEXT_"
        self.from_message = from_message
        self.to_format = to_format if not self.as_text else "TXT"

    async def run(self):
        filename = str(uuid.uuid4().hex)
        if self.from_message:
            with open(f"temp\\{filename}.txt", "w", encoding='utf-8') as file:
                file.write(self.media.text)
            type_ = ".txt"
        else:
            type_ = get_type(self.media)
        await self.message.edit_text(
            config.strings["convert"].format(type_, self.to_format) + config.strings["working"]
        )
        path = await get_path(self.media) if not self.from_message else f"temp\\{filename}.txt"
        out_file = os.path.join("temp", filename + "." + self.to_format)
        try:
            await self.message.edit_text(
                config.strings["convert"].format(type_, self.to_format) + config.strings["exporting"]
            )
            await self.word_work(path, out_file, self.to_format, self.from_message)
            if self.as_text:
                with open(out_file, "r", encoding='utf-8') as f:
                    text = f.read()
                await self.message.edit_text(text[:4096])
                if len(text) > 4096:
                    await self.media.reply_document(InputFile(out_file, filename=config.strings["to_file"]),
                                                    caption=config.strings["too_long_text"])
                return
            await self.message.edit_text(
                config.strings["convert"].format(type_, self.to_format) + config.strings["uploading"]
            )
            await self.media.reply_document(
                InputFile(out_file, filename=get_extension(self.media, name=True) + "." + self.to_format),
                caption=config.strings["converted"].format(type_, self.to_format)
            )
            await self.message.delete()
        except Exception as e:
            logging.info(f"[TextTask]: {e}", exc_info=True)
            await self.message.edit_text(config.strings["not_supported"].format(self.to_format))
        os.system(f"del /f {out_file} {path if path.startswith('temp') else ''}")

    @staticmethod
    @aioify
    def word_work(in_file, out_file, to_format, from_message=False):
        in_file = os.path.abspath(in_file)
        out_file = os.path.abspath(out_file)
        if from_message and to_format == "TXT":
            os.rename(in_file, out_file)
            return
        CoInitialize()  # пайчарм может ругаться, но на самом деле все ок
        word = comtypes.client.CreateObject('Word.Application')
        doc = word.Documents.Open(in_file)
        doc.SaveAs(os.path.abspath(out_file), FileFormat=config.WD_ENUM[to_format])
        doc.Close()
        word.Quit()


class ExelTask(Task):
    def __init__(self, message: types.Message, media: types.Message, to_format: str):
        super().__init__(message, media)
        self.pdf = to_format == "PDF_"
        self.to_format = to_format if not self.pdf else "PDF"

    async def run(self):
        filename = str(uuid.uuid4().hex)
        path = await get_path(self.media)
        from_format = get_extension(self.media).upper()
        new_path = os.path.join("temp", "from_" + filename + "." + from_format.lower())
        out_file = os.path.join("temp", filename + "." + self.to_format.lower())
        type_ = get_type(self.media)
        shutil.copy2(path, new_path)

        try:
            await self.message.edit_text(
                config.strings["convert"].format(type_, self.to_format) + config.strings["exporting"]
            )
            await self.exel_work(new_path, out_file, self.to_format, from_format)
            await self.message.edit_text(
                config.strings["convert"].format(type_, self.to_format) + config.strings["uploading"]
            )
            await self.media.reply_document(
                InputFile(out_file, filename=get_extension(self.media, name=True) + "." + self.to_format),
                caption=config.strings["converted"].format(type_, self.to_format)
            )
            await self.message.delete()
        except Exception as e:
            logging.info(f"[TextTask]: {e}", exc_info=True)
            await self.message.edit_text(config.strings["not_supported"].format(self.to_format))
        os.system(f"del /f {out_file} {new_path}")

    @staticmethod
    @aioify
    def exel_work(in_file, out_file, to_format, from_format):
        if from_format == "CSV":
            read_file = pd.read_csv(in_file)
            read_file.to_excel(out_file, engine="xlsxwriter", index = None, header=False)
        else:
            if to_format == "CSV":
                read_file = pd.read_excel(in_file)
                read_file.to_csv(out_file, index = None, header=False)
            else:
                read_file = pd.read_excel(in_file)
                read_file.to_excel(out_file, engine="xlsxwriter", index = None, header=False)


class VideoCutTask(Task):
    def __init__(self, message: types.Message, media: types.Message, time_from: str, time_to: str):
        super().__init__(message, media)
        self.time_from = time_from
        self.time_to = time_to

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(
            config.strings["cut"].format(self.time_from, self.time_to) + config.strings["working"]
        )
        in_file = await get_path(self.media)
        out_file = os.path.join("temp", "cut" + filename + "." + get_extension(self.media))
        await self.message.edit_text(
            config.strings["cut"].format(self.time_from, self.time_to) + config.strings["exporting"]
        )
        try:
            ffmpeg_extract_subclip(in_file, self.time_from, self.time_to, targetname=out_file)
        except Exception as e:
            logging.error(f"[VideoCutTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        await self.message.edit_text(
            config.strings["cut"].format(self.time_from, self.time_to) + config.strings["uploading"]
        )
        await self.media.reply_document(
            InputFile(out_file, filename=get_extension(self.media, fullname=True)),
            caption=config.strings["edited"] + config.strings["cut"].format(self.time_from, self.time_to)
        )
        await self.message.delete()
        os.system(f"del /f {out_file}")


class VideoAddTask(Task):
    def __init__(self, message: types.Message, media: types.Message, media2: types.Message):
        super().__init__(message, media)
        self.media2 = media2

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(config.strings["add"] + config.strings["working"])
        in_file = await get_path(self.media)
        in_file2 = await get_path(self.media2)
        out_file = os.path.join("temp", filename + "." + get_extension(self.media))
        await self.message.edit_text(config.strings["add"] + config.strings["exporting"])
        try:
            await self.add(in_file, in_file2, out_file)
        except Exception as e:
            logging.warning(f"[VideoAddTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        await self.message.edit_text(config.strings["add"] + config.strings["uploading"])
        await self.media.reply_document(
            InputFile(out_file, filename=get_extension(self.media, fullname=True)),
            caption=config.strings["edited"] + config.strings["add"]
        )
        await self.message.delete()
        os.system(f"del /f {out_file}")

    @staticmethod
    @aioify
    def add(in_file, in_file2, out_file):
        clip = VideoFileClip(in_file)
        clip2 = VideoFileClip(in_file2)
        final_clip = concatenate_videoclips([clip, clip2], method="compose")
        final_clip.write_videofile(out_file)


class VideoSpeedTask(Task):
    def __init__(self, message: types.Message, media: types.Message, speed_: float):
        super().__init__(message, media)
        self.speed_ = speed_

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(config.strings["speed"].format(self.speed_) + config.strings["working"])
        path = await get_path(self.media)
        out_file = os.path.join("temp", filename + "." + get_extension(self.media))
        await self.message.edit_text(config.strings["speed"].format(self.speed_) + config.strings["exporting"])
        try:
            await self.speed(path, out_file, self.speed_)
        except Exception as e:
            logging.warning(f"[VideoSpeedTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        await self.message.edit_text(config.strings["speed"].format(self.speed_) + config.strings["uploading"])
        await self.media.reply_document(
            InputFile(out_file, filename=get_extension(self.media, fullname=True)),
            caption=config.strings["edited"] + config.strings["speed"].format(self.speed_)
        )
        await self.message.delete()
        os.system(f"del /f {out_file}")

    @staticmethod
    @aioify
    def speed(path, out_file, speed_):
        clip = VideoFileClip(path)
        clip = clip.speedx(speed_)
        clip.write_videofile(out_file)


class VideoExtractTask(Task):
    def __init__(self, message: types.Message, media: types.Message):
        super().__init__(message, media)

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(config.strings["extract"] + config.strings["working"])
        path = await get_path(self.media)
        out_file = os.path.join("temp", filename + ".mp3")
        await self.message.edit_text(config.strings["extract"] + config.strings["exporting"])
        try:
            await self.extract(path, out_file)
        except Exception as e:
            logging.warning(f"[VideoExtractTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        await self.message.edit_text(config.strings["extract"] + config.strings["uploading"])
        await self.media.reply_document(
            InputFile(out_file, filename=get_extension(self.media, name=True) + ".mp3"),
            caption=config.strings["edited"] + config.strings["extract"]
        )
        await self.message.delete()
        os.system(f"del /f {out_file}")

    @staticmethod
    @aioify
    def extract(path, out_file):
        audio_clip = AudioFileClip(path)
        audio_clip.write_audiofile(out_file)


class VideoReplaceTask(Task):
    def __init__(self, message: types.Message, media: types.Message, media2: types.Message):
        super().__init__(message, media)
        self.media2 = media2

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(config.strings["replace"] + config.strings["working"])
        path = await get_path(self.media)
        audio_path = await get_path(self.media2)
        out_file = os.path.join("temp", filename + ".mp4")
        await self.message.edit_text(config.strings["replace"] + config.strings["exporting"])
        try:
            await self.replace(path, audio_path, out_file)
        except Exception as e:
            logging.warning(f"[VideoReplaceTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        await self.message.edit_text(config.strings["replace"] + config.strings["uploading"])
        await self.media.reply_document(
            InputFile(out_file, filename=get_extension(self.media, name=True) + ".MP4"),
            caption=config.strings["edited"] + config.strings["replace"]
        )
        await self.message.delete()
        os.system(f"del /f {out_file}")

    @staticmethod
    @aioify
    def replace(path, audio_path, out_file):
        clip = VideoFileClip(path)
        audio_clip = AudioFileClip(audio_path)
        clip.audio = audio_clip
        clip.write_videofile(out_file, codec="libx264")


class AudioFvTask(Task):
    def __init__(self, message: types.Message, media: types.Message):
        super().__init__(message, media)
        self.audio = bool(media.audio)

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(config.strings["fv"] + config.strings["working"])
        path = await get_path(self.media)
        out_file = os.path.join("temp", filename + get_extension(self.media))
        try:
            with open(path, "rb") as f:
                au = BytesIO(f.read())
            au.seek(0)
            await self.message.edit_text(config.strings["fv"] + config.strings["exporting"])
            audio = AudioSegment.from_file(au)
            m = BytesIO()
            m.name = get_extension(self.media, fullname=True)
            audio.split_to_mono()
            audio.export(m, format=get_extension(self.media).lower())
            m.seek(0)
            await self.message.edit_text(config.strings["fv"] + config.strings["uploading"])
            if self.audio:
                await self.media.reply_audio(m, caption=config.strings["edited"] + config.strings["fv"])
            else:
                await self.media.reply_document(m, caption=config.strings["edited"] + config.strings["fv"])
            await self.message.delete()
        except Exception as e:
            logging.warning(f"[AudioFvTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        os.system(f"del /f {out_file}")


class AudioSpeedTask(Task):
    def __init__(self, message: types.Message, media: types.Message, speed: float):
        super().__init__(message, media)
        self.speed = speed
        self.audio = bool(media.audio)

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(config.strings["speed"].format(self.speed) + config.strings["working"])
        path = await get_path(self.media)
        out_file = os.path.join("temp", filename + get_extension(self.media))
        await self.message.edit_text(config.strings["speed"].format(self.speed) + config.strings["exporting"])
        try:
            with open(path, "rb") as f:
                au = BytesIO(f.read())
            au.seek(0)
            audio = AudioSegment.from_file(au)
            del au  # не уверен что имеет смысл, тот же cpython бы автоматом очистил
            audio = self.speed_change(audio, self.speed)
            out = BytesIO()
            out.name = get_extension(self.media, fullname=True)
            audio.export(out, format=get_extension(self.media).lower())
            out.seek(0)
            await self.message.edit_text(config.strings["speed"].format(self.speed) + config.strings["uploading"])
            if self.audio:
                await self.media.reply_audio(
                    out, caption=config.strings["edited"] + config.strings["speed"].format(self.speed)
                )
            else:
                await self.media.reply_document(
                    out, caption=config.strings["edited"] + config.strings["speed"].format(self.speed)
                )
            await self.message.delete()
        except Exception as e:
            logging.warning(f"[AudioSpeedTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        os.system(f"del /f {out_file}")

    @staticmethod  # https://stackoverflow.com/questions/51434897/how-to-change-audio-playback-speed-using-pydub
    def speed_change(sound, speed=1.0):
        sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
            "frame_rate": int(sound.frame_rate * speed)
        })
        return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


class AudioCutTask(Task):
    def __init__(self, message: types.Message, media: types.Message, time_from: str, time_to: str):
        super().__init__(message, media)
        self.time_from = time_from
        self.time_to = time_to
        self.audio = bool(media.audio)

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(
            config.strings["cut"].format(self.time_from, self.time_to) + config.strings["working"]
        )
        in_file = await get_path(self.media)
        out_file = os.path.join("temp", "cut" + filename + "." + get_extension(self.media))
        await self.message.edit_text(
            config.strings["cut"].format(self.time_from, self.time_to) + config.strings["exporting"]
        )
        try:
            ffmpeg_extract_subclip(in_file, self.time_from, self.time_to, targetname=out_file)
        except Exception as e:
            logging.error(f"[VideoCutTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        await self.message.edit_text(
            config.strings["cut"].format(self.time_from, self.time_to) + config.strings["uploading"]
        )
        if self.audio:
            await self.media.reply_audio(
                InputFile(out_file, filename=get_extension(self.media, fullname=True)),
                caption=config.strings["edited"] + config.strings["cut"].format(self.time_from, self.time_to)
            )
        else:
            await self.media.reply_document(
                InputFile(out_file, filename=get_extension(self.media, fullname=True)),
                caption=config.strings["edited"] + config.strings["cut"].format(self.time_from, self.time_to)
            )
        await self.message.delete()
        os.system(f"del /f {out_file}")


class AudioAddTask(Task):
    def __init__(self, message: types.Message, media: types.Message, media2: types.Message):
        super().__init__(message, media)
        self.media2 = media2
        self.audio = bool(media.audio)

    async def run(self):
        filename = str(uuid.uuid4().hex)
        await self.message.edit_text(config.strings["add"] + config.strings["working"])
        in_file = await get_path(self.media)
        in_file2 = await get_path(self.media2)
        out_file = os.path.join("temp", filename + "." + get_extension(self.media))
        await self.message.edit_text(config.strings["add"] + config.strings["exporting"])
        try:
            await self.add(in_file, in_file2, out_file, get_extension(self.media))
        except Exception as e:
            logging.warning(f"[VideoAddTask]: {e}", exc_info=True)
            os.system(f"del /f {out_file}")
            return await self.message.edit_text(config.strings["not_supported_video"])
        await self.message.edit_text(config.strings["add"] + config.strings["uploading"])
        if self.audio:
            await self.media.reply_audio(
                InputFile(out_file, filename=get_extension(self.media, fullname=True)),
                caption=config.strings["edited"] + config.strings["add"]
            )
        else:
            await self.media.reply_document(
                InputFile(out_file, filename=get_extension(self.media, fullname=True)),
                caption=config.strings["edited"] + config.strings["add"]
            )
        await self.message.delete()
        os.system(f"del /f {out_file}")

    @staticmethod
    @aioify
    def add(in_file, in_file2, out_file, extension):
        clip = AudioSegment.from_file(in_file)
        clip2 = AudioSegment.from_file(in_file2)
        final_clip = clip + clip2
        final_clip.export(out_file, format=extension)
