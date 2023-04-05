import string
from datetime import datetime
import threading
import queue
import time

import pymorphy2

from bot import Bot, Searcher
from Database import connect

morph = pymorphy2.MorphAnalyzer()


def form_criteria(user):
    criteria = {}

    if user.get('city'):
        criteria['city'] = user.get('city', {}).get('id', '')

    if user.get('sex'):
        criteria['sex'] = (1, 2)[user['sex'] == 1]
    else:
         # SEND A MESSAGE THAT WE CAN"T HELP IF YOU HAVE NO SEX
        return

    def age_from_bdate(bdate):
        try:
            return (datetime.now() - datetime.strptime(bdate, '%d.%m.%Y')).days // 365
        except ValueError:
            return None

    if user.get('bdate'):
        max_delta = 8
        min_age = 18
        user_age = age_from_bdate(user['bdate'])
        if user_age:
            criteria['age_to'] = user_age + max_delta
            criteria['age_from'] = max(user_age - max_delta, min_age)
        else:
            criteria['age_from'] = min_age
            criteria['age_to'] = 99

    if user.get('interests'):
        criteria['interests'] = sort_interests(user['interests'])
    else:
        criteria['interests'] = []
    return criteria


def sort_interests(raw):
    stop_list = ['ходить', 'смотреть', 'играть', 'делать', 'заниматься', 'слушать']
    stripper = str.maketrans({char: '' for char in string.punctuation})
    interests = [interest.translate(stripper).lower() for interest in raw.split()
                 if len(interest) >= 4]
    interests = filter(lambda word: morph.parse(word) and 'NOUN' in morph.parse(word)[0].tag
                                    or 'INFN' in morph.parse(word)[0].tag and word not in stop_list,
                       interests)
    return sorted(interests)


def filter_by_interests(criteria, candidates):
    perfect_matches = {}
    for candidate in candidates:
        if candidate.get('interests'):
            counter = 0
            for target in criteria['interests']:
                for interest in sort_interests(candidate['interests']):
                    if target == interest:
                        counter += 1
            if counter > 0:
                perfect_matches[counter] = candidate

    for candidate in perfect_matches.values():
        if candidate in candidates:
            candidates.remove(candidate)

    return [perfect_matches[count] for count in sorted(perfect_matches.keys(), reverse=True)] + \
           [candidate for candidate in candidates if candidate not in perfect_matches.values()]


def send_suggestion(account, sender_id):
    name = f"{account['first_name']} {account['last_name']}"
    link = f"https://vk.com/id{account['id']}"
    photos = account['photos']
    bot.suggest(sender_id, name, link, photos)


if __name__ == '__main__':
    bot = Bot()
    searcher = Searcher()
    accounts = []
    dialogues = {}
    # connect.clear_population()                      # MAKE SURE TO REMOVE THIS LINE WHEN PUSHING TO PROD

    print(bot.get_server())

    def listen_thread_func():

        while True:
            event = bot.listen()
            if event:
                if event[0] not in dialogues:
                    dialogues[event[0]] = threading.Event()
                event_thread = threading.Thread(target=handle_event, args=(event,))
                event_thread.start()

    def handle_event(event):
        sender_id, text = event
        offers_queue = queue.Queue()

        if text == 'предложить еще':
            print(f'Получен запрос на след. предложение от {sender_id}')
            dialogues[sender_id].set()
            print(f'Маяк установлен!')
        else:
            print(f'Получено сообщение от пользователя {sender_id}:\n'
                  f'Содержание сообщения:\n"{text}"')

            details = bot.get_users_details(sender_id)
            print(f'Получены данные пользователя:\n{details}')

            print(f'Добавляем данные о пользователе {sender_id} в БД (если отсутсвует)')
            connect.add_user(details['id'],
                             details['first_name'],
                             details['last_name'],
                             details['sex'],
                             details.get('bdate'),
                             details.get('city', {}).get('id', ''),
                             details.get('interests'))

            search_params = form_criteria(details)
            print(f'Сформированы параметры поиска:\n{search_params}')

            print('Получаем подходящие аккаунты из БД...')
            offers_from_db = connect.get_offers(search_params)

            if offers_from_db and len(offers_from_db) >= 10:
                print(f'Получено {len(offers_from_db)} аккаунтов.')
                filtered = filter_by_interests(search_params, offers_from_db)
                print(f'Произведена фильтрация по интересам.\n'
                      f'Аккаунты с подходящими интересами перемещены во главу списка.')
                for account in filtered:
                    offers_queue.put(account)
                suggest_thread = threading.Thread(target=suggest, args=(offers_queue, sender_id))
                suggest_thread.start()
            else:
                print(f'Подходящих аккаунтов в БД не обнаружено.')
                request_api_thread = threading.Thread(target=get_accounts_from_api, args=(search_params, sender_id, offers_queue))
                request_api_thread.start()

    def get_accounts_from_api(search_params, sender_id, offers_queue):
        def add_to_db(accounts):
            counter = 0

            for i, account in enumerate(accounts):
                progress = f'{round(((i + 1) * 100) / len(accounts), 2)} %'
                print('\r' + progress, end='')

                offer_id = account['id']
                raw = searcher.get_photos_and_details(offer_id, )

                if not raw:
                    continue
                else:
                    raw = sum(raw, [])

                photos = {photo['sizes'][-1]['url']: photo['likes']['count'] for photo in raw}
                photos = [pair[0] for pair in sorted(photos.items(), key=lambda x: x[1])][:3]
                if len(photos) < 3:
                    continue

                first_name = f"{account['first_name']}"
                last_name = f"{account['last_name']}"

                if not all([account.get('bdate'), account.get('city'), account.get('sex')]):
                    continue
                else:
                    bdate = account['bdate']
                    city = account['city']
                    sex = account['sex']

                try:
                    bdate = datetime.strptime(bdate, '%d.%m.%Y').date()
                except ValueError:
                    continue

                interests = account.get('interests', '')

                connect.add_offer(sender_id, offer_id, first_name, last_name, sex, bdate, city['id'], interests)
                connect.add_photo(offer_id, photos)
                counter += 1
                offers_queue.put({'id': offer_id,
                                  'first_name': first_name,
                                  'last_name': last_name,
                                  'sex': sex,
                                  'bdate': bdate,
                                  'city': city,
                                  'interests': interests,
                                  'photos': photos})

            return counter

        api_search_result = searcher.search_users(search_params)
        print(f'\nВсего найдено {len(api_search_result)} аккаунтов')
        print(f'Получаем данные для сохранения в БД...')
        suggest_thread = threading.Thread(target=suggest,
                                          args=(offers_queue, sender_id))
        suggest_thread.start()
        count = add_to_db(api_search_result)
        print('\n')
        print(f'В базу внесено: {count} аккаунтов')

    def suggest(offers_queue, user_id):
        while True:
            if offers_queue.qsize() >= 10:
                break
            time.sleep(1)

        print(f'\n\n{offers_queue.qsize()} аккаунтов уже подготовлены к предложению.\n'
              f'Начинаю предлагать!')

        send_suggestion(offers_queue.get(), user_id)
        print(f'\nПредложение отправлено пользователю {user_id}')

        while offers_queue.qsize() > 0:
            if dialogues[user_id].wait(timeout=600):
                print('Маяк получен!')
                dialogues[user_id].clear()
                send_suggestion(offers_queue.get(), user_id)
                print(f'\nПредложение отправлено пользователю {user_id}')
                continue
            del(dialogues[user_id])
            print(f'\nДиалог с пользователем {user_id} завершён.')
            break

    listen_thread = threading.Thread(target=listen_thread_func)
    listen_thread.start()



            # reply = ""
            # print(bot.say(user_id, reply))

    # long_poll.get_settings()
    # print(long_poll.set_settings())
