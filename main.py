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


def find_max_photo(photos):
    def get_type_order(photo):
        type_sequence = {'s': 1, 'm': 2, 'x': 3, 'o': 4, 'p': 5, 'q': 6, 'r': 7, 'y': 8, 'z': 9, 'w': 10}
        return type_sequence.get(photo.get('type'), 0)

    max_photo = sorted(photos, key=get_type_order)

    return max_photo[-1]


def get_count_photos(user_id, access_token, album):
    params_vk = {
        'access_token': access_token,
        'v': '5.199',
        'user_id': user_id,
        'album_id': album,
        'extended': 1
    }
    response_vk = requests.get('https://api.vk.com/method/photos.get', params=params_vk)
    count = response_vk.json()['response']['count']
    return count


def get_vk_photos(user_id, access_token, count, album):
    params_vk = {
        'access_token': access_token,
        'v': '5.199',
        'user_id': user_id,
        'album_id': album,
        'extended': 1,
        'count': count
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
        urls.append(find_max_photo(i['sizes']))
    if find_duplicates(likes):
        for i in find_duplicates(likes):
            likes[i] += f' {dates[i]}'
    return dict(zip(likes, urls))


def check_vk_errors(func):
    if list(func.keys())[0] != 'error':
        return True, func
    else:
        return False, f'Error - error_msg: {func["error"]["error_msg"]}, error_code: {func["error"]["error_code"]}'


def upload_to_yandex_disk(photos, yandex_token, folder_name):
    upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {
        'Authorization': f'OAuth {yandex_token}'
    }
    responses = []
    check = None
    response_check = requests.get(folder_url, headers=headers, params={'path': folder_name})
    if response_check.status_code == 404:
        requests.put(folder_url, headers=headers, params={'path': folder_name})
    for i in list(photos.keys()):
        response_upload = requests.post(upload_url, headers=headers,
                                        params={'path': f'{folder_name}/{i}', 'url': photos[i]['url']})
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


def main():
    vk_token = 'vk_token'
    yandex_token = input('Yandex token:')
    user_id = input('User id:')

    print('Получена инфомация!')

    album_total = int(
        input('Выберите альбом из которого будут выгружаться:\n1 - Фотографии со стены\n2 - Фотографии из профиля\n'))

    if album_total == 1:
        album_id = 'wall'
    elif album_total == 2:
        album_id = 'profile'
    else:
        print(f'Неправильное значение альбома, либо 1 либо 2. Вы указали {album_total}')
        return

    number_of_photos = get_count_photos(user_id, vk_token, album_id)

    if number_of_photos <= 0:
        print('0 фотографий в этом альбоме, выберите другой')
        return

    count = int(input(f'К выгрузке готово {number_of_photos} фотографий, сколько фотографий выгрузить?\n'))

    if count < 1:
        print('Количество фотографий меньше 1, попробуйте еще раз')
        return
    elif count > number_of_photos:
        print('Количество фотографий больше возможного, попробуйте еще раз')
        return

    print('Получение ответа с сервера vk...')

    photos_info = get_vk_photos(user_id, vk_token, count, album_id)

    check_errors = check_vk_errors(photos_info)

    if check_errors[0]:
        print('Успешный ответ!')
    else:
        print(f'Ошибка: {check_errors[1]}')
        return

    print('Загрузка фотографий на яндекс диск...')

    folder = input('Введите название папки в которую будут загружены фотографии:\n')

    print('Загружаем!')

    logs = upload_to_yandex_disk(photos_info, yandex_token, folder)

    if logs[0]:
        print('Успешно загружено, проверяйте!')
    else:
        print('Ошибка')

    print('Запись логов в файл...')

    get_logs(logs)

    print('Готово!')


if __name__ == '__main__':
    main()
