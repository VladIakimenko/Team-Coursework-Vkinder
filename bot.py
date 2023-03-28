import os
import json
import random

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
                       'access_token': os.environ.get("SECRET"),
                       'v': '5.131'}

    def get_server(self):
        """
        Getting session data (required when first addressing to long poll)
        :return: "session data successfully received" OR error message
        """
        method = 'groups.getLongPollServer/'
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


if __name__ == '__main__':
    bot = Bot()
    print(bot.get_server())
    while True:
        event = bot.listen()
        if event:
            user, text = event
            print(f'Incoming message from user {user}:\n'
                  f'"{text}"')
            reply = "Hi, thanks for your interest! I am a dating bot, a Love Machine in some way...\n" \
                    "Unfortunately, for now I can only service you myself, " \
                    "but in future I'll be able to offer some nice dating suggestions out of VK users."
            print(bot.say(user, reply))

    # long_poll.get_settings()
    # print(long_poll.set_settings())







