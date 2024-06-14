import logging
import os
import sched
import time
from datetime import datetime

import requests
import sqlalchemy as sa
from sqlalchemy_cratedb import ObjectType

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

CRATEDB_HOST = os.getenv('CRATEDB_HOST')

API_KEY = os.getenv('WEATHER_API_KEY')
CITY = os.getenv('CITY_NAME')
URI = f'https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}&aqi=no'

RUN_EVERY_SECONDS = int(os.getenv('FETCH_EVERY_SECONDS', 60))

# Setup sqlalchemy
engine = sa.create_engine(f"crate://{CRATEDB_HOST}")
Base = sa.orm.declarative_base()
Session = sa.orm.sessionmaker(bind=engine)
session = Session()


class Weather(Base):
    __tablename__ = 'weather'
    inserted_at = sa.Column(sa.DateTime, primary_key=True, default=datetime.now)
    location = sa.Column(ObjectType)
    current = sa.Column(ObjectType)


def fetch_data(api_uri) -> dict:
    response = requests.get(api_uri)
    response.raise_for_status()
    return response.json()


def insert_record():
    data = fetch_data(URI)

    record = Weather(**data)
    session.add(record)
    session.flush()


def schedule_every(seconds, func, scheduler):
    # schedule the next call first
    scheduler.enter(seconds, 1, schedule_every, (RUN_EVERY_SECONDS, insert_record, scheduler))

    func()


def main():
    try:
        logger.debug('Creating table if doesn\'t exist')
        Weather.__table__.create(engine, checkfirst=True)

        logger.debug(f'Starting scheduler, will run every {RUN_EVERY_SECONDS}(s)')
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(RUN_EVERY_SECONDS, 1, schedule_every, (RUN_EVERY_SECONDS, insert_record, scheduler))
        scheduler.run()

    except KeyboardInterrupt:
        logger.info('Exit: KeyboardInterrupt')


if __name__ == '__main__':
    main()
