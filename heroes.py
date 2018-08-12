from time import sleep

import requests

import config
from process import write_json_data


def get_heroes(language):
    base = 'http://api.steampowered.com/IEconDOTA2_570/GetHeroes/v1'
    payload = {'key': config.STEAM_API_KEY, 'language': language}
    response = requests.get(base, params=payload)
    return response


def fetch_heroes(filename, language):
    for attempt in range(5):
        response = get_heroes(language)
        status_code = response.status_code
        if status_code == 200:
            decoded = response.json()
            result = decoded['result']
            heroes = result['heroes']
            count = result['count']
            hero_data = {'heroes': heroes, 'count': count}
            write_json_data(filename, hero_data)
            print('Hero data saved to {} successfully.'.format(filename))
            break
        else:
            print('HTTP status code: {}. Waiting to retry...'.format(status_code))
            sleep(30)
    else:
        raise requests.exceptions.RetryError('fetch_heroes exceeded maximum number of attempts.')


if __name__ == '__main__':
    fetch_heroes(config.HERO_DATA_FILE, config.LANGUAGE)
