import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    user_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String(length=40), nullable=False)
    last_name = sq.Column(sq.String(length=40), nullable=False)
    sex = sq.Column(sq.Integer, nullable=False)
    bdate = sq.Column(sq.String, nullable=False)
    city = sq.Column(sq.Integer, nullable=False)
    interest = sq.Column(sq.String, nullable=True)

    user_offer = relationship('UserOffer', back_populates='user')
    interest_user_offer = relationship('InterestUserOffer', back_populates='user')


class Offer(Base):
    __tablename__ = 'offer'

    offer_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String(length=40), nullable=False)
    last_name = sq.Column(sq.String(length=40), nullable=False)
    sex = sq.Column(sq.Integer, nullable=False)
    bdate = sq.Column(sq.Date, nullable=False)
    city = sq.Column(sq.Integer, nullable=False)
    interest = sq.Column(sq.String, nullable=True)

    user_offer = relationship('UserOffer', back_populates='offer')
    photo = relationship('Photo', back_populates='offer')
    interest_user_offer = relationship('InterestUserOffer', back_populates='offer')


class UserOffer(Base):
    __tablename__ = 'user_offer'

    user_offer_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.user_id'), nullable=False)
    offer_id = sq.Column(sq.Integer, sq.ForeignKey('offer.offer_id'), nullable=False)
    black_list = sq.Column(sq.Integer, nullable=False, default=0)
    favorite_list = sq.Column(sq.Integer, nullable=False, default=0)

    offer = relationship('Offer', back_populates='user_offer', cascade='all, delete')
    user = relationship('User', back_populates='user_offer', cascade='all, delete')


class Photo(Base):
    __tablename__ = 'photo'

    photo_id = sq.Column(sq.Integer, primary_key=True)
    offer_id = sq.Column(sq.Integer, sq.ForeignKey('offer.offer_id'), nullable=False)
    photo_url = sq.Column(sq.String, nullable=False)

    offer = relationship('Offer', back_populates='photo', cascade='all, delete')


class InterestUserOffer(Base):
    __tablename__ = 'interest_user_offer'

    interest_user_offer_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.user_id'))
    offer_id = sq.Column(sq.Integer, sq.ForeignKey('offer.offer_id'))
    interest_id = sq.Column(sq.Integer, sq.ForeignKey('interest.interest_id'), nullable=False)

    user = relationship('User', back_populates='interest_user_offer', cascade='all, delete')
    offer = relationship('Offer', back_populates='interest_user_offer', cascade='all, delete')
    interest = relationship('Interest', back_populates='interest_user_offer', cascade='all, delete')


class Interest(Base):
    __tablename__ = 'interest'

    interest_id = sq.Column(sq.Integer, primary_key=True)
    interest = sq.Column(sq.String(length=80), nullable=False)

    interest_user_offer = relationship('InterestUserOffer', back_populates='interest')


def create_table(engine):
    Base.metadata.create_all(engine)


def delete_table(engine):
    Base.metadata.drop_all(engine)
