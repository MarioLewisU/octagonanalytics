from django.db import models
from events.models import Event
from fighters.models import Fighter

# Create your models here.


class Fight(models.Model):
    """
    Represents information regarding an entire fight (or bout) that occurred in an `Event`.
    """

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="fights"
    )

    bout = models.CharField(max_length=128)
    outcome = models.CharField(max_length=8)
    weight_class = models.CharField(max_length=128)
    method = models.CharField(max_length=32)
    round = models.IntegerField()
    time = models.CharField(max_length=8)
    time_format = models.CharField(max_length=32)
    referee = models.CharField(max_length=32, null=True)
    details = models.CharField(max_length=256, null=True)
    url = models.CharField(max_length=128)

    def __str__(self):
        return self.bout


class FightStat(models.Model):
    """
    Represents statistics for a `Fighter` in a single round of a `Fight`.
    """

    fight = models.ForeignKey(
        Fight,
        on_delete=models.CASCADE,
        related_name="stats"
    )
    fighter = models.ForeignKey(
        Fighter,
        on_delete=models.CASCADE,
        related_name="stats"
    )

    knockdowns = models.IntegerField()
    submission_attempts = models.IntegerField()
    reversals = models.IntegerField()
    control_time = models.IntegerField()
    takedowns = models.IntegerField()
    takedowns_attempted = models.IntegerField()

    total_strikes = models.IntegerField()
    total_strikes_attempted = models.IntegerField()
    sig_strikes = models.IntegerField()
    sig_strikes_attempted = models.IntegerField()
    head_strikes = models.IntegerField()
    head_strikes_attempted = models.IntegerField()
    body_strikes = models.IntegerField()
    body_strikes_attempted = models.IntegerField()
    leg_strikes = models.IntegerField()
    leg_strikes_attemped = models.IntegerField()
    distance_strikes = models.IntegerField()
    distance_strikes_attempted = models.IntegerField()
    clinch_strikes = models.IntegerField()
    clinch_strikes_attempted = models.IntegerField()
    ground_strikes = models.IntegerField()
    ground_strikes_attemped = models.IntegerField()

    def __str__(self):
        return f"{self.fighter} stats for {self.fight.bout}: round {self.fight.round}"
