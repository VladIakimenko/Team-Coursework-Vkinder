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

    user_offer = relationship('UserOffer', back_populates='user', cascade='all, delete')


class Offer(Base):
    __tablename__ = 'offer'

    offer_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String(length=40), nullable=False)
    last_name = sq.Column(sq.String(length=40), nullable=False)
    sex = sq.Column(sq.Integer, nullable=False)
    bdate = sq.Column(sq.Date, nullable=False)
    city = sq.Column(sq.Integer, nullable=False)
    interest = sq.Column(sq.String, nullable=True)

    user_offer = relationship('UserOffer', back_populates='offer', cascade='all, delete')
    photo = relationship('Photo', back_populates='offer', cascade='all, delete')


class UserOffer(Base):
    __tablename__ = 'user_offer'

    user_offer_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    offer_id = sq.Column(sq.Integer, sq.ForeignKey('offer.offer_id', ondelete='CASCADE'), nullable=False)
    black_list = sq.Column(sq.Integer, nullable=False, default=0)
    favorite_list = sq.Column(sq.Integer, nullable=False, default=0)

    offer = relationship('Offer', back_populates='user_offer')
    user = relationship('User', back_populates='user_offer')


class Photo(Base):
    __tablename__ = 'photo'

    photo_id = sq.Column(sq.Integer, primary_key=True)
    offer_id = sq.Column(sq.Integer, sq.ForeignKey('offer.offer_id', ondelete='CASCADE'), nullable=False)
    photo_url = sq.Column(sq.String, nullable=False)

    offer = relationship('Offer', back_populates='photo')


def create_table(engine):
    Base.metadata.create_all(engine, checkfirst=True)


def delete_table(engine):
    Base.metadata.drop_all(engine)
