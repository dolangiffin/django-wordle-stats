import csv
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from core.models import User, WordleWord, Score


# Wordle puzzle #0 started on June 19, 2021
WORDLE_EPOCH = date(2021, 6, 19)


class Command(BaseCommand):
    help = 'Import Wordle data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--words-file',
            default='Wordle Words - Sheet1.csv',
            help='Path to the Wordle words CSV file'
        )
        parser.add_argument(
            '--stats-file',
            default='Wordle Stats - Sheet1(1).csv',
            help='Path to the Wordle stats CSV file'
        )
        parser.add_argument(
            '--words-only',
            action='store_true',
            help='Only import Wordle words (skip scores)'
        )
        parser.add_argument(
            '--scores-only',
            action='store_true',
            help='Only import scores (assumes words and users exist)'
        )

    def handle(self, *args, **options):
        words_file = options['words_file']
        stats_file = options['stats_file']
        words_only = options['words_only']
        scores_only = options['scores_only']

        if not scores_only:
            self.import_words(words_file)

        if not words_only:
            self.import_users_and_scores(stats_file)

        self.stdout.write(self.style.SUCCESS('Import complete!'))

    def import_words(self, filepath):
        """Import Wordle words from CSV"""
        self.stdout.write(f'Importing words from {filepath}...')

        created_count = 0
        skipped_count = 0
        seen_numbers = {}

        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 2:
                    continue

                # Parse puzzle number (format: #365)
                puzzle_str = row[0].strip()
                if not puzzle_str.startswith('#'):
                    continue

                try:
                    puzzle_number = int(puzzle_str[1:])
                except ValueError:
                    self.stdout.write(self.style.WARNING(
                        f'Could not parse puzzle number: {puzzle_str}'
                    ))
                    continue

                word = row[1].strip().upper()

                # Check for duplicate puzzle numbers
                if puzzle_number in seen_numbers:
                    self.stdout.write(self.style.WARNING(
                        f'Duplicate puzzle #{puzzle_number}: '
                        f'"{seen_numbers[puzzle_number]}" and "{word}" - skipping second'
                    ))
                    continue

                seen_numbers[puzzle_number] = word

                # Calculate date from puzzle number
                game_date = WORDLE_EPOCH + timedelta(days=puzzle_number)

                # Create or get the WordleWord
                wordle_word, created = WordleWord.objects.get_or_create(
                    wordle_number=puzzle_number,
                    defaults={
                        'game_date': game_date,
                        'word': word
                    }
                )

                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(
            f'Words: {created_count} created, {skipped_count} already existed'
        )

    def import_users_and_scores(self, filepath):
        """Import users and scores from stats CSV"""
        self.stdout.write(f'Importing users and scores from {filepath}...')

        users_created = 0
        scores_created = 0
        scores_skipped = 0
        errors = 0

        # Known player names (used to distinguish DATE rows from player rows)
        player_names = set()
        users_cache = {}

        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        current_dates = []

        for row in rows:
            if not row or not row[0].strip():
                continue

            first_cell = row[0].strip()

            # Check if this is a DATE header row
            if first_cell == 'DATE':
                # Parse the dates (DD/MM/YYYY format)
                current_dates = []
                for i in range(1, len(row)):
                    date_str = row[i].strip()
                    if date_str:
                        try:
                            day, month, year = date_str.split('/')
                            current_dates.append(date(int(year), int(month), int(day)))
                        except (ValueError, IndexError):
                            current_dates.append(None)
                    else:
                        current_dates.append(None)
                continue

            # This should be a player row
            player_name = first_cell

            if player_name not in player_names:
                player_names.add(player_name)
                # Create user if not exists
                user, created = User.objects.get_or_create(
                    name=player_name,
                    defaults={'email': f'{player_name.lower()}@example.com'}
                )
                users_cache[player_name] = user
                if created:
                    users_created += 1

            user = users_cache.get(player_name)
            if not user:
                user = User.objects.get(name=player_name)
                users_cache[player_name] = user

            # Parse scores for each date
            for i, score_str in enumerate(row[1:], start=0):
                if i >= len(current_dates) or current_dates[i] is None:
                    continue

                score_str = score_str.strip()
                if not score_str:
                    continue

                try:
                    guesses = int(score_str)
                except ValueError:
                    continue

                game_date = current_dates[i]

                # Find the WordleWord for this date
                try:
                    wordle_word = WordleWord.objects.get(game_date=game_date)
                except WordleWord.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'No WordleWord found for date {game_date}'
                    ))
                    errors += 1
                    continue

                # Create score if not exists
                score, created = Score.objects.get_or_create(
                    user=user,
                    wordle_word=wordle_word,
                    defaults={'guesses': guesses}
                )

                if created:
                    scores_created += 1
                else:
                    scores_skipped += 1

        self.stdout.write(f'Users: {users_created} created')
        self.stdout.write(
            f'Scores: {scores_created} created, {scores_skipped} already existed'
        )
        if errors:
            self.stdout.write(self.style.WARNING(f'Errors: {errors}'))
