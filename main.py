import requests
import datetime
import json


def find_duplicates(lst):
    indices = {}
    for index, number in enumerate(lst):
        if number in indices:
            first_occurrence_index = indices[number]
            return first_occurrence_index, index
        else:
            indices[number] = index
    return False


def get_vk_photos(user_id, access_token):
    params_vk = {
        'access_token': access_token,
        'v': '5.199',
        'user_id': user_id,
        'album_id': 'profile',
        'extended': 1
    }
    likes = []
    urls = []
    dates = []
    response_vk = requests.get('https://api.vk.com/method/photos.get', params=params_vk)
    try:
        total = response_vk.json()['response']['items']
    except:
        return response_vk.json()
    for i in total:
        likes.append(str(i['likes']['count']))
        dates.append(datetime.datetime.fromtimestamp(i['date']).strftime("%d.%m.%Y"))
        urls.append(max(i['sizes'], key=lambda x: x['height'] + x['width']))
    if find_duplicates(likes):
        for i in find_duplicates(likes):
            likes[i] += f' {dates[i]}'
    return dict(zip(likes, urls))


def check_vk_errors(func):
    if list(func.keys())[0] != 'error':
        return True, func
    else:
        return False, f'Error - error_msg: {func["error"]["error_msg"]}, error_code: {func["error"]["error_code"]}'


def upload_to_yandex_disk(photos, yandex_token):
    upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {
        'Authorization': f'OAuth {yandex_token}'
    }
    responses = []
    check = None
    requests.put(folder_url, headers=headers, params={'path': 'vk_photos'})
    for i in list(photos.keys()):
        response_upload = requests.post(upload_url, headers=headers,
                                        params={'path': f'vk_photos/{i}', 'url': photos[i]['url']})
        if response_upload.status_code == 202:
            responses.append({'file_name': f'{i}.jpg', 'size': photos[i]['type']})
            check = True
        else:
            responses.append({'error': f'status_code: {response_upload.status_code}'})
            check = False

    return check, responses


def get_logs(responses):
    with open('data.json', 'w') as file:
        json.dump(responses[1], file, indent=4)


def main(vk_token):
    yandex_token = input('Yandex token:')
    user_id = input('User id:')

    print('Получена инфомация!')
    print('Получение ответа с сервера vk...')

    photos_info = get_vk_photos(user_id, vk_token)

    check_errors = check_vk_errors(photos_info)

    if check_errors[0]:
        print('Успешный ответ!')
    else:
        print(f'Ошибка: {check_errors[1]}')
        return

    print('Загрузка фотографий на яндекс диск...')

    logs = upload_to_yandex_disk(photos_info, yandex_token)

    if logs[0]:
        print('Успешно загружено, проверяйте!')
    else:
        print('Ошибка')

    print('Запись логов в файл...')

    get_logs(logs)

    print('Готово!')


# нужно передать токен от вк
if __name__ == '__main__':
    main('vk_token')
