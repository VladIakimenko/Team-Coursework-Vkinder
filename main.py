from datetime import datetime
import string

from bot import Bot, Searcher


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

    def sort_interests(raw):
        stripper = str.maketrans({char: '' for char in string.punctuation})
        return sorted([interest.translate(stripper).lower() for interest in raw.split()])

    if user.get('interests'):
        criteria['interests'] = sort_interests(user['interests'])

    return criteria


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

            result = searcher.search_users(search_params)
            print(result)

            # reply = ""
            # print(bot.say(user_id, reply))

    # long_poll.get_settings()
    # print(long_poll.set_settings())
