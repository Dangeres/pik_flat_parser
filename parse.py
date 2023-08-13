import requests
import datetime
import time
import os
import re
import math
import hashlib
import random

from jsona import Jsona


BASE_URL = 'https://www.pik.ru/flat/'

jsona_settings = Jsona('', 'settings.json')
jsona_system = Jsona('', 'settings_system.json')
jsona_params = Jsona('', 'settings_params.json')

settings = jsona_settings.return_json().get('data', {})
settings_system = jsona_system.return_json().get('data', {'time': int(time.time())})
settings_params = jsona_params.return_json().get('data', {})


FOLDER_DATA = 'data/'
FOLDER_QUEUE = 'queue/'
FOLDER_ERRORS = 'errors/'


for path in [
    FOLDER_DATA,
    FOLDER_QUEUE,
    FOLDER_ERRORS,
]:
    os.makedirs(path, exist_ok = True)


def price_format(value):
    str_value = str(value)

    regex = r'\d{3}(?!$)'
    subst = '\g<0>.'

    return re.sub(regex, subst, str_value[::-1], 0, re.MULTILINE)[::-1]


def get_all_flats():
    result = []
    page = 1
    size = settings_params.get('flatLimit', 20)
    all_count = size

    try:
        while page <= math.ceil(all_count // size):
            settings_params['flatPage'] = page

            while True:
                try:
                    req = requests.get(
                        url='https://api-selectel.pik-service.ru/v2/filter',
                        params=settings_params,
                    )

                    response = req.json()

                    all_count = response.get('count', size)

                    flats = response.get('flats', [])

                    if not response.get('flats') and response.get('blocks'):
                        flats = response.get('blocks', [])[0].get('flats', [])

                    break
                except Exception as e:
                    time.sleep(random.uniform(1, 4))
                    print(e)

            for flat in flats:
                url = ''.join(
                    [
                        BASE_URL,
                        str(flat.get('id')),
                    ]
                )

                data = {
                    'uid': hashlib.sha256(url.encode()).hexdigest(),
                    'link': url,
                    'name': flat.get('address') + '\n' + flat.get('number'),
                    'size': size,
                    'floor': flat.get('floor'),
                    'price': flat.get('price') if flat.get('status') == 'free' else -1,
                    'time': int(time.time()),
                }

                result.append(
                    data
                )

            page += 1

            time.sleep(random.uniform(0.1, 0.7))
    except Exception as e:
        print(e)

    return result


def save_data_flats_queue(flats):
    try:
        for data in flats:
            jsona = Jsona(
                path_file=FOLDER_QUEUE,
                name_file=f'{data["uid"]}.json'
            )

            jsona.save_json(
                data = data,
            )
    except Exception as e:
        print(e)


def send_telegram(uid, message):
    try:
        result = requests.post(
            url = settings.get('host') + '/message',
            json = {
                'id': uid,
                'sender': settings.get('sender'),
                'text': message,
            },
            headers = {
                'token': settings.get('token'),
            }
        )

        print(message)

        return result.status_code == 200 and result.json().get('success')
    except Exception as e:
        print(e)

    return False


def just_print(message):
    print(message)

    return True


def process_flats():
    for file in os.listdir(FOLDER_DATA):
        if not file.endswith('.json'):
            continue
        
        jsona_queue = Jsona(path_file=FOLDER_QUEUE, name_file=file).return_json()
        jsona_data = Jsona(path_file=FOLDER_DATA, name_file=file).return_json()

        if jsona_queue.get('success'):
            data_file = jsona_data.get('data')
            queue_file = jsona_queue.get('data')

            last_price = data_file['last_price']

            if last_price == queue_file.get('price'):
                continue

            data_file['last_price'] = queue_file.get('price')

            data_file['prices'].append(
                {
                    'price': queue_file.get('price'),
                    'time': queue_file.get('time'),
                }
            )

            while True:
                if last_price == -1:
                    prev_last_price = price_format(data_file['prices'][-3]['price']) if len(data_file['prices']) > 2 else 'Неизвестно'

                    message_html = '<a href="%s">%s</a> пропадала с продажи но вернулась.\nЦена до продажи %s\nТекущая цена %s\n\n<i>uid: %s</i>' % (
                        data_file['link'],
                        data_file['name'],
                        prev_last_price,
                        price_format(queue_file.get('price')),
                        queue_file.get('uid'),
                    )

                    message_raw = '%s %s пропадала с продажи но вернулась.\nЦена до продажи %s\nТекущая цена %s\n\nuid: %s' % (
                        data_file['name'],
                        data_file['link'],
                        prev_last_price,
                        price_format(queue_file.get('price')),
                        queue_file.get('uid'),
                    )
                
                else:
                    message_html = '<a href="%s">%s</a> изменила цену.\nС %s на %s\n\n<i>uid: %s</i>' % (
                        data_file['link'],
                        data_file['name'],
                        price_format(last_price),
                        price_format(queue_file.get('price')),
                        queue_file.get('uid'),
                    )

                    message_raw = 'Изменение цены %s %s\nС %s на %s\n\nuid: %s' % (
                        data_file['name'],
                        data_file['link'],
                        price_format(last_price),
                        price_format(queue_file.get('price')),
                        queue_file.get('uid'),
                    )

                result = send_telegram(
                    uid = queue_file.get('uid'),
                    message = message_html,
                ) if settings.get('send_telegram_message') else just_print(
                    message = message_raw,
                )

                if result:
                    Jsona(path_file=FOLDER_DATA, name_file=file).save_json(data = data_file)
                    os.remove(FOLDER_QUEUE + file)

                    break
                else:
                    time.sleep(random.uniform(1, 2))
        
        else:
            data_file = jsona_data.get('data')

            last_price = data_file['last_price']

            if last_price == -1:
                continue

            data_file['last_price'] = -1

            data_file['prices'].append(
                {
                    'price': -1,
                    'time': int(time.time()),
                }
            )

            while True:
                message_html = '<a href="%s">%s</a> была продана.\nПоследняя цена %s\n\n<i>uid: %s</i>' % (
                    data_file['link'],
                    data_file['name'],
                    price_format(last_price),
                    data_file.get('uid'),
                )

                message_raw = 'Продажа %s %s\nПоследняя цена %s\n\nuid: %s' % (
                    data_file['name'],
                    data_file['link'],
                    price_format(last_price),
                    data_file.get('uid'),
                )

                result = send_telegram(
                    uid = data_file.get('uid'),
                    message = message_html,
                ) if settings.get('send_telegram_message') else just_print(
                    message = message_raw,
                )
                
                if result:
                    Jsona(path_file=FOLDER_DATA, name_file=file).save_json(data = data_file)
                    break
                else:
                    time.sleep(random.uniform(1, 2))

    for file in os.listdir(FOLDER_QUEUE):
        if not file.endswith('.json'):
            continue

        jsona_queue = Jsona(path_file=FOLDER_QUEUE, name_file=file).return_json()
        jsona_data = Jsona(path_file=FOLDER_DATA, name_file=file).return_json()

        if jsona_data.get('success'):
            os.remove(FOLDER_QUEUE + file)
            continue

        queue_file = jsona_queue.get('data')
        
        data_file = {
            'uid': queue_file.get('uid'),
            'name': queue_file.get('name'),
            'link': queue_file.get('link'),
            'last_price': queue_file.get('price'),
            'size': queue_file.get('size'),
            'floor': queue_file.get('floor'),
            'prices': [
                {
                    'price': queue_file.get('price'),
                    'time': queue_file.get('time'),
                }
            ],
        }

        while True:
            message_html = '<a href="%s">%s</a>\nЦена новопоявившейся квартиры %s\n\n<i>uid: %s</i>' % (
                data_file['link'],
                data_file['name'],
                price_format(data_file['last_price']),
                queue_file.get('uid'),
            )

            message_raw = 'Появилась %s %s\nЦена %s\n\nuid: %s' % (
                data_file['name'],
                data_file['link'],
                price_format(data_file['last_price']),
                queue_file.get('uid'),
            )

            result = send_telegram(
                uid = queue_file.get('uid'),
                message = message_html,
            ) if settings.get('send_telegram_message') else just_print(
                message = message_raw,
            )
            
            if result:
                Jsona(path_file=FOLDER_DATA, name_file=file).save_json(data = data_file)
                os.remove(FOLDER_QUEUE + file)

                break
            else:
                time.sleep(random.uniform(1, 2))


def tick():
    print('Начинаем получать квартиры....')

    flats = get_all_flats()

    print('Квартиры были получены')
    
    save_data_flats_queue(flats)
    
    print('Квартиры были обработаны')

    process_flats()


def main():
    while not settings.get('use_cron', False):
        now_time = int(time.time())

        sleep_time = max(settings_system['time'] - now_time, 0)

        print(f'Спим {sleep_time} секунд.\nВремя: {datetime.datetime.fromtimestamp(settings_system["time"]).strftime("%d.%m.%y %H:%M:%S")}')

        time.sleep(sleep_time)

        tick()

        settings_system['time'] = int(time.time()) + settings['await_time']

        jsona_system.save_json(data = settings_system, ident=4)

    if settings.get('use_cron', False):
        tick()


if __name__ == '__main__':
    main()