import asyncio
import logging
import queue
from aiogram import Bot, Dispatcher, executor, types
from aiogram.bot.api import TelegramAPIServer
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import ChatNotFound, BotBlocked
from queue_ import run_handler
from tasks import PhotoTask, AudioTask, VideoTask, TextTask, ExelTask, \
    VideoCutTask, VideoAddTask, VideoSpeedTask, VideoExtractTask, VideoReplaceTask, AudioFvTask, AudioSpeedTask, \
    AudioCutTask, AudioAddTask
from utils import check_all, get_extension, get_list
import config
from buttons import buttons, menu_buttons, MAIN_MENU, MAIN_MENU_KEYBOARD, MAIN_MENU_KEYBOARD_FROM_MESSAGE
from states import BotStates as bs
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main-bot")

task_queue = queue.Queue()  # Очердь задач
big_task_queue = queue.Queue()

local_server = TelegramAPIServer.from_base(config.API_URL)
storage = MemoryStorage()
bot = Bot(token=config.API_TOKEN, server=local_server)
dp = Dispatcher(bot, storage=storage)


#  Отправка меню и сброс состояния
@dp.message_handler(commands=['start', 'menu'], state="*")
async def send_welcome(message: types.Message, state: FSMContext):
    db.User.get_or_create(id=message.from_user.id)
    await state.reset_state()
    await message.reply(config.strings["start"], reply_markup=menu_buttons())

# Отправка помощи
@dp.message_handler(commands=['help'], state="*")
async def send_help(message: types.Message):
    help_txt = ""
    for name, type_ in config.TYPES.items():
        temp = ", ".join(get_list(config.TYPES_META[type_]))
        help_txt += f"{name}\n" + temp + "\n"
    await message.reply(config.strings["help"].format(help_txt), reply_markup=menu_buttons())


#  Админ часть
@dp.message_handler(commands=['mail'], state="*")
async def send_mail_query(message: types.Message, state: FSMContext):
    check_db = db.User.get_or_none(id=message.from_user.id)
    if check_db:
        check_db = check_db.admin
    check_config = message.from_user.id in config.ADMIN_IDS
    if not (check_db or check_config):
        return

    keyboard = menu_buttons({"Отменить": "cancel"})
    await message.reply("Отправьте сообщение которое хотите разослать", reply_markup=keyboard)

    await bs.MAIL.set()


@dp.message_handler(state=bs.MAIL)
async def choice_mail(message: types.Message, state: FSMContext):
    keyboard = menu_buttons({"Переслать": "forward", "Скопировать": "copy"})
    await message.reply("Как разослать сообщение?", reply_markup=keyboard)
    await state.reset_state()


@dp.callback_query_handler(lambda c: c.data == "copy", state="*")
async def copy_message(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message

    await message.edit_text(config.strings["admin_mail_start"])
    for user in db.User.select():
        try:
            await message.reply_to_message.copy_to(user.id)
        except (ChatNotFound, BotBlocked):
            user.delete_instance()
        except Exception as e:
            logger.warning(f"While copy message: {e}", exc_info=True)
    await message.edit_text(config.strings["admin_mail_end"].format(len(db.User.select())))


@dp.callback_query_handler(lambda c: c.data == "forward", state="*")
async def forward_message(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message

    await message.edit_text(config.strings["admin_mail_start"])
    for user in db.User.select():
        try:
            await message.reply_to_message.forward(user.id)
        except (ChatNotFound, BotBlocked):
            user.delete_instance()
        except Exception as e:
            logger.warning(f"While forward message: {e}", exc_info=True)
    await message.edit_text(config.strings["admin_mail_end"].format(len(db.User.select())))


@dp.callback_query_handler(lambda c: c.data == "cancel", state="*")
async def main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    await state.reset_state()
    await message.delete()


@dp.message_handler(commands=['add'], state="*")
async def add_admin(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        return
    temp = message.text.split()
    if len(temp) < 2:
        return await message.reply("Укажите ID пользователя")
    else:
        admin_id = temp[1]
    try:
        admin_id = int(admin_id)
    except ValueError:
        return await message.reply("{} не похоже на число".format(admin_id))

    model = db.User.get_or_create(id=admin_id)[0]
    model.admin = True
    model.save()
    await message.reply("{} был назначен новым администратором".format(admin_id))
    await state.reset_state()


@dp.message_handler(commands=['del'], state="*")
async def del_admin(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        return
    temp = message.text.split()
    if len(temp) < 2:
        return await message.reply("Укажите ID пользователя")
    else:
        admin_id = temp[1]
    try:
        admin_id = int(admin_id)
    except ValueError:
        return await message.reply("{} не похоже на число".format(admin_id))

    model = db.User.get_or_create(id=admin_id)[0]
    model.admin = False
    model.save()
    await message.reply("{} был назначен новым администратором".format(admin_id))
    await state.reset_state()


@dp.message_handler(commands=['list'], state="*")
async def list_admin(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        return

    cum = "Список администраторов: \n"
    query = db.User.select().where(db.User.admin == True)
    text = cum + "\n".join([str(admin.id) for admin in query])
    text += "\n" + "Список администраторов из конфига:" + "\n" + "\n".join([str(uid) for uid in config.ADMIN_IDS])
    await message.reply(text)
    await state.reset_state()


# Нажал на "Главное меню"
@dp.callback_query_handler(lambda c: c.data == "main_menu", state="*")
async def main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    await state.reset_state()
    await message.edit_text(config.strings["start"], reply_markup=menu_buttons())


# Нажал на Прератить в текст
@dp.callback_query_handler(lambda c: c.data == "from_message", state="*")
async def main_menu(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    keyboard = buttons(lambda x: f"txt:{x}:from_message", config.TXT_TYPES, "AS_TEXT_")
    await message.edit_text(config.strings["choice"], reply_markup=keyboard)


#
#  Когда человек кинул файл
#
#  Обработчики колбеков
@dp.callback_query_handler(lambda c: c.data.split(":")[0] == "photo")
async def photo_file(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    media = message.reply_to_message
    message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
    task_queue.put(PhotoTask(
        message, media, callback_query.data.split(":")[1]
    ))


@dp.callback_query_handler(lambda c: c.data.split(":")[0] == "video")
async def video_file(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    media = message.reply_to_message
    message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
    big_task_queue.put(VideoTask(
        message, media, callback_query.data.split(":")[1]
    ))


@dp.callback_query_handler(lambda c: c.data.split(":")[0] == "audio")
async def audio_file(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    media = message.reply_to_message
    message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
    big_task_queue.put(AudioTask(
        message, media, callback_query.data.split(":")[1]
    ))


@dp.callback_query_handler(lambda c: c.data.split(":")[0] == "txt")
async def txt_file(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    media = message.reply_to_message
    message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
    big_task_queue.put(TextTask(
        message, media, callback_query.data.split(":")[1], from_message=len(callback_query.data.split(":")) == 3
    ))


@dp.callback_query_handler(lambda c: c.data.split(":")[0] == "exel")
async def txt_file(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    media = message.reply_to_message
    message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
    big_task_queue.put(ExelTask(
        message, media, callback_query.data.split(":")[1]
    ))


#  Обработка входных файлов
@dp.message_handler(content_types=(types.message.ContentType.VIDEO, types.message.ContentType.VIDEO_NOTE),
                    state="*")
async def video(media: types.Message):
    allow, error, type_ = check_all(media, config.VIDEO_TYPES, config.MAX_FILE_SIZE_VIDEO)
    if not allow:
        return await media.reply(error)
    file = get_extension(media, working=False)
    keyboard = buttons(lambda x: f"video:{x}", config.TYPES_META[type_], file)
    await media.reply(config.strings["choice"], reply_markup=keyboard)


@dp.message_handler(content_types=(types.message.ContentType.PHOTO, types.message.ContentType.STICKER,
                                   types.message.ContentType.ANIMATION), state="*")
async def photo(media: types.Message):
    allow, error, type_ = check_all(media, config.PHOTO_TYPES, config.MAX_FILE_SIZE_PHOTO)
    if not allow:
        return await media.reply(error)
    file = get_extension(media, working=False)
    keyboard = buttons(lambda x: f"photo:{x}", config.TYPES_META[type_], file)
    await media.reply(config.strings["choice"], reply_markup=keyboard)


@dp.message_handler(content_types=(types.message.ContentType.VOICE, types.message.ContentType.AUDIO), state="*")
async def audio(media: types.Message):
    allow, error, type_ = check_all(media, config.AUDIO_TYPES, config.MAX_FILE_SIZE_AUDIO)
    if not allow:
        return await media.reply(error)
    file = get_extension(media, working=False)
    keyboard = buttons(lambda x: f"audio:{x}", config.TYPES_META[type_], file)
    await media.reply(config.strings["choice"], reply_markup=keyboard)


@dp.message_handler(content_types=types.message.ContentType.DOCUMENT, state="*")
async def document_analyser(media: types.Message):
    message = await media.reply(config.strings["analyzing"])
    allow, error, type_ = check_all(media)
    file = get_extension(media)
    if not allow:
        return await message.edit_text(error)
    if type_:
        keyboard = buttons(lambda x: f"{type_}:{x}", config.TYPES_META[type_], file)
        await message.edit_text(config.strings["choice"], reply_markup=keyboard)
    else:
        await message.edit_text(config.strings["unknown"])


#
#  Когда человек решил выбрать из меню
#
# Редактирование видео
@dp.callback_query_handler(lambda c: c.data == "edit_video")
async def edit_video_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data['action'] = 'edit_video'
    message = callback_query.message
    keyboard = menu_buttons(config.VIDEO_EDIT_TYPES, main=True)
    await message.edit_text(config.strings["choice_action"], reply_markup=keyboard)
    await bs.EDIT_VIDEO.set()


@dp.callback_query_handler(state=bs.EDIT_VIDEO)
async def edit_video_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    async with state.proxy() as data:
        data['type'] = callback_query.data
        await message.edit_text(config.strings["choice_param"]["video"][data['type']],
                                reply_markup=MAIN_MENU_KEYBOARD)
        if data['type'] == "extract":
            await bs.ACTION.set()
        else:
            await bs.EDIT_VIDEO_OPTIONS.set()


@dp.message_handler(state=bs.EDIT_VIDEO_OPTIONS,
                    content_types=(types.message.ContentType.DOCUMENT,
                                   types.message.ContentType.VIDEO,
                                   types.message.ContentType.VIDEO_NOTE))
async def edit_video_option_file(media: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data["type"] == "add":
            allow, error, type_ = check_all(media, type_="video")
            if not allow:
                return await media.reply(error, reply_markup=MAIN_MENU_KEYBOARD)
            data["param"] = media
            await media.reply(config.strings["video"] + config.strings["meta"][data["type"]],
                              reply_markup=MAIN_MENU_KEYBOARD)
            await bs.ACTION.set()
        else:
            await media.reply(config.strings["choice_param"]["video"][data['type']], reply_markup=MAIN_MENU_KEYBOARD)


@dp.message_handler(state=bs.EDIT_VIDEO_OPTIONS,
                    content_types=(types.message.ContentType.VOICE,
                                   types.message.ContentType.AUDIO))
async def edit_video_option_file(media: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data["type"] == "replace":
            allow, error, type_ = check_all(media, type_="audio")
            if not allow:
                return await media.reply(error, reply_markup=MAIN_MENU_KEYBOARD)
            data["param"] = media
            await media.reply(config.strings["video"] + config.strings["meta"]["replace"],
                              reply_markup=MAIN_MENU_KEYBOARD)
            await bs.ACTION.set()
        else:
            await media.reply(config.strings["choice_param"]["video"][data['type']], reply_markup=MAIN_MENU_KEYBOARD)


@dp.message_handler(state=bs.EDIT_VIDEO_OPTIONS)  # Только текст
async def edit_video_option_text(media: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data['type'] == "speed":
            if len(media.text) > 5:
                await media.reply(config.strings["choice_param"]["video"][data['type']],
                                  reply_markup=MAIN_MENU_KEYBOARD)
            try:
                speed_ = float(media.text)
            except ValueError:
                await media.reply(config.strings["choice_param"]["video"][data['type']],
                                  reply_markup=MAIN_MENU_KEYBOARD)
            if config.MAX_SPEED >= speed_ >= config.MIN_SPEED:
                data["param"] = speed_
                await bs.ACTION.set()
                await media.reply(config.strings["video"] + config.strings["meta"][data['type']].format(data["param"]),
                                  reply_markup=MAIN_MENU_KEYBOARD)
            else:
                await media.reply(config.strings["choice_param"]["video"][data['type']],
                                  reply_markup=MAIN_MENU_KEYBOARD)
        elif data['type'] == "cut":
            temp = media.text.split(":")
            if len(temp) != 2:
                await media.reply(config.strings["choice_param"]["video"][data['type']],
                                  reply_markup=MAIN_MENU_KEYBOARD)
            try:
                time_from = float(temp[0])
                time_to = float(temp[1])
            except ValueError:
                return await media.reply(config.strings["choice_param"]["video"][data['type']],
                                         reply_markup=MAIN_MENU_KEYBOARD)
            data["param"] = [time_from, time_to]
            await bs.ACTION.set()
            await media.reply(config.strings["video"] + config.strings["meta"][data['type']].format(*data["param"]),
                              reply_markup=MAIN_MENU_KEYBOARD)
        elif data["type"] == "extract":
            await media.reply(config.strings["choice_param"]["video"][data['type']], reply_markup=MAIN_MENU_KEYBOARD)
    await bs.ACTION.set()


# редактирование аудио
@dp.callback_query_handler(lambda c: c.data == "edit_audio")
async def edit_audio_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data['action'] = 'edit_audio'
    message = callback_query.message
    keyboard = menu_buttons(config.AUDIO_EDIT_TYPES, main=True)
    await message.edit_text(config.strings["choice_action"], reply_markup=keyboard)
    await bs.EDIT_AUDIO.set()


@dp.callback_query_handler(state=bs.EDIT_AUDIO)
async def edit_video_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    message = callback_query.message
    async with state.proxy() as data:
        data['type'] = callback_query.data
        await message.edit_text(config.strings["choice_param"]["audio"][data['type']],
                                reply_markup=MAIN_MENU_KEYBOARD)
        if data['type'] == "fv":
            await bs.ACTION.set()
        else:
            await bs.EDIT_AUDIO_OPTIONS.set()


@dp.message_handler(state=bs.EDIT_AUDIO_OPTIONS,
                    content_types=(types.message.ContentType.AUDIO,
                                   types.message.ContentType.VOICE))
async def edit_audio_option_file(media: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data["type"] == "add":
            allow, error, type_ = check_all(media, type_="audio")
            if not allow:
                return await media.reply(error, reply_markup=MAIN_MENU_KEYBOARD)
            data["param"] = media
            await media.reply(config.strings["audio"] + config.strings["meta"][data["param"]],
                              reply_markup=MAIN_MENU_KEYBOARD)
            await bs.ACTION.set()
        else:
            await media.reply(config.strings["choice_param"]["audio"][data['type']], reply_markup=MAIN_MENU_KEYBOARD)


@dp.message_handler(state=bs.EDIT_AUDIO_OPTIONS)  # Только текст
async def edit_audio_option_text(media: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data['type'] == "speed":
            if len(media.text) > 5:
                return await media.reply(config.strings["choice_param"]["audio"][data['type']],
                                         reply_markup=MAIN_MENU_KEYBOARD)
            try:
                speed_ = float(media.text)
            except ValueError:
                return await media.reply(config.strings["choice_param"]["audio"][data['type']],
                                         reply_markup=MAIN_MENU_KEYBOARD)
            if config.MAX_SPEED >= speed_ >= config.MIN_SPEED:
                data["param"] = speed_
                await bs.ACTION.set()
                await media.reply(config.strings["audio"] + config.strings["meta"][data['type']].format(data["param"]),
                                  reply_markup=MAIN_MENU_KEYBOARD)
            else:
                return await media.reply(config.strings["choice_param"]["audio"][data['type']],
                                         reply_markup=MAIN_MENU_KEYBOARD)
        elif data['type'] == "cut":
            temp = media.text.split(":")
            if len(temp) != 2:
                return await media.reply(config.strings["choice_param"]["audio"][data['type']],
                                         reply_markup=MAIN_MENU_KEYBOARD)
            try:
                time_from = float(temp[0])
                time_to = float(temp[1])
            except ValueError:
                return await media.reply(config.strings["choice_param"]["audio"][data['type']],
                                         reply_markup=MAIN_MENU_KEYBOARD)
            data["param"] = [time_from, time_to]
            await bs.ACTION.set()
            await media.reply(config.strings["audio"] + config.strings["meta"][data['type']].format(*data["param"]),
                              reply_markup=MAIN_MENU_KEYBOARD)
    await bs.ACTION.set()


# Конвертирование
@dp.callback_query_handler(lambda c: c.data == "convert")
async def convert(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data['action'] = 'convert'
    message = callback_query.message
    keyboard = menu_buttons(config.TYPES)
    keyboard.add(MAIN_MENU)
    await message.edit_text(config.strings["choice_type"], reply_markup=keyboard)
    await bs.CONVERT_TYPE.set()


@dp.callback_query_handler(state=bs.CONVERT_TYPE)
async def convert_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    if callback_query.data == "photo":
        convert_type = config.PHOTO_TYPES
    elif callback_query.data == "video":
        convert_type = config.VIDEO_TYPES
    elif callback_query.data == "audio":
        convert_type = config.AUDIO_TYPES
    elif callback_query.data == "txt":
        convert_type = config.TXT_TYPES
    elif callback_query.data == "exel":
        convert_type = config.EXEL_TYPES
    else:
        await callback_query.message.reply(config.strings["wtf_bro"].format(callback_query))
        logger.debug(callback_query)
        return
    async with state.proxy() as data:
        data['type'] = callback_query.data
    message = callback_query.message
    keyboard = buttons(lambda x: f"{x}", convert_type)
    keyboard.add(MAIN_MENU)
    await message.edit_text(config.strings["choice"],
                            reply_markup=keyboard)
    await bs.CONVERT_FORMAT.set()


@dp.callback_query_handler(state=bs.CONVERT_FORMAT)
async def convert_format(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data['format'] = callback_query.data
        await callback_query.message.edit_text(config.strings["action"].format(data["type"], data["format"]))
    await bs.ACTION.set()


@dp.message_handler(state=bs.ACTION, content_types=(types.message.ContentType.DOCUMENT,
                                                    types.message.ContentType.VIDEO,
                                                    types.message.ContentType.PHOTO,
                                                    types.message.ContentType.AUDIO,
                                                    types.message.ContentType.VOICE,
                                                    types.message.ContentType.STICKER,
                                                    types.message.ContentType.VIDEO_NOTE,
                                                    types.message.ContentType.ANIMATION))
async def action(media: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data["action"] == "convert":
            allow, error, type_ = check_all(media, type_=data["type"])
            logger.debug([allow, error, type_])
            if not allow:
                return await media.reply(error, reply_markup=MAIN_MENU_KEYBOARD)
            if data["type"] == "photo":
                message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
                task_queue.put(PhotoTask(
                    message, media, data["format"]
                ))
            elif data["type"] == "video":
                message = await media.reply(config.strings["queue"].format(big_task_queue.qsize() + 1))
                task_queue.put(VideoTask(
                    message, media, data["format"]
                ))
            elif data["type"] == "audio":
                message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
                task_queue.put(AudioTask(
                    message, media, data["format"]
                ))
            elif data["type"] == "txt":
                message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
                task_queue.put(TextTask(
                    message, media, data["format"]
                ))
            elif data["type"] == "exel":
                message = await media.reply(config.strings["queue"].format(task_queue.qsize() + 1))
                task_queue.put(ExelTask(
                    message, media, data["format"]
                ))
        elif data["action"] == "edit_video":
            message = await media.reply(config.strings["queue"].format(big_task_queue.qsize() + 1))
            if data["type"] == "speed":
                big_task_queue.put(
                    VideoSpeedTask(message, media, data["param"])
                )
            elif data["type"] == "add":
                big_task_queue.put(
                    VideoAddTask(message, data["param"], media)
                )
            if data["type"] == "cut":  # cut
                big_task_queue.put(
                    VideoCutTask(message, media, data["param"][0], data["param"][1])
                )
            if data["type"] == "extract":
                big_task_queue.put(
                    VideoExtractTask(message, media)
                )
            if data["type"] == "replace":
                big_task_queue.put(
                    VideoReplaceTask(message, media, data["param"])
                )
        elif data["action"] == "edit_audio":
            message = await media.reply(config.strings["queue"].format(big_task_queue.qsize() + 1))
            if data["type"] == "speed":
                big_task_queue.put(
                    AudioSpeedTask(message, media, data["param"])
                )
            elif data["type"] == "add":
                big_task_queue.put(
                    AudioAddTask(message, data["param"], media)
                )
            if data["type"] == "cut":
                big_task_queue.put(
                    AudioCutTask(message, media, data["param"][0], data["param"][1])
                )
            if data["type"] == "fv":
                big_task_queue.put(
                    AudioFvTask(message, media)
                )
        else:
            await media.reply(config.strings["wtf_bro"].format(str(media) + str(data)))
            logger.debug(str(media) + str(data))
            return
    await state.reset_state()
    await media.reply("Задача выполняется.", reply_markup=MAIN_MENU_KEYBOARD)


@dp.message_handler(state="*", content_types=types.message.ContentType.ANY)
async def wtf(message: types.Message):
    if message.text:
        await message.reply(config.strings["wtf_text"], reply_markup=MAIN_MENU_KEYBOARD_FROM_MESSAGE)
    else:
        await message.reply(config.strings["wtf"], reply_markup=MAIN_MENU_KEYBOARD)


if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    print("Создание потоков")
    for _ in range(config.MAX_THREAD):  # запуск всех обработчиков задачь в фоне
        run_handler(task_queue, bot, main_loop)
    for _ in range(config.MAX_THREAD_BIG):  # отдельно для больших файлов
        run_handler(big_task_queue, bot, main_loop)
    # thread = threading.Thread(target=delete_files)
    # thread.daemon = True  # Демонизирование потока, запуск его в фоне
    # thread.start()  # Запуск потока
    asyncio.run(executor.start_polling(dp, skip_updates=True))
