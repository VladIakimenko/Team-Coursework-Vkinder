FROM python:3.10

WORKDIR /app

COPY Pipfile Pipfile.lock /app/

RUN pip install pipenv

RUN pipenv install
    
COPY . /app/

CMD ["pipenv", "run", "python", "main.py"]
