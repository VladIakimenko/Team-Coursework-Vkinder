import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker


from models import create_table, User, Offer, UserOffer, delete_table, Photo, Interest, InterestUserOffer

SQLsystem = 'postgresql'
login = 'postgres'
password = ''
host = 'localhost'
port = '5432'
db_name = ""
DSN = f'{SQLsystem}://{login}:{password}@{host}:{port}/{db_name}'
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)

delete_table(engine)
create_table(engine)


def add_user(user_id: int, first_name: str, last_name: str, sex: int, age: int, city: str):
    """
        Function adds a user to the database.
    :param user_id: id user
    :param first_name: first name user
    :param last_name: last name user
    :param sex: gender user. 1 - female, 2 - male
    :param age: age user
    :param city: city user
    """
    with Session() as session:
        user_find = session.query(User.user_id).all()
        if user_id not in [user[0] for user in user_find]:
            user = User(user_id=user_id, first_name=first_name, last_name=last_name, sex=sex, age=age, city=city)
            session.add(user)
            session.commit()


def add_offer(user_id: int, offer_id: int, first_name: str, last_name: str, sex: int, age: int, city: str):
    """
        The function adds an offer to the database.
    :param user_id: id user
    :param offer_id: id offer
    :param first_name: first name of offer
    :param last_name: last name of offer
    :param sex: gender offer. 1 - female, 2 - male
    :param age: age offer
    :param city: city offer
    """
    with Session() as session:
        offer_find = session.query(Offer.offer_id).all()
        if offer_id not in [offer[0] for offer in offer_find]:
            offer = Offer(offer_id=offer_id, first_name=first_name, last_name=last_name, sex=sex, age=age,
                          city=city)
            session.add(offer)
        user_offer_find = session.query(UserOffer.user_offer_id). \
            filter(UserOffer.user_id == user_id). \
            filter(UserOffer.offer_id == offer_id).all()
        if len(user_offer_find) == 0:
            user_offer = UserOffer(user_id=user_id, offer_id=offer_id, black_list=0, favorite_list=0)
            session.add(user_offer)
        session.commit()


def add_black_list(user_id: int, offer_id: int):
    """
        Function adds an offer to the black list. Offer is permanently hidden from the search.
    0 - offer is irrelevant, 1 - offer is excluded from the search
    :param user_id: id user
    :param offer_id: id offer
    """
    with Session() as session:
        session.query(UserOffer). \
            filter(UserOffer.offer_id == offer_id). \
            filter(UserOffer.user_id == user_id). \
            filter(UserOffer.black_list == 0). \
            update({'black_list': 1})
        session.commit()


def add_favorite_list(user_id: str, offer_id: str):
    """
        Function adds the offer to favorites if the user wants to save the offer.
    0 - offer is irrelevant, 1 - offer is included in favorites
    :param user_id: id user
    :param offer_id: id offer
    """
    with Session() as session:
        session.query(UserOffer). \
            filter(UserOffer.vk_offer_id == offer_id). \
            filter(UserOffer.vk_user_id == user_id). \
            filter(UserOffer.black_list == 0). \
            update({'favorite_list': 1})
        session.commit()


def add_photo(offer_id: int, photo_url: list[str]):
    """
        Function saves links to photos of the offer in the database
    :param offer_id: id offer
    :param photo_url: list photo url
    """
    with Session() as session:
        for url in photo_url:
            photo_find = session.query(Photo).filter(Photo.id_photo == url).all()
            if len(photo_find) == 0:
                photo = Photo(id_photo=url, offer_id=offer_id)
                session.add(photo)
            session.commit()


def add_interest(interest: str, user_id=0, offer_id=0):
    """
        Function adds user interests or offers to the database
    :param interest: name of user interest or offer
    :param user_id: id user
    :param offer_id: id offer
    """
    with Session() as session:
        interest_find = session.query(Interest.interest).filter(Interest.interest == interest)
        if interest not in [interest[0] for interest in interest_find]:
            interest_add = Interest(interest="interest")
            session.add(interest_add)
        interest_id_find = session.query(Interest.interest_id).filter(Interest.interest == interest).all()[0][0]
        user_find = session.query(InterestUserOffer.user_id). \
            filter(InterestUserOffer.interest_id == interest_id_find). \
            filter(InterestUserOffer.user_id == user_id).all()
        offer_find = session.query(InterestUserOffer.offer_id). \
            filter(InterestUserOffer.interest_id == interest_id_find). \
            filter(InterestUserOffer.vk_offer_id == offer_id).all()
        if user_id != 0 and user_id not in [user[0] for user in user_find]:
            interest_person_add = InterestUserOffer(vk_user_id=user_id, interest_id=interest_id_find)
            session.add(interest_person_add)
        if offer_id != 0 and offer_id not in [offer[0] for offer in offer_find]:
            interest_person_add = InterestUserOffer(vk_offer_id=offer_id, interest_id=interest_id_find)
            session.add(interest_person_add)
        session.commit()


def get_offer_info(user_id, offer):
    """
        Function provides information about offers.
    :param user_id: id user
    :param offer: object containing information about offers
    :return: list containing lists with details of offers
            format list:
            [[offer 1], [offer 2], ...]
            format offer:
            [id offer, 'first name', 'last name', sex, age, 'city',
            [list with url photo], [list with general user interests and offer]]
    """
    offer_list = []
    with Session() as session:
        user_interests = session.query(Interest.interest). \
            join(InterestUserOffer, InterestUserOffer.interest_id == Interest.interest_id). \
            filter(InterestUserOffer.user_id == user_id).all()
        for note in offer:
            offer_list.append([])
            for el in note:
                offer_list[-1].append(el)
            photo = session.query(Photo.id_photo).filter(Photo.offer_id == note[0]).all()
            offer_list[-1].append([url[0] for url in photo])
            offer_interests = session.query(Interest.interest). \
                join(InterestUserOffer, InterestUserOffer.interest_id == Interest.interest_id). \
                filter(InterestUserOffer.offer_id == note[0]).all()
            interest_list = []
            for interest in [inter_user[0] for inter_user in user_interests]:
                if interest in [inter_offer[0] for inter_offer in offer_interests]:
                    interest_list.append(interest)
            offer_list[-1].append(interest_list)
    return offer_list


def get_offer(user_id):
    """
        Function provides information about all offers.
    :param user_id: id user
    :return: list containing list with details of offers
            format list:
            [[offer 1], [offer 2]...]
            format offer:
            [id user, 'first nam', 'last name', sex, age, 'city',
            [list with url photo], [list with general user interests and offer]]
    """
    with Session() as session:
        offer = session.query(Offer.offer_id,
                              Offer.first_name,
                              Offer.last_name,
                              Offer.sex,
                              Offer.age,
                              Offer.city). \
            join(UserOffer, UserOffer.offer_id == Offer.offer_id). \
            join(User, User.user_id == UserOffer.user_id). \
            filter(User.user_id == user_id). \
            filter(UserOffer.black_list == 0). \
            filter(UserOffer.favorite_list == 0).all()
        result = get_offer_info(user_id, offer)
    return result


def get_favorite(user_id):
    """
            Function provides information about featured offers.
    :param user_id: id user
    :return: list containing list with details of offers.
            Формат листа:
            [[offer 1], [offer 2]...]
            format offer:
            [id user, 'first nam', 'last name', sex, age, 'city',
            [list with url photo], [list with general user interests and offer]]
    """
    with Session() as session:
        offer = session.query(Offer.offer_id,
                              Offer.first_name,
                              Offer.last_name,
                              Offer.sex,
                              Offer.age,
                              Offer.city). \
            join(UserOffer, UserOffer.offer_id == Offer.offer_id). \
            join(User, User.user_id == UserOffer.user_id). \
            filter(User.user_id == user_id). \
            filter(UserOffer.favorite_list == 1).all()
        result = get_offer_info(user_id, offer)
    return result


def get_user():
    """
        Function provides information about the id of all users
    :return: List with id users
    """
    with Session() as session:
        return [user[0] for user in session.query(User.user_id).all()]

# add_user(user_id=1, first_name='Oleg', last_name="Sun", sex=2, age=26, city='NN')
# add_offer(user_id=1, offer_id=2, first_name="Ol", last_name='Pi', sex=1, age=22, city='NN')
# add_offer(user_id=1, offer_id=1, first_name="Olga", last_name='Piop', sex=1, age=22, city='NN')
