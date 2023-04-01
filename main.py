from datetime import datetime
import string
import time

import pymorphy2

from bot import Bot, Searcher

morph = pymorphy2.MorphAnalyzer()


def form_criteria(user):
    criteria = {}

    if user.get('city'):
        criteria['city'] = user.get('city', {}).get('id', '')

    if user.get('sex'):
        criteria['sex'] = (1, 2)[user['sex'] == 1]
    else:
        raise Exception("ERROR: Cannot form search criteria if user's sex is not determined in profile!")

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

    if user.get('interests'):
        criteria['interests'] = sort_interests(user['interests'])

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


def browse_for_photos(accounts, start_from):
    index = start_from
    while True:
        albums = searcher.get_albums(accounts[index]['id'])
        time.sleep(0.35)
        index += 1
        print(f'\rПретендент номер:{index}\t\t'
              f'Кол-во альбомов:{len(albums) if albums != False else albums}', end='')
        photos = searcher.get_photos(accounts[index]['id'], albums)
        if len(photos) >= 3:
            return (accounts[index]['id'],
                    sorted(photos, key=lambda x: x[1], reverse=True),
                    index)

        if index == len(accounts) - 1:
            return False


if __name__ == '__main__':
    bot = Bot()
    searcher = Searcher()

    print(bot.get_server())
    while True:
        event = bot.listen()
        if event:
            user_id, text = event
            print(f'Incoming message from user {user_id}:\n'
                  f'"{text}"')

            details = bot.get_users_details(user_id)
            print(details)

            search_params = form_criteria(details)
            print(search_params)

            all_ = searcher.search_users(search_params)
            print(f'\ntotal found: {len(all_)}')

            filtered_by_interests = filter_by_interests(search_params, all_)
            print(f' total filtered: {len(filtered_by_interests)}')

            for person in filtered_by_interests:
                print(f"{person['first_name']} {person['last_name']}")
                print(f"пол: {('ОШИБКА', 'женский')[person['sex'] == 1]}")
                print(f"город: {person.get('city', '')}")
                print(f"дата рождения: {person.get('bdate', '')}")
                print(f"интересы: {person.get('interests', '')}")
                print(f"как их видит прога: {sort_interests(person['interests']) if person.get('interests') else ''}")
                print()

            stopped_at = 0
            while True:
                result = browse_for_photos(filtered_by_interests, stopped_at)
                if result:
                    user_id, photos, stopped_at = result
                    print('\n')
                    print(f'ID пользователя: {user_id}')
                    print(f'Фото: {photos}')
                    input('"Enter" для продолжения')
                else:
                    break






            # reply = ""
            # print(bot.say(user_id, reply))

    # long_poll.get_settings()
    # print(long_poll.set_settings())
