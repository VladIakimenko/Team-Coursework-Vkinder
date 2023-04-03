import os
import json
import random
import vk_api

import requests
from dotenv import load_dotenv


class Bot:
    dotenv_path = '.env'
    settings_path = 'settings.cfg'
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

    def say(self, recipient, message):
        randint = random.randint(-2147483648, 2147483647)
        method = 'messages.send'
        data = {'user_id': {recipient}, 'message': {message}, 'random_id': randint}
        params = {**self.params, **data}
        response = requests.get(self.base + method, params=params)
        if response.json().get('response'):
            return 'message successfully sent'
        else:
            return response.json().get('error', {}).get('error_msg', 'unknown error')

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
            code = f.read().replace('<city>', str(criteria['city'])) \
                .replace('<sex>', str(criteria['sex'])) \
                .replace('<age_from>', str(criteria['age_from'])) \
                .replace('<age_to>', str(criteria['age_to']))
        response = self.vk.execute(code=code)
        return response[0]['items'] if response else response



