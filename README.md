# Wordle Stats Django

A Django admin dashboard for tracking and analyzing family Wordle game statistics, built with Django and Supabase.

## Features

- Track daily Wordle scores for multiple users
- View comprehensive statistics (weekly, monthly, yearly)
- Admin dashboard for managing users and scores
- Immutable score records (no editing once created)
- Optional performance caching for large datasets
- Support for DNF (Did Not Finish) scores

## Tech Stack

- **Backend**: Django 5.0.1
- **Database**: Supabase (PostgreSQL)
- **Admin Interface**: Django Admin
- **Authentication**: Django Session Auth (upgradeable to Supabase Auth)

## Project Structure

```
WordleStatsDjango/
├── core/                   # Main Django app
│   ├── models.py          # Database models
│   ├── admin.py           # Admin interface configuration
│   └── migrations/        # Database migrations
├── wordle_stats/          # Django project settings
├── database-schema-hybrid.dbml  # Database schema definition
├── supabase_schema.sql    # SQL to create Supabase tables
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── manage.py             # Django management script
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Supabase account ([sign up free](https://supabase.com))
- Git (optional, for version control)

### 2. Clone/Download the Project

```bash
cd /Users/dolangiffin/Documents/Software/WordleStatsDjango
```

### 3. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Supabase

1. Create a new Supabase project at [app.supabase.com](https://app.supabase.com)

2. Once created, go to **Settings > Database** to get your connection details

3. Execute the schema SQL in Supabase:
   - Go to **SQL Editor** in your Supabase dashboard
   - Copy the contents of `supabase_schema.sql`
   - Paste and run it in the SQL Editor

### 5. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your Supabase credentials:
```env
# Django Settings
SECRET_KEY=your-secret-key-here  # Generate a new one for production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase Database Connection
# Find these in Supabase Dashboard > Settings > Database
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-password-here
SUPABASE_DB_HOST=db.xxxxxxxxxxxxx.supabase.co
SUPABASE_DB_PORT=5432

# Supabase API (optional)
# Find these in Supabase Dashboard > Settings > API
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
```

### 6. Initialize Django

```bash
# Create Django migrations
python manage.py makemigrations

# Apply migrations (with --fake-initial since tables exist)
python manage.py migrate --fake-initial

# Create a superuser for admin access
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin` and log in with your superuser credentials.

## Usage

### Adding Users

1. Go to the Admin panel
2. Click on "Users" under the CORE section
3. Click "Add User"
4. Enter name and email
5. Save

### Adding Wordle Words

1. Go to "Wordle words" in the Admin
2. Click "Add Wordle word"
3. Enter:
   - Game date
   - Wordle number (official puzzle number)
   - Word (5-letter solution)
4. Save

### Recording Scores

1. Go to "Scores" in the Admin
2. Click "Add Score"
3. Select:
   - User
   - Wordle word (puzzle)
   - Guesses (1-6 for success, 7 for DNF)
4. Save

**Note**: Scores are immutable - once created, they cannot be edited (only deleted in development mode).

### Viewing Statistics

The admin interface shows:
- Total games and average scores per user
- Player counts and average scores per puzzle
- Color-coded score display (green for good, orange for average, red for poor/DNF)
- Cache status for performance optimization (when enabled)

## Database Schema

The project uses a minimal, normalized schema:

- **users**: Store user information (id, name, email)
- **wordle_words**: Daily puzzle information (date, number, word)
- **scores**: Individual game results (user, puzzle, guesses)
- **user_stats_cache**: Optional caching table for performance

See `database-schema-hybrid.dbml` for detailed schema documentation.

## Importing Historical Data

To import existing spreadsheet data:

1. Export your spreadsheet as CSV
2. Create a Python script using Django's ORM:

```python
import csv
from datetime import datetime
from core.models import User, WordleWord, Score

# Example import script
with open('wordle_data.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Get or create user
        user, _ = User.objects.get_or_create(
            email=row['email'],
            defaults={'name': row['name']}
        )

        # Get or create puzzle
        puzzle, _ = WordleWord.objects.get_or_create(
            wordle_number=int(row['puzzle_number']),
            defaults={
                'game_date': datetime.strptime(row['date'], '%Y-%m-%d').date(),
                'word': row['word']
            }
        )

        # Create score (will fail if duplicate)
        Score.objects.create(
            user=user,
            wordle_word=puzzle,
            guesses=int(row['guesses'])
        )
```

## Performance Optimization

The `user_stats_cache` table is optional and should be added when:
- Dashboard load time exceeds 500ms
- You have more than 10 active users
- You're running complex statistical queries frequently

To enable caching, implement cache refresh logic using Django signals or scheduled tasks.

## Development Tips

### Generate a New Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Check Database Connection

```bash
python manage.py dbshell
```

### Run Django Shell

```bash
python manage.py shell
```

### Create Sample Data

```python
from core.models import User, WordleWord, Score
from datetime import date, timedelta

# Create a test user
user = User.objects.create(name="Test User", email="test@example.com")

# Create a test puzzle
puzzle = WordleWord.objects.create(
    game_date=date.today(),
    wordle_number=1000,
    word="TESTS"
)

# Create a test score
score = Score.objects.create(user=user, wordle_word=puzzle, guesses=4)
```

## Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Add your domain to `ALLOWED_HOSTS`
3. Use a production-grade server (Gunicorn, uWSGI)
4. Set up static file serving (WhiteNoise is included)
5. Use environment-specific settings
6. Enable SSL/HTTPS
7. Set up regular database backups

## Troubleshooting

### "Table already exists" error
Use `python manage.py migrate --fake-initial` if tables were created manually.

### Connection refused
Check that your Supabase database is active and credentials are correct.

### SSL error
Ensure `sslmode=require` is set in database options.

### Admin CSS not loading
Run `python manage.py collectstatic` in production.

## Future Enhancements

- [ ] Public leaderboard views
- [ ] REST API for mobile apps
- [ ] Automated daily stats emails
- [ ] Streak tracking
- [ ] Head-to-head comparisons
- [ ] Export statistics to PDF
- [ ] Integration with official Wordle API (if available)

## Contributing

Feel free to fork this project and submit pull requests for any improvements.

## License

This project is for personal/educational use. Wordle is a trademark of The New York Times Company.