from django.contrib import admin
from django.db.models import Avg, Count, Sum
from django.utils.html import format_html
from .models import User, WordleWord, Score, UserStatsCache


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model"""
    list_display = ('name', 'email', 'created_at', 'total_games', 'total_guesses', 'average_score')
    list_filter = ('created_at',)
    search_fields = ('name', 'email')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        """Annotate queryset with stats for sorting"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            num_games=Count('scores'),
            sum_guesses=Sum('scores__guesses'),
            avg_score=Avg('scores__guesses')
        )
        return queryset

    def total_games(self, obj):
        """Display total games played by user"""
        return obj.num_games
    total_games.short_description = 'Games Played'
    total_games.admin_order_field = 'num_games'

    def total_guesses(self, obj):
        """Display total guesses by user"""
        return obj.sum_guesses or 0
    total_guesses.short_description = 'Total Guesses'
    total_guesses.admin_order_field = 'sum_guesses'

    def average_score(self, obj):
        """Display user's average score"""
        if obj.avg_score is not None:
            return f"{obj.avg_score:.2f}"
        return "-"
    average_score.short_description = 'Avg Score'
    average_score.admin_order_field = 'avg_score'


@admin.register(WordleWord)
class WordleWordAdmin(admin.ModelAdmin):
    """Admin interface for WordleWord model"""
    list_display = ('wordle_number', 'game_date', 'word', 'players_count', 'average_score')
    list_filter = ('game_date',)
    search_fields = ('word', 'wordle_number')
    ordering = ('-game_date',)
    readonly_fields = ('id',)
    date_hierarchy = 'game_date'

    def get_queryset(self, request):
        """Annotate queryset with average score for sorting"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            avg_score=Avg('scores__guesses'),
            num_players=Count('scores')
        )
        return queryset

    def players_count(self, obj):
        """Display how many users played this puzzle"""
        return obj.num_players
    players_count.short_description = 'Players'
    players_count.admin_order_field = 'num_players'

    def average_score(self, obj):
        """Display average score for this puzzle"""
        if obj.avg_score is not None:
            return f"{obj.avg_score:.2f}"
        return "-"
    average_score.short_description = 'Avg Score'
    average_score.admin_order_field = 'avg_score'


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    """Admin interface for Score model"""
    list_display = ('display_user', 'display_puzzle', 'guesses_display', 'created_at')
    list_filter = ('guesses', 'created_at', 'user')
    search_fields = ('user__name', 'user__email', 'wordle_word__word')
    readonly_fields = ('id', 'created_at', 'user', 'wordle_word', 'guesses')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def display_user(self, obj):
        """Display user name"""
        return obj.user.name
    display_user.short_description = 'User'
    display_user.admin_order_field = 'user__name'

    def display_puzzle(self, obj):
        """Display puzzle info"""
        return f"#{obj.wordle_word.wordle_number} ({obj.wordle_word.game_date})"
    display_puzzle.short_description = 'Puzzle'
    display_puzzle.admin_order_field = 'wordle_word__wordle_number'

    def guesses_display(self, obj):
        """Display guesses with color coding"""
        if obj.guesses == 7:
            return format_html('<span style="color: red;">DNF</span>')
        elif obj.guesses <= 3:
            return format_html('<span style="color: green;">{}</span>', obj.guesses)
        elif obj.guesses <= 5:
            return format_html('<span style="color: orange;">{}</span>', obj.guesses)
        else:
            return format_html('<span style="color: red;">{}</span>', obj.guesses)
    guesses_display.short_description = 'Score'
    guesses_display.admin_order_field = 'guesses'

    def has_add_permission(self, request):
        """Allow adding new scores"""
        return True

    def has_change_permission(self, request, obj=None):
        """Prevent editing existing scores (immutability)"""
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only in development"""
        from django.conf import settings
        return settings.DEBUG


@admin.register(UserStatsCache)
class UserStatsCacheAdmin(admin.ModelAdmin):
    """Admin interface for UserStatsCache model"""
    list_display = ('user_name', 'period_display', 'games_played', 'average_guesses',
                   'is_winner', 'cache_status', 'last_updated')
    list_filter = ('period_type', 'is_winner', 'last_updated')
    search_fields = ('user__name', 'user__email')
    readonly_fields = ('id', 'last_updated', 'distribution_display')
    ordering = ('-last_updated',)

    def user_name(self, obj):
        """Display user name"""
        return obj.user.name
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__name'

    def period_display(self, obj):
        """Display formatted period"""
        period = obj.period_type.title()
        if obj.period_year:
            period += f" {obj.period_year}"
            if obj.period_value:
                if obj.period_type == 'week':
                    period += f" W{obj.period_value}"
                elif obj.period_type == 'month':
                    period += f" M{obj.period_value}"
        return period
    period_display.short_description = 'Period'

    def cache_status(self, obj):
        """Display cache freshness status"""
        if obj.cache_is_stale:
            return format_html('<span style="color: red;">Stale</span>')
        else:
            return format_html('<span style="color: green;">Fresh</span>')
    cache_status.short_description = 'Cache Status'

    def distribution_display(self, obj):
        """Display guess distribution in a readable format"""
        if not obj.distribution:
            return "No data"

        html = "<table style='border-collapse: collapse;'>"
        html += "<tr><th style='padding: 5px; border: 1px solid #ddd;'>Guesses</th>"
        html += "<th style='padding: 5px; border: 1px solid #ddd;'>Count</th></tr>"

        for guesses in range(1, 8):
            count = obj.distribution.get(str(guesses), 0)
            if count > 0:
                html += f"<tr><td style='padding: 5px; border: 1px solid #ddd;'>"
                if guesses == 7:
                    html += "DNF"
                else:
                    html += str(guesses)
                html += f"</td><td style='padding: 5px; border: 1px solid #ddd;'>{count}</td></tr>"

        html += "</table>"
        return format_html(html)
    distribution_display.short_description = 'Guess Distribution'

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of cache entries"""
        return True


# Customize admin site header and title
admin.site.site_header = "Wordle Stats Admin"
admin.site.site_title = "Wordle Stats"
admin.site.index_title = "Dashboard"