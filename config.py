API_TOKEN = "YOU TOKEN"
DATA_ROOT = "bot_api\\{}".format(API_TOKEN.replace(":", "~"))
AUTO_DELETE_TIME = 1  # часов
API_URL = "http://127.0.0.1:8081"  # http://127.0.0.1:8081 | https://api.telegram.org/
MAX_THREAD = 4
MAX_THREAD_BIG = 4
MIN_SPEED = 0.25
MAX_SPEED = 4.0
MAX_FILE_SIZE_PHOTO = 100 * 1024 * 1024  # В байтах /// 10МБ
MAX_FILE_SIZE_VIDEO = 100 * 1024 * 1024  # В байтах /// 10МБ
MAX_FILE_SIZE_AUDIO = 100 * 1024 * 1024  # В байтах /// 10МБ
MAX_FILE_SIZE_TXT = 100 * 1024 * 1024  # В байтах /// 4МБ
MAX_FILE_SIZE_EXEL = 100 * 1024 * 1024  # В байтах /// 4МБ
ADMIN_IDS = [367426419]  # int

strings = {
    "start": "some text",
    "help": "Поддерживаемые форматы:\n{}",
    "main_menu": "Вернуться в главное меню",
    "wtf": "Не понимаю о чем вы, может в главное меню?",
    "wtf_text": "Хотите конвертировать ваше сообщение в текст?",
    "from_message": "Превратить в текст",

    # get params
    "choice": "Выберите формат для конвертации:",
    "choice_action": "Выберите какое действие хотите сделать:",
    "choice_type": "Выберите вид ваших файлов:",
    "choice_param": {
        "video": {
            "add": "Отправьте первое видео к котору добавить следующее (в конец), желательно в формате MP4",
            "cut": "Отправьте в секундах откуда и до куда вырезать видео. Пример 12:15 (с 12 до 15 секунды), "
                   "0 начало, 99999 до самого конца",
            "speed": f"Отправьте коэфициент изменения скорости, от {MIN_SPEED} до {MAX_SPEED}",
            "extract": "Отправьте видео из которого отделить звук",
            "replace": "Отправьте аудио которое хотите вставить в видое"
        },
        "audio": {
            "add": "Отправьте первое аудио к котору добавить следующее (в конец), желательно в формате MP3",
            "cut": "Отправьте в секундах откуда и до куда вырезать аудио. Пример 12:15 (с 12 до 15 секунды), "
                   "0 начало, 99999 до самого конца",
            "speed": f"Отправьте коэфициент изменения скорости, от {MIN_SPEED} до {MAX_SPEED}",
            "fv": "Отправьте аудио которое хотите испортить"
        }
    },
    "action": "Хорошо, можете начать отправлять файлы типа {}\n"
              "Они будут сконвертированы в формат {}",
    "video": "Хорошо, можете отправить видео, желательно mp4\nОно будет",
    "audio": "Хорошо, можете отправить аудио, желательно mp3\nОно будет",
    "meta": {
        "add": "склеино с первым",
        "cut": "обрезано с {} до {}",
        "speed": "изменено в скорости, с коэфициентом {}",
        "fv": "сшакалено",
        "replace": "замена аудио дорожка"
    },

    # input xxx output
    "analyzing": "Немного подождите, анализирую файл",
    "queue": "Хорошо, ожидайте выполнения. Ваше место в очереди {}",
    "working": "\nНачинаю работу",
    "exporting": "\nЭкспортирую",
    "uploading": "\nЗагружаю в телеграм",
    "converted": "Успешно сконвертировано из {} в {}",
    "edited": "Файл успешно отредактирован:\n",

    "convert": "Конвертирование из {} в {}",
    "speed": "Изменение скорости на {}",
    "cut": "Обрезка с {} до {}",
    "fv": "Уничтожение звука",
    "extract": "Вырезка звука из видео",
    "replace": "Замена звука в видео",
    "add": "Склека двух медия в одно",

    # errors
    "too_long_text": "Текст файла слишком большой, отправил начало",
    "not_supported": "Конвертация в {} не удалась из-за неизвестной ошибки",
    "not_supported_video": "Изменить видео не удалось из-за не поддерживаемого формата, рекомендуюмый формат: MP4",
    "not_supported_audio": "Изменить видео не удалось из-за не поддерживаемого формата, рекомендуюмый формат: MP3",
    "too_big": "Файл слишком большой! Максимальный размер файла: {} мегабайт",  # tasks.py:L41 что бы поменять
    "bad_extension": "Этот файл не подходит! Отправьте файл формата {}",
    "unknown": "Этот файл не подходит! Напишите /help что бы получить полный список",
    "wtf_bro": "Произошла очень странная ошибка в работе бота! Включите режим дебага, вот доп инфа\n {}",

    # admin
    "admin_menu": "Пользователей: {}\nАдминистаторов: {}\nВ быстрой очереди: {}\n В медленной очереди: {}",
    "admin_no_reply": "Сделайте реплай что бы разослать это сообщение всем",
    "admin_mail_start": "Началась рассылка",
    "admin_mail_end": "Отправлено {} пользователям",

    # static
    "to_file": "Текстовый_файл.txt",
    "animation": "gif",
    "voice": "голосовое_сообщение",
    "photo": "фотография",
    "sticker": "стикер",
    "video_note": "видео_заметка",
    "undefined": "не_указан",

}
# Меню админа | не сделано
ADMIN_MENU = {
    "Переслать всем": "forward_all",
    "Разослать всем": "copy_to_all",
    "Список администаторов": "admin_list",
    "Добавить админов": "add_admin_"  # _ означает что доступно только главным админам
}

# Форматы и прочая информация
WD_ENUM = {  # https://docs.microsoft.com/en-us/office/vba/api/word.wdsaveformat
    "PDF": 17,
    "DOC": 0,
    "TXT": 5,
    "DOCX": 16
}
VIDEO_TYPES = {
    'MP4': 'MP4',
    'AVI': 'AVI',
    '3GP': '3GP',
    'MOV': 'MOV',
    'TS': 'TS',
    'M4V': 'M4V',
    'WEBM': 'WEBM',
    'FLV': 'FLV',
    'Отправить в кругляшке': 'VIDEO_NOTE_'  # _ означает что в списке форматов не будет отображаться
}
PHOTO_TYPES = {
    'PNG': 'PNG',
    'JPEG': 'JPEG',
    'WEBP': 'WEBP',
    'BMP': 'BMP',
    'TIFF': 'TIFF',
    'GIF': 'GIF',
    'ICO': 'ICO',
    'Отправить фото': 'PHOTO_'
}
AUDIO_TYPES = {
    'OGG': 'OGG',
    'MP3': 'MP3',
    'WAV': 'WAV',
    'OGA': 'OGA',
    'OPUS': 'OPUS',
    'FLAC': 'FLAC',
    'M4A': 'M4A',
    'AAC': 'AAC',
    'Отправить голосовое': 'VOICE_',
}
TXT_TYPES = {
    'PDF': 'PDF',  # PDF что выше в списке будет первым обработан, то есть как текст, а не таблица
    'DOC': 'DOC',
    'TXT': 'TXT',
    'DOCX': 'DOCX',
    'Отправить как текст': 'AS_TEXT_'
}
EXEL_TYPES = {
    'XLSX': 'XLSX',
    'XLS': 'XLS',
    'CSV': 'CSV',
}
TYPES = {
    "Фотографии": "photo",
    "Видео": "video",
    "Аудио": "audio",
    "Текстовые файлы": "txt",
    "Таблицы": "exel"
}

MENU_KEYBOARD = {
    "Конвертировать": "convert",
    "Редактировать видео": "edit_video",
    "Редактировать аудио": "edit_audio"
}

VIDEO_EDIT_TYPES = {
    "Изменить скорость": "speed",
    "Склеить с другим видео": "add",
    "Обрезать видео": "cut",
    "Извлечь звуковую дорожку": "extract",
    "Заменить аудио": "replace",
}

AUDIO_EDIT_TYPES = {
    "Изменить скорость": "speed",
    "Склеить два аудио файла": "add",
    "Обрезать аудио": "cut"
    # "Испортить звук":
}

ALIASES = {  # у некоторых форматор есть несколько имён
    'JPG': 'JPEG',  # http://gearmobile.github.io/mix/jpeg-jpg-difference/
    'TIF': 'TIFF'   # https://blog.media.io/image-converter/open-tiff-tif.html
}

NOT_ALLOWED = {  # убирается из списка
    "ONLY_ENTER": [],  # в которые нельзя конвертировать никак, но можно из
    "VOICE_": ["M4A", "AAC"]  # из гс невозможно сдлетать эти 2 формата
}

# META DO NOT CHANGE
TYPES_META = {
    "photo": PHOTO_TYPES,
    "video": VIDEO_TYPES,
    "txt": TXT_TYPES,
    "audio": AUDIO_TYPES,
    "exel": EXEL_TYPES
}

SIZE_META = {
    "photo": MAX_FILE_SIZE_PHOTO,
    "video": MAX_FILE_SIZE_VIDEO,
    "txt": MAX_FILE_SIZE_TXT,
    "audio": MAX_FILE_SIZE_AUDIO,
    "exel": MAX_FILE_SIZE_TXT
}
