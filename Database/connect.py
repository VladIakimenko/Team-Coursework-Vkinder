from datetime import datetime, timedelta

import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker

from Database.models import create_table, User, UserOffer, Photo, Offer
from Database.postgres_config import SQLSYS, USER, PASSWORD, HOST, PORT, DATABASE

SQLsystem = SQLSYS
login = USER
password = PASSWORD
host = HOST
port = PORT
db_name = DATABASE

DSN = f'{SQLsystem}://{login}:{password}@{host}:{port}/{db_name}'
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)


def create_tables():
    create_table(engine)
    

def add_user(user_id: int, first_name: str, last_name: str, sex: int, bdate: str, city: int, interest: str):
    """
        Function adds a user to the database.
    :param user_id: id user
    :param first_name: first name user
    :param last_name: last name user
    :param sex: gender user. 1 - female, 2 - male
    :param bdate: date of birth
    :param city: city user
    :param interest: user's interests
    """
    with Session() as session:
        user_find = session.query(User.user_id).all()
        if user_id not in [user[0] for user in user_find]:
            user = User(user_id=user_id, first_name=first_name, last_name=last_name, sex=sex, bdate=bdate, city=city, interest=interest)
            session.add(user)
            session.commit()


def add_offer(user_id: int, offer_id: int, first_name: str, last_name: str, sex: int, bdate: datetime.date, city: int, interest: str):
    """
        Function adds an offer to the database.
    :param user_id: id user
    :param offer_id: id offer
    :param first_name: first name of offer
    :param last_name: last name of offer
    :param sex: gender offer. 1 - female, 2 - male
    :param bdate: birthdate
    :param city: city offer
    """
    with Session() as session:
        offer_find = session.query(Offer.offer_id).all()
        if offer_id not in [offer[0] for offer in offer_find]:
            offer = Offer(offer_id=offer_id, first_name=first_name, last_name=last_name, sex=sex, bdate=bdate,
                          city=city)
            session.add(offer)
        user_offer_find = session.query(UserOffer.user_offer_id). \
            filter(UserOffer.user_id == user_id). \
            filter(UserOffer.offer_id == offer_id).all()
        if len(user_offer_find) == 0:
            user_offer = UserOffer(user_id=user_id, offer_id=offer_id, black_list=0, favorite_list=0)
            session.add(user_offer)
        session.commit()


def remove_records(offer_id):
    """
    Function removes the records from the Offer table by "offer_id".
    Since cascade removal is adjusted, all relevant records from other tables are evenly removed.
    """
    with Session() as session:
        session.query(Offer).filter(Offer.offer_id == offer_id).delete()
        session.commit()


def clear_favorites(user_id):
    """
    Function clears up the favorites list.
    """
    with Session() as session:
        session.query(UserOffer).filter(UserOffer.user_id == user_id).delete()
        session.commit()


def add_black_list(user_id: int, offer_id: int):
    """
        Function adds an offer to the black list. Offer is permanently hidden from the search.
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
    :param user_id: id user
    :param offer_id: id offer
    """
    with Session() as session:
        session.query(UserOffer). \
            filter(UserOffer.offer_id == offer_id). \
            filter(UserOffer.user_id == user_id). \
            filter(UserOffer.black_list == 0). \
            update({'favorite_list': 1})
        session.commit()


def add_photo(offer_id, photo_url):
    """
        Function saves links to photos of the offer in the database
    :param offer_id: id offer
    :param photo_url: list photo url
    """
    with Session() as session:
        for url in photo_url:
            photo_find = session.query(Photo).filter(Photo.photo_url == url).all()
            if len(photo_find) == 0:
                photo = Photo(photo_url=url, offer_id=offer_id)
                session.add(photo)
            session.commit()


def prepare_output(raw):
    """
    Reforms the return from get_offer function to resemble the vk api output.
    Adds photos as a list to the collection.
    """
    result = []
    with Session() as session:
        for element in raw:
            photos = session.query(Photo.photo_url).filter(Photo.offer_id == element[0]).all()
            result.append({'id': element[0],
                           'first_name': element[1],
                           'last_name': element[2],
                           'sex': element[3],
                           'bdate': element[4],
                           'city': {'id': element[5]},
                           'interests': element[6],
                           'photos': [photo[0] for photo in photos]})
    return result


def get_offer(criteria, user_id):
    """
        Function takes a structure produced by the form_criteria func and
    :returns: a list of offers that fit the criteria.
    """

    today = datetime.utcnow()
    birthdate_from = today - timedelta(days=365 * criteria['age_to'])
    birthdate_to = today - timedelta(days=365 * criteria['age_from'])

    with Session() as session:
        offer = session.query(Offer.offer_id,
                              Offer.first_name,
                              Offer.last_name,
                              Offer.sex,
                              Offer.bdate,
                              Offer.city,
                              Offer.interest).\
            filter(Offer.city == criteria['city']). \
            filter(Offer.sex == criteria['sex']). \
            filter(Offer.bdate.between(birthdate_from, birthdate_to)). \
            join(UserOffer, UserOffer.offer_id == Offer.offer_id). \
            join(User, User.user_id == UserOffer.user_id). \
            filter(User.user_id == user_id). \
            filter(UserOffer.black_list == 0). \
            filter(UserOffer.favorite_list == 0). \
            all()
        result = prepare_output(offer)

    return result


def get_favorite(user_id):
    """
        Function provides information about featured offers.
    :returns: a list of offers from DB that have been saved to favorites
    """
    with Session() as session:
        offer = session.query(Offer.offer_id,
                              Offer.first_name,
                              Offer.last_name,
                              Offer.sex,
                              Offer.bdate,
                              Offer.city,
                              Offer.interest).\
            join(UserOffer, UserOffer.offer_id == Offer.offer_id). \
            join(User, User.user_id == UserOffer.user_id). \
            filter(User.user_id == user_id). \
            filter(UserOffer.favorite_list == 1).all()
        result = prepare_output(offer)
    return result


def get_user():
    """
        Function provides information about the id of all users
    :return: List with id users
    """
    with Session() as session:
        return [user[0] for user in session.query(User.user_id).all()]


