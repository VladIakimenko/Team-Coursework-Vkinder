import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker

from models import create_table

SQLsystem = 'postgresql'
login = 'postgres'
password = ''
host = 'localhost'
port = '5432'
db_name = ""
DSN = f'{SQLsystem}://{login}:{password}@{host}:{port}/{db_name}'
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)

with Session() as session:
    create_table(engine)
