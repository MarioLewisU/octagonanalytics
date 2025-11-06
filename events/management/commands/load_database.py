from octagonanalytics.settings import BASE_DIR
from django.core.management.base import BaseCommand, CommandParser
from django.db.models.functions import Concat
from django.db.models import Value
from events.models import Event
from fighters.models import Fighter
from fights.models import Fight, FightStat
from typing import Any
from datetime import datetime
from collections import defaultdict
import json
import requests
import logging
import os
import pandas as pd
import numpy as np
import re

# TODO:
# - handle skipping duplicate fight stats
# - order events by date before insertion
# - add args
#   - clear tables before loading

logger = logging.getLogger(__name__)
DATA_DIR = BASE_DIR / "load_database"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUT_DATA_DIR = DATA_DIR / "out"


def _raw_data_path(file: str):
    """
    Get the path of a file in the raw data directory.
    """
    return (RAW_DATA_DIR / file).resolve()


def _out_data_path(file: str):
    """
    Get the path of a file in the output directory.
    """
    return (OUTPUT_DATA_DIR / file).resolve()


def _parse_date(date_string: str | None):
    """
    Parse a date string into a datetime from the various formats found in the raw UFC data. 
    """
    # Check for NaN values
    if date_string is None:
        return

    formats = [
        '%B %d, %Y',
        '%b %d, %Y',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue


def _parse_time(time_string: str | None):
    """
    Parse a time string of format "mm:ss" into an integer representing total seconds.
    """
    if time_string is None:
        return 0

    try:
        m, s = list(map(int, time_string.split(":")))
        return m * 60 + s
    except:
        return 0


class Command(BaseCommand):
    help = "Scrape and load UFC data into the database."

    # def add_arguments(self, parser: CommandParser) -> None:
    #     parser.add_argument(
    #         '--clear-tables',
    #         help='Delete all existing records from the database before processing data. THIS ACTION IS PERMANENT.',
    #         action='store_false',
    #     )

    #     parser.add_argument(
    #         '--process-only',
    #         help='Only process and prepare raw data, does not insert any records into the database.',
    #         action='store_false',
    #     )

    def handle(self, *args: Any, **options: Any) -> str | None:
        logger.info(
            f'Beginning database update with args: {json.dumps(options)}')

        try:
            self.ensure_folders()
            self.download_raw_data()
            self.process_raw_data()

            # if options['process-only']:
            #     logger.info('Completed processing UFC data')
            #     return

            self.load_database()
        except Exception as err:
            logger.error(f'Error occurred while updating data: {err}')
        logger.info('Database update complete')

    def ensure_folders(self):
        """
        Creates output folders if they do not exist, and empties them if they do.
        """
        if not DATA_DIR.exists():
            DATA_DIR.mkdir()

        if not RAW_DATA_DIR.exists():
            RAW_DATA_DIR.mkdir()

        if not OUTPUT_DATA_DIR.exists():
            OUTPUT_DATA_DIR.mkdir()

    def download_raw_data(self):
        """
        Download the raw csv data files from the scraper source.
        """
        files = [
            "ufc_event_details.csv",
            "ufc_fight_details.csv",
            "ufc_fight_results.csv",
            "ufc_fight_stats.csv",
            "ufc_fighter_details.csv",
            "ufc_fighter_tott.csv"
        ]

        for fname in files:
            response = requests.get(
                'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/refs/heads/main/' + fname)
            with open(_raw_data_path(fname), 'wb') as f:
                f.write(response.content)

    def process_raw_data(self):
        """
        Manipulate raw csv data to fit the constraints of our database.
        """
        logger.debug("Processing raw UFC data...")

        self.process_raw_fighter_data()
        self.process_raw_event_data()
        self.process_raw_fight_data()
        self.process_raw_fight_stats()
        self.cleanup_raw_data()

        logger.debug("Completed processing raw UFC data")

    def process_raw_fighter_data(self):
        """
        Combines raw UFC fighter details and tail of the tape (tott) data.
        """
        df_details = pd.read_csv(_raw_data_path("ufc_fighter_details.csv"))
        df_tott = pd.read_csv(_raw_data_path("ufc_fighter_tott.csv"))

        # Outer join to keep all records
        combined_df = pd.merge(df_details, df_tott, on='URL', how='outer')

        if 'FIGHTER' in combined_df.columns:
            combined_df = combined_df.drop('FIGHTER', axis=1)

        combined_df = combined_df.replace('--', '')

        combined_df.to_csv(_out_data_path("fighters.csv"), index=False)

    def process_raw_event_data(self):
        """
        Formats raw event details data.
        """
        df_events = pd.read_csv(_raw_data_path("ufc_event_details.csv"))

        df_events.rename(columns={'EVENT': 'NAME'}, inplace=True)

        df_events.to_csv(_out_data_path("events.csv"), index=False)

    def process_raw_fight_data(self):
        """
        Combines raw fight details and results.
        """
        df_fight_details = pd.read_csv(_raw_data_path("ufc_fight_details.csv"))
        df_fight_results = pd.read_csv(_raw_data_path("ufc_fight_results.csv"))

        combined_df = pd.merge(
            df_fight_details, df_fight_results, on='URL', how='outer')

        combined_df = combined_df.drop(columns=['EVENT_x', 'BOUT_x'])
        combined_df.rename(columns={'EVENT_y': 'EVENT',
                                    'BOUT_y': 'BOUT'}, inplace=True)

        combined_df['URL'] = combined_df.pop('URL')

        combined_df.to_csv(_out_data_path("fights.csv"), index=False)

    def process_raw_fight_stats(self):
        """
        Formats and manipulates raw fight stats data.
        """
        df_fight_stats = pd.read_csv(_raw_data_path("ufc_fight_stats.csv"))

        rename_cols = {
            'KD': 'KNOCKDOWNS',
            'SIG.STR.': 'SIGSTRIKES',
            'SIG.STR. %': 'SIGSTRIKESPERCENT',
            'TOTAL STR.': 'TOTALSTRIKES',
            'TD': 'TAKEDOWNS',
            'TD %': 'TAKEDOWNSPERCENT',
            'SUB.ATT': 'SUBMISSIONATTEMPTS',
            'REV.': 'REVERSALS',
            'CTRL': 'CONTROLTIME',
            'HEAD': 'HEADSTRIKES',
            'BODY': 'BODYSTRIKES',
            'LEG': 'LEGSTRIKES'
        }

        # Rename cols
        df_fight_stats.rename(columns=rename_cols, inplace=True)

        # Remove 'Round {x}' text from ROUND col
        df_fight_stats['ROUND'] = df_fight_stats['ROUND'].str.replace(
            'Round ', '', regex=False)

        # Convert any blank control time values '--' to zeroes
        df_fight_stats['CONTROLTIME'] = df_fight_stats['CONTROLTIME'].str.replace(
            '--', '0:00', regex=False)

        # Convert control time to a total number of seconds
        df_fight_stats['CONTROLTIME'] = df_fight_stats['CONTROLTIME'].apply(
            _parse_time)

        # Extract '{x} of {y}' stats into separate columns
        df_fight_stats[['SIGSTRIKESHIT', 'SIGSTRIKESATTEMPTED']
                       ] = df_fight_stats['SIGSTRIKES'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('SIGSTRIKES', axis=1, inplace=True)
        df_fight_stats.drop('SIGSTRIKESPERCENT', axis=1, inplace=True)

        df_fight_stats[['TOTALSTRIKESHIT', 'TOTALSTRIKESATTEMPTED']
                       ] = df_fight_stats['TOTALSTRIKES'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('TOTALSTRIKES', axis=1, inplace=True)

        df_fight_stats[['TAKEDOWNSHIT', 'TAKEDOWNSATTEMPTED']
                       ] = df_fight_stats['TAKEDOWNS'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('TAKEDOWNS', axis=1, inplace=True)
        df_fight_stats.drop('TAKEDOWNSPERCENT', axis=1, inplace=True)

        df_fight_stats[['HEADSTRIKESHIT', 'HEADSTRIKESATTEMPTED']
                       ] = df_fight_stats['HEADSTRIKES'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('HEADSTRIKES', axis=1, inplace=True)

        df_fight_stats[['BODYSTRIKESHIT', 'BODYSTRIKESATTEMPTED']
                       ] = df_fight_stats['BODYSTRIKES'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('BODYSTRIKES', axis=1, inplace=True)

        df_fight_stats[['LEGSTRIKESHIT', 'LEGSTRIKESATTEMPTED']
                       ] = df_fight_stats['LEGSTRIKES'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('LEGSTRIKES', axis=1, inplace=True)

        df_fight_stats[['DISTANCEHIT', 'DISTANCEATTEMPTED']
                       ] = df_fight_stats['DISTANCE'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('DISTANCE', axis=1, inplace=True)

        df_fight_stats[['CLINCHHIT', 'CLINCHATTEMPTED']
                       ] = df_fight_stats['CLINCH'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('CLINCH', axis=1, inplace=True)

        df_fight_stats[['GROUNDHIT', 'GROUNDATTEMPTED']
                       ] = df_fight_stats['GROUND'].str.extract(r'(\d+) of (\d+)')
        df_fight_stats.drop('GROUND', axis=1, inplace=True)

        df_fight_stats.to_csv(_out_data_path("fight_stats.csv"), index=False)

    def cleanup_raw_data(self):
        """
        Clean up various inconsistencies and performs a final formatting pass on all raw data.
        """

        files = [
            _out_data_path(f) for f in [
                'fighters.csv', 'events.csv', 'fights.csv', 'fight_stats.csv'
            ]
        ]

        for file in files:
            if os.path.exists(file):
                df = pd.read_csv(file)

                # Lowercase headers
                df.columns = [col.lower() for col in df.columns]
                # Strip whitespace from strings
                df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
                # Remove double-spaces
                df = df.map(lambda x: re.sub(r'\s+', ' ', x.strip())
                            if isinstance(x, str) else x)
                # Normalize "vs" to "vs."
                df = df.map(lambda x: re.sub(r"\bvs(?!\.)", "vs.", x)
                            if isinstance(x, str) else x)
                df.to_csv(file, index=False)

    def load_database(self):
        """
        Load entities into the database from the processed UFC data.
        """
        logger.debug(
            'Beginning to insert entities into database from processed UFC data...')
        self.load_events()
        self.load_fighters()
        self.load_fights()
        self.load_fight_stats()

    def load_events(self):
        """
        Create and save event entities to the database.
        """
        logger.debug("Loading events...")

        df_events = pd.read_csv(_out_data_path("events.csv"))

        existing_events = set(Event.objects.values_list("url", flat=True))

        new_events = [
            Event(
                name=d["name"],
                date=_parse_date(d['date']),
                location=d['location'],
                url=d['url']
            ) for _, d in df_events.iterrows()
            if d['url'] not in existing_events
        ]

        Event.objects.bulk_create(new_events)

        logger.info(f"inserted {len(new_events)} new event(s)")

    def load_fighters(self):
        """
        Create and save fighter entities to the database.
        """
        logger.debug("Loading fighters...")

        df_fighters = pd.read_csv(_out_data_path("fighters.csv"))
        df_fighters.replace({np.nan: None}, inplace=True)

        existing_fighters = set(Fighter.objects.values_list("url", flat=True))

        new_fighters = [
            Fighter(
                first_name=d["first"],
                last_name=d['last'],
                nickname=d['nickname'],
                height=d['height'],
                weight=d['weight'],
                reach=d['reach'],
                stance=d['stance'],
                dob=_parse_date(d['dob']),
                url=d['url']
            ) for _, d in df_fighters.iterrows()
            if d['url'] not in existing_fighters
            # TODO: log this case
            and d['first'] is not None
            and d['last'] is not None
        ]

        Fighter.objects.bulk_create(new_fighters)

        logger.info(f"inserted {len(new_fighters)} new event(s)")

    def load_fights(self):
        """
        Create and save fight entities to the database.
        """
        logger.debug("Loading fights...")

        df_fights = pd.read_csv(_out_data_path("fights.csv"))
        df_fights.replace({np.nan: None}, inplace=True)

        existing_fights = set(Fight.objects.values_list("url", flat=True))

        # Group fight data by event name
        new_fights: dict[str, list[Any]] = defaultdict(list)
        for f in [d for _, d in df_fights.iterrows()
                  if d["url"] not in existing_fights]:
            new_fights[f["event"]].append(f)

        for event_name, fights_data in new_fights.items():
            logger.debug(
                f"Preparing to create {len(fights_data)} fight(s) for event: {event_name}")

            event_entity = Event.objects.get(name=event_name)
            if not event_entity:
                logger.warning(
                    f"Skipping creation of {len(fights_data)} fight(s), could not locate event with name: {event_name}")
                continue

            new_fight_entities = [
                Fight(
                    event=event_entity,
                    bout=d['bout'],
                    outcome=d['outcome'],
                    weight_class=d['weightclass'],
                    method=d['method'],
                    round=d['round'],
                    time=d['time'],
                    time_format=d['time format'],
                    referee=d['referee'],
                    details=d['details'],
                    url=d['url']
                ) for d in fights_data
            ]

            Fight.objects.bulk_create(new_fight_entities)

    def load_fight_stats(self):
        """
        Create and save fightstat entities to the database.
        """
        logger.debug("Loading fight stats...")

        df_fight_stats = pd.read_csv(_out_data_path("fight_stats.csv"))
        df_fight_stats.replace({np.nan: None}, inplace=True)

        # Group stats by { event: bout: fighter: [stats] }
        # Looking up fights by bout name only is not reliable since there could be multiple
        # instances of the same matchup (i.e. "Khabib Nurmagomedov vs. Conor McGregor")
        stats_data_grouped: dict[str, dict[str, dict[str, list[Any]]]] = {}
        for (event, bout, fighter), group in df_fight_stats.groupby(["event", "bout", "fighter"]):
            stats_data_grouped.setdefault(event, {}).setdefault(
                bout, {})[fighter] = group.to_dict(orient="records")

        # Set up efficient lookup for fighters
        fighters_cache: dict[str, Fighter] = {}

        def get_fighter(name: str):
            # Check cache first
            fighter = fighters_cache.get(name)
            if fighter:
                return fighter

            # Query database for fighter by full name
            try:
                fighter = Fighter.objects.annotate(full_name_q=Concat(
                    'first_name', Value(' '), 'last_name')).get(full_name_q__iexact=name)
            except Fighter.MultipleObjectsReturned:
                # Currently fight stats only identify the fighter by name, so if multiple fighters share
                # the same full name, there is no way to distinguish them
                logger.warning(
                    f'Query returned multiple fighters with name: {name}')
                return
            except:
                logger.warning(f'Could not locate fighter with name: {name}')
                return

            fighters_cache[name] = fighter
            return fighter

        for event_name, fights_data in stats_data_grouped.items():
            event_entity = Event.objects.prefetch_related(
                "fights").get(name=event_name)

            # Save fight stats in batches per event
            new_stats: list[FightStat] = []

            # Iterate over the fight entities fetched with the event
            for fight_entity in event_entity.fights.all():
                # Find the fight in the raw data
                stats_data = fights_data.get(fight_entity.bout)

                if stats_data is None:
                    continue

                # Create stat entities for each fighter
                for fighter_name, fighter_stats_data in stats_data.items():
                    fighter_entity = get_fighter(fighter_name)

                    if not fighter_entity:
                        logger.warning(
                            f'Could not locate fighter: "{fighter_name}", skipping creation of {len(fighter_stats_data)} fight stats')
                        continue

                    new_stats_for_fighter = [FightStat(
                        fight=fight_entity,
                        fighter=fighter_entity,
                        knockdowns=d['knockdowns'],
                        submission_attempts=d['submissionattempts'],
                        reversals=d['reversals'],
                        control_time=d['controltime'],
                        takedowns=d['takedownshit'],
                        takedowns_attempted=d['takedownsattempted'],
                        total_strikes=d['totalstrikeshit'],
                        total_strikes_attempted=d['totalstrikesattempted'],
                        sig_strikes=d['sigstrikeshit'],
                        sig_strikes_attempted=d['sigstrikesattempted'],
                        head_strikes=d['headstrikeshit'],
                        head_strikes_attempted=d['headstrikesattempted'],
                        body_strikes=d['bodystrikeshit'],
                        body_strikes_attempted=d['bodystrikesattempted'],
                        leg_strikes=d['legstrikeshit'],
                        leg_strikes_attemped=d['legstrikesattempted'],
                        distance_strikes=d['distancehit'],
                        distance_strikes_attempted=d['distanceattempted'],
                        clinch_strikes=d['clinchhit'],
                        clinch_strikes_attempted=d['clinchattempted'],
                        ground_strikes=d['groundhit'],
                        ground_strikes_attemped=d['groundattempted']
                    ) for d in fighter_stats_data]

                    logger.debug(
                        f"Creating {len(new_stats_for_fighter)} stats for {fighter_entity}")

                    new_stats.extend(new_stats_for_fighter)

            logger.debug(f"Creating {len(new_stats)} stats for {event_name}")
            FightStat.objects.bulk_create(new_stats)
