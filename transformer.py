import pymorphy2
import string
from datetime import datetime


morph = pymorphy2.MorphAnalyzer()


def form_criteria(user):
    """
    The function forms search criteria based on the user's details.
    user: {'id': int,
           'bdate': str,
            city': {'id': int, 'title': str},
           'interests': str,
           'sex': int,
           'first_name': str,
           'last_name': str}
    :return: criteria: {'city': int,
                        'sex': int,
                        'age_to': int,
                        'age_from': int,
                        'interests': [str, ...]}
         OR: None, if user['sex'] hasn't  been provided
    """
    criteria = {}

    criteria['city'] = user.get('city', {}).get('id', '1')

    if user.get('sex'):
        criteria['sex'] = (1, 2)[user['sex'] == 1]
    else:
        return None

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
    """
    Linguistic analysis function that picks out nouns and verbs in
    infinitive form and sorts them in lexicographic order, to allow comparison of the interests fields.


    """
    stop_list = ['ходить', 'смотреть', 'играть', 'делать', 'заниматься', 'слушать']
    stripper = str.maketrans({char: '' for char in string.punctuation})
    interests = [interest.translate(stripper).lower() for interest in raw.split()
                 if len(interest) >= 4]
    interests = filter(lambda word: morph.parse(word) and 'NOUN' in morph.parse(word)[0].tag
                                    or 'INFN' in morph.parse(word)[0].tag and word not in stop_list,
                       interests)
    return sorted(interests)


def filter_by_interests(criteria, candidates):
    """
    Takes the search criteria and the list of accounts, finds the accounts with matching interests,
    sorts them by the number of matching words and puts these accounts in the head of the list.
    criteria: {'city': int,
               'sex': int,
               'age_to': int,
               'age_from': int,
               'interests': [str, ...]}
    candidates:  [{'id': int,
                   'bdate': str,
                   'city': {'id': int, 'title': str},
                   'interests': str,
                   'sex': int,
                   'first_name': str,
                   'last_name': str}, ...]
    :return: "candidates" reordered
    """
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
