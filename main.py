import sys
from datetime import datetime
import threading
import queue
import time
import atexit


from bot import Bot, Searcher
from transformer import form_criteria, filter_by_interests
from Database import connect

LOG_FILE = 'log.txt'


def listen():
    """
    Function keeps listening to long poll events and starts the
    event_thread(handle_event function) each time an incoming message is received.
    """
    while True:
        event = bot.listen()
        if event:
            if event[0] not in dialogues:
                dialogues[event[0]] = threading.Event()
                processed[event[0]] = threading.Event()
            event_thread = threading.Thread(target=handle_event,
                                            args=(event,))
            event_thread.start()


def check_account(user_id):
    """
    Checks an account validity.
    :return: False, if invalid
             True, if the account is active
    """
    account = bot.get_users_details(user_id)
    return not account.get('deactivated')


def handle_event(event):
    """
    Function analyses the incoming message and acts accordingly:
        'next': If the memory holds a record of the previously made suggestion, an event flag is set
                that unblocks the dialogue in the suggest_thread.
        If there was no proposal made so far or the text command is not recognized, the following
        algorythm is realized:
                - receive sender's details
                - add user to DB (optional)
                - form search criteria
                - request relevant records from DB
                    if at least 10 records found:
                - start suggest_thread
                    else:
                - start suggest_thread
                - start request_api_thread
        'blacklist'/'favorites': Adds a record to blacklist or favorites in DB
        'clear favorites': Clears the favorites list in DB
        'saved': sends names and link to the page for every record in favorites
    """
    sender_id, text = event
    offers_queue = queue.Queue()

    if text == 'next' and last_offers.get(sender_id):
        print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
              f'Next offer requested by user {sender_id}')
        dialogues[sender_id].set()

    elif text == 'blacklist' or text == 'favorites':
        if last_offers.get(sender_id):
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'Add to {text} requested by user {sender_id} '
                  f'for offer with id {last_offers[sender_id]}')
            if last_offers.get(sender_id):
                connect.add_black_list(sender_id, last_offers[sender_id]) if text == 'blacklist' \
                    else connect.add_favorite_list(sender_id, last_offers[sender_id])
                message = f"Пользователь добавлен(а) в {('чёрный список', 'избранное')[text == 'favorites']}."
                bot.say(sender_id, message)
                print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                      f"Offer with id {last_offers[sender_id]} "
                      f"added to user {sender_id}'s {text}\n")
        else:
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'No data on the last offer.')

    elif text == 'saved':
        favorites = connect.get_favorite(sender_id)
        for favorite in favorites:
            passed = check_account(favorite['id'])
            if not passed:
                connect.remove_records(favorite['id'])
                print(f"\nUser {favorite['id']}'s account has been deactivated! Removing from DB.")
                continue
            message = f"{favorite['first_name']} {favorite['last_name']}: " \
                       f"https://vk.com/id{favorite['id']}\n"
            bot.say(sender_id, message=message)

    elif text == 'clear favorites':
        connect.clear_favorites(sender_id)
        bot.say(sender_id, message='Список "Избранное" очищен!')

    else:
        print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
              f'Incoming message from user {sender_id}:\n'
              f'Message text:\n"{text}"')

        if last_offers.get(sender_id):
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'Dialogue with user {sender_id} already in progress.\n')
            bot.say(sender_id, 'Пожалуйста, используйте кнопки.')
            return
        elif processed[sender_id].is_set():
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'Suggestion for user {sender_id} is already being prepared.\n')
            bot.say(sender_id, 'Пожалуйста, подождите, обрабатываю Ваш запрос.')
            return

        processed[sender_id].set()
        details = bot.get_users_details(sender_id)
        print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
              f'User data received:\n{details}')

        print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
              f"Adding user {sender_id} to DB (if user's not there)")
        connect.add_user(details['id'],
                         details['first_name'],
                         details['last_name'],
                         details['sex'],
                         details.get('bdate'),
                         details.get('city', {}).get('id', 1),
                         details.get('interests'))

        search_params = form_criteria(details)
        if not search_params:
            print(bot.say(sender_id,
                          'Вы должны установить параметр "пол" в Вашем аккаунте, чтобы пользоваться ботом!'))
            return
        else:
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'Search criteria formed:\n{search_params}')

        print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
              f'Getting relevant accounts from DB for user {sender_id}')
        offers_from_db = connect.get_offer(search_params, sender_id)

        if offers_from_db and len(offers_from_db) >= 10:
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'{len(offers_from_db)} accounts received.')
            filtered = filter_by_interests(search_params, offers_from_db)
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'Accounts filtered by interests.\n'
                  f'Accounts with corresponding interests moved to the top of the list.')
            for account in filtered:
                offers_queue.put(account)
            suggest_thread = threading.Thread(target=suggest,
                                              args=(offers_queue, sender_id))
            suggest_thread.start()
        else:
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'No relevant accounts found in DB.')
            request_api_thread = threading.Thread(target=get_accounts_from_api,
                                                  args=(search_params, sender_id, offers_queue))
            request_api_thread.start()


def get_accounts_from_api(search_params, sender_id, offers_queue):
    """
    Function requests the API for accounts matching the "search_params".
    Then recursively requests for a list of albums and photos in each of the albums.
    In case at least three photos are present, saves the account to DB and adds it up
    to the queue that is used by the suggest_thread for making proposals while the search is
    still in progress.
    """
    def add_to_db(accounts):
        counter = 0
        print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
              f'Requesting API for accounts for user {sender_id}')

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

            connect.add_offer(sender_id,
                              offer_id,
                              first_name,
                              last_name,
                              sex,
                              bdate,
                              city['id'],
                              interests)
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
    print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
          f'\nTotal found {len(api_search_result)}')
    suggest_thread = threading.Thread(target=suggest,
                                      args=(offers_queue, sender_id))
    suggest_thread.start()
    print(f'Receiving all necessary details for adding to DB...')
    count = add_to_db(api_search_result)
    print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
          f'{count} accounts added to DB')
        
        
def suggest(offers_queue, user_id):
    """
    Function checks if the queue with accounts has at least 10 elements and starts sending proposals
    to the interlocutor.
    Before sending a message it checks if the suggested user is valid (not deactivated) and removes it
    from DB otherwise.
    After sending a message it awaits for the "next" command to continue offering from the queue.
    In case there is no message from user for over 10 minutes it finshes the dialogue (to be started all
    over again, when user comes back next time)
    In case the queue runs empty, the user receives a notice and is suggested to come back later.
    """
    while True:
        if offers_queue.qsize() >= 10:
            break
        time.sleep(1)

    print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
          f'{offers_queue.qsize()} accounts are ready to be offered.\n'
          f'Starting to suggest!')

    def suggest():
        passed = False
        while not passed:
            suggestion = offers_queue.get()
            passed = check_account(suggestion['id'])
            if not passed:
                print(f"\nUser {suggestion['id']}'s account has been deactivated! Removing from DB.")
                connect.remove_records(suggestion['id'])

        name = f"{suggestion['first_name']} {suggestion['last_name']}"
        link = f"https://vk.com/id{suggestion['id']}"
        photos = suggestion['photos']
        bot.suggest(user_id, name, link, photos)
        last_offers[user_id] = suggestion['id']
        print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
              f'Suggestion sent to user {user_id}')

    suggest()
    while offers_queue.qsize() > 0:
        if dialogues[user_id].wait(timeout=600):
            dialogues[user_id].clear()
            suggest()
            print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
                  f'Suggestion sent to user {user_id}')
            if offers_queue.qsize() == 0:
                message = "Предложений больше нет. Возвращайтесь в другой раз!"
                print(bot.say(user_id, message))
            continue

        del(dialogues[user_id])
        del(last_offers[user_id])
        del(processed[user_id])
        print(f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
              f'Dialogue with {user_id} closed.')
        break
    
        
if __name__ == '__main__':
    bot = Bot()
    searcher = Searcher()
    accounts = []
    dialogues = {}
    last_offers = {}
    processed = {}

    connect.clear_population()                                 # MAKE SURE TO REMOVE THIS LINE WHEN PUSHING TO PROD
    log_file = open(LOG_FILE, 'at', encoding='UTF-8')
    sys.stderr = log_file
    sys.stdout = log_file
    atexit.register(lambda file: file.close, log_file)
    
    print(bot.get_server())
    
    listen_thread = threading.Thread(target=listen)
    listen_thread.start()

