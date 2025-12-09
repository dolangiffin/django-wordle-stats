from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from .models import User, Score


@login_required
def dashboard(request):
    """
    Main stats dashboard view.
    Shows overall statistics and a leaderboard.

    Key Django concept: This is a function-based view (FBV).
    It receives an HTTP request and returns an HTTP response.
    """
    # Get total counts
    total_players = User.objects.count()
    total_games = Score.objects.count()

    # Calculate overall average score (excluding DNF which is 7)
    # Using aggregate() to compute a single value across all rows
    avg_result = Score.objects.filter(guesses__lte=6).aggregate(
        avg_score=Avg('guesses')
    )
    overall_average = avg_result['avg_score']

    # Get leaderboard: top 5 players by average score
    # Using annotate() to compute a value for each row in the group
    # Only count games where the player solved it (guesses <= 6)
    leaderboard = (
        User.objects
        .annotate(
            games_played=Count('scores'),
            avg_score=Avg('scores__guesses', filter=Q(scores__guesses__lte=6))
        )
        .filter(games_played__gt=0)  # Only include users who have played
        .order_by('avg_score')[:5]   # Lower average is better
    )

    # Build the context dictionary to pass to the template
    context = {
        'total_players': total_players,
        'total_games': total_games,
        'overall_average': round(overall_average, 2) if overall_average else None,
        'leaderboard': leaderboard,
    }

    # render() combines a template with the context and returns HttpResponse
    return render(request, 'dashboard.html', context)
