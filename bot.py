import os
import json
import random

import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import requests
from dotenv import load_dotenv


class Bot:
    dotenv_path = '.env'
    settings_path = 'settings.cfg'
    keyboard_path = 'keyboard.json'
    base = 'https://api.vk.com/method/'

    def __init__(self):
        if os.path.exists(self.dotenv_path):
            load_dotenv(self.dotenv_path)
        self.key = None
        self.server = None
        self.ts = None
        self.params = {'group_id': os.environ.get("GROUP_ID"),
                       'access_token': os.environ.get("GROUP_TOKEN"),
                       'v': '5.131'}
        vk_session = vk_api.VkApi(token=os.environ.get("GROUP_TOKEN"))
        self.vk = vk_session.get_api()

    def get_server(self):
        """
        Getting session data (required when first addressing to long poll)
        :return: "session data successfully received" OR error message
        """
        method = 'groups.getLongPollServer'
        response = requests.get(self.base + method, params=self.params)
        try:
            self.key = response.json()['response']['key']
            self.server = response.json()['response']['server']
            self.ts = response.json()['response']['ts']
            return "session data successfully received"
        except KeyError:
            return f'{response.json().get("error", {}).get("error_msg", "unknown error")}'

    def get_settings(self):
        """
        Saving settings of which events to operate with to a file --> "self.settings_path"
        In case of an error, the error message is saved to the file.
        :return: None
        """
        method = 'groups.getLongPollSettings'
        with open(self.settings_path, 'wt', encoding='UTF-8') as settings_file:
            response = requests.get(self.base + method, params=self.params)
            settings = response.json().get('response', {}).get('events', 'could not receive settings')
            json.dump(settings, fp=settings_file, indent=4)

    def set_settings(self):
        """
        Commit new settings from file located at "self.settings_path"
        :return: 'settings successfully changed' OR error message
        """
        method = 'groups.setLongPollSettings'
        with open(self.settings_path, 'rt', encoding='UTF-8') as settings_file:
            settings = json.load(settings_file)
            params = {**self.params, **settings}
        response = requests.get(self.base + method, params=params)
        if response.json().get('response') == 1:
            return 'settings successfully changed'
        else:
            return response.json().get('error', {}).get('error_msg', 'unknown error')

    def listen(self):
        url = f'{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait=25'
        response = requests.get(url, params=self.params)
        self.ts = response.json().get('ts')
        if response.json().get('updates'):
            return (
                response.json()['updates'][0]['object']['message']['from_id'],
                response.json()['updates'][0]['object']['message']['text']
            )
        else:
            return None

    def suggest(self, recipient, name, link, photos):
        message = f'Я нашел для тебя отличный вариант для знакомства!\n\n' \
                  f'{name}\n' \
                  f'{link}\n\n'
        attachment = ','.join(photos)
        random_id = random.randint(-2147483648, 2147483647)
        # with open(self.keyboard_path, 'rt', encoding='UTF-8') as filehandle:
        #     keyboard = json.load(fp=filehandle)
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('предложить еще', color=VkKeyboardColor.PRIMARY)

        self.vk.messages.send(user_id=recipient,
                              message=message,
                              attachment=attachment,
                              random_id=random_id,
                              keyboard=keyboard.get_keyboard())

    def get_users_details(self, user):
        method = 'users.get'
        data = {'user_ids': f"{user}", 'fields': 'city, sex, bdate, interests'}
        params = {**self.params, **data}
        response = requests.get(self.base + method, params=params)
        return response.json()['response'][0]


class Searcher(Bot):
    scripts_path = 'vk_scripts/'

    def __init__(self):
        if os.path.exists(self.dotenv_path):
            load_dotenv(self.dotenv_path)

        access_token = os.environ.get("USER_TOKEN")
        vk_session = vk_api.VkApi(token=access_token)
        self.vk = vk_session.get_api()

    def search_users(self, criteria):
        with open(self.scripts_path + 'users.search') as f:
            code = f.read().replace('<city>', str(criteria['city']))\
                           .replace('<sex>', str(criteria['sex']))\
                           .replace('<age_from>', str(criteria['age_from']))\
                           .replace('<age_to>', str(criteria['age_to']))
        response = self.vk.execute(code=code)
        return response[0]['items'] if response else response

    def get_albums(self, user_id):
        try:
            response = self.vk.photos.getAlbums(owner_id=user_id, need_system=1)
            return [album['id'] for album in response['items']]
        except vk_api.exceptions.ApiError:
            return []

    def get_photos(self, user_id, albums):
        result = []
        for album in albums:
            try:
                response = self.vk.photos.get(owner_id=user_id, extended=1, photo_sizes=1, album_id=album)
                photo = {photo['sizes'][-1]['url']: photo['likes']['count'] for photo in response['items']}
                result.extend(photo.items())
            except vk_api.exceptions.ApiError as e:
                if not str(e).startswith("[30] This profile is private") \
                        and not str(e).startswith("[200] Access denied"):
                    raise e
        return result











