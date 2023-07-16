<h1 align="center">
  PIK парсер недвижимости.
</h1>


<h4 align="center">Оглавление README:</h4>
<div align="center">
    <a href="#про-скрипт"> • Для чего нужен этот скрипт • </a><br>
    <a href="#установка"> • Установка • </a><br>
    <a href="#внутрянка"> • Что внутри • </a><br>
    <a href="#файл-settingsjson"> • Что такое файл settings.json • </a><br>
    <a href="#файл-settings_paramsjson"> • Что такое файл settings_params.json • </a><br>
    <a href="#примечание"> • Примечание • </a>
</div>


## Про скрипт
Есть такой популярный застройщик недвижимости как ПИК (https://www.pik.ru/).

Хочется получать уведомления о новых доступных вариантах которые попадают под поиск по заданным параметрам, так же изменение цен на варианты которые попадают под поиск - какие квартиры выкупаются, какие квартиры изменяют цены и так далее.

Именно для этого и создавался этот скрипт.


## Установка
1. Скачиваете ветку;
2. Устанавливаете python 3.9;
3. Создаете виртуальное окружение `python3.9 -m venv env`
4. Активируете виртуальное окружение и устанавливаете зависимости `pip install -r requirements.txt`
5. Редактируете файл `settings.json` под себя;
6. Закидываем параметры для поиска в файл `settings_params.json`;
7. Запускаете `parse.py` и наслаждаетесь результатом.


## Внутрянка
1. Данные для настройки указываются в конфиг файле `settings.json` *(шаблон заполнен тестовыми данными и называется sample_settings.json)*;
2. Данные с параметрами для поиска указываются в формате json, в файле `settings_params.json` *(шаблон заполнен тестовыми данными и называется sample_params.json)*;
2. Автоматизированная программа(скрипт) забирает все квартиры по адресу, преобразует в список [`get_all_flats` функция];
3. Этот список закидывается в файлы внутрь папки `queue` [`save_data_flats_queue` функция];
4. Затем происходит обработка всех данных путем сравнения полученных квартир из пункта 2 и сохраненными раннее данными в папку `data` [`process_flats`];
5. В ходе процессинга в пункте 5 происходит отправка уведомлений в телеграм путем post запроса на собственный микросервис по отправке сообщений (при условии что флаг `send_telegram_message` внутри настроеек имеет значение True);
6. После процессинга засыпаем на время указанное в `settings.json`, значение следующего запроса записываем в системный файл `settings_system.json`.


## Файл settings.json
Файл settings.json имеет формат json, с следующими ключами:

* "host": [str] адрес микросервиса для отправки сообщений в телегу,

* "sender": [str|int] кому отправлять сообщение в телеге, если указана str то будет ресолвить username, если указан int то будет считать что это userid(можно указывать ид канала),

* "await_time": [int] количество секунд перед, следующим циклом запросов,

* "send_telegram_message": [bool] использовать ли уведомление в телеграм или обойдемся обычными принтами.

*Если возникают какие-то сложности с файлом `settings.json` то можно переименовать файл с базовыми настройками `sample_settings.json` в `settings.json`, скрипт будет работать корректно*.


## Файл settings_params.json
Файл settings_params.json имеет формат json, с следующими ключами для поиска необходимых вариантов квартир на сайте.

Получить этот список можно зайдя най сайт <a href="https://pik.ru">pik.ru</a>, открыв консоль разработчика Ctrl+F12, выбрав необходимые параметры.

![Находим вкладку payload](/images/params1.png)

Находим вкладку payload

![Находим параметры для поиска](/images/params2.png)

Находим параметры для поиска

![Преобразуем параметры поиска в json в файл](/images/params3.png)

Преобразуем параметры поиска в json и складываем в файл `settings_params.json`.

*Если возникают какие-то сложности с файлом `settings_params.json` то можно переименовать файл с базовыми настройками `sample_params.json` в `settings_params.json`, скрипт будет работать корректно*.


## Примечание
По работе с виртуальными окружениями можно почитать <a href="https://docs.python.org/3/library/venv.html#how-venvs-work"> docs.python.org</a>