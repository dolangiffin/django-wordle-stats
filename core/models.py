import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class User(models.Model):
    """
    Custom user model for Wordle stats tracking.
    Simplified version without authentication details for now.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email'], name='users_email_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"


class WordleWord(models.Model):
    """
    Official Wordle puzzle information.
    Each record represents a single day's Wordle puzzle.
    """
    id = models.AutoField(primary_key=True)
    game_date = models.DateField(unique=True, db_index=True)
    wordle_number = models.IntegerField(unique=True, db_index=True)
    word = models.CharField(max_length=5)

    class Meta:
        db_table = 'wordle_words'
        ordering = ['-game_date']
        indexes = [
            models.Index(fields=['game_date'], name='wordle_words_date_idx'),
            models.Index(fields=['wordle_number'], name='wordle_words_num_idx'),
        ]

    def __str__(self):
        return f"Wordle #{self.wordle_number} ({self.game_date}): {self.word}"


class Score(models.Model):
    """
    User scores for Wordle puzzles.
    Immutable once created - no updates allowed to maintain data integrity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scores')
    wordle_word = models.ForeignKey(WordleWord, on_delete=models.CASCADE, related_name='scores')
    guesses = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text='1-6 for successful solve, 7 for DNF'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scores'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'wordle_word'],
                name='unique_user_puzzle'
            )
        ]
        indexes = [
            models.Index(fields=['user'], name='scores_user_idx'),
            models.Index(fields=['wordle_word'], name='scores_puzzle_idx'),
            models.Index(fields=['guesses'], name='scores_guesses_idx'),
        ]

    def __str__(self):
        status = "DNF" if self.guesses == 7 else f"{self.guesses} guesses"
        return f"{self.user.name} - Wordle #{self.wordle_word.wordle_number}: {status}"

    def save(self, *args, **kwargs):
        """Enforce immutability - prevent updates after creation"""
        if self.pk and Score.objects.filter(pk=self.pk).exists():
            raise ValueError("Scores cannot be updated once created")
        super().save(*args, **kwargs)


class UserStatsCache(models.Model):
    """
    Optional performance optimization table.
    Pre-calculated statistics to speed up dashboard loading.
    Add this table when dashboard load time > 500ms or with > 10 active users.
    """
    PERIOD_CHOICES = [
        ('week', 'Weekly'),
        ('month', 'Monthly'),
        ('year', 'Yearly'),
        ('all_time', 'All Time'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stats_cache')
    period_type = models.TextField(choices=PERIOD_CHOICES)
    period_year = models.IntegerField(null=True, blank=True,
                                      help_text='NULL for all_time stats')
    period_value = models.IntegerField(null=True, blank=True,
                                       help_text='Week (1-53) or Month (1-12), NULL for yearly/all_time')

    # Core statistics
    games_played = models.IntegerField(default=0)
    games_solved = models.IntegerField(default=0)
    games_failed = models.IntegerField(default=0)
    total_guesses = models.IntegerField(default=0,
                                       help_text='Sum of all guesses for average calculation')
    average_guesses = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    best_score = models.IntegerField(null=True, blank=True,
                                     help_text='Lowest guess count in period')

    # Guess distribution stored as JSON for flexibility
    # Example: {"1": 5, "2": 12, "3": 20, "4": 15, "5": 8, "6": 3, "7": 2}
    distribution = models.JSONField(default=dict,
                                  help_text='JSON object with guess counts')

    # Competitive stats
    is_winner = models.BooleanField(default=False,
                                   help_text='Won this period against other users')

    # Cache management
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_stats_cache'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'period_type', 'period_year', 'period_value'],
                name='unique_user_period'
            )
        ]
        indexes = [
            models.Index(fields=['user'], name='stats_cache_user_idx'),
            models.Index(fields=['period_type'], name='stats_cache_type_idx'),
            models.Index(fields=['last_updated'], name='stats_cache_updated_idx'),
        ]

    def __str__(self):
        period_desc = f"{self.period_type}"
        if self.period_year:
            period_desc += f" {self.period_year}"
            if self.period_value:
                if self.period_type == 'week':
                    period_desc += f" Week {self.period_value}"
                elif self.period_type == 'month':
                    period_desc += f" Month {self.period_value}"
        return f"{self.user.name} - {period_desc} stats"

    @property
    def cache_is_stale(self):
        """Check if cache needs refreshing (older than 24 hours for recent periods)"""
        if self.period_type == 'all_time':
            # All-time stats can be cached longer
            return (timezone.now() - self.last_updated).days > 7
        elif self.period_year == timezone.now().year:
            # Current year stats should be fresher
            return (timezone.now() - self.last_updated).hours > 24
        else:
            # Historical stats can be cached indefinitely
            return False