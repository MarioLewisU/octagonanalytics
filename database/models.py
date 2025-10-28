from django.db import models

# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=128)
    date = models.DateField()
    location = models.CharField(max_length=64)
    url = models.CharField(max_length=128)

class Fighter(models.Model):
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    nickname = models.CharField(max_length=32, null=True)
    height = models.CharField(max_length=16, null=True)
    weight = models.CharField(max_length=16, null=True)
    reach = models.CharField(max_length=16, null=True)
    stance = models.CharField(max_length=16, null=True)
    dob = models.DateField(null=True)
    url = models.CharField(max_length=128)

class Fight(models.Model):
    event = models.ForeignKey(Event)

    bout = models.CharField(max_length=128)
    outcome = models.CharField(max_length=8)
    weight_class = models.CharField(max_length=128)
    method = models.CharField(max_length=32)
    round = models.IntegerField()
    time = models.CharField(max_length=8)
    time_format = models.CharField(max_length=32)
    referee = models.CharField(max_length=32)
    details = models.CharField(max_length=256)
    url = models.CharField(max_length=128)

class FightStat(models.Model):
    fight = models.ForeignKey(Fight)
    fighter = models.ForeignKey(Fighter)

    knockdowns = models.IntegerField()
    submission_attempts = models.IntegerField()
    reversals = models.IntegerField()
    control_time = models.CharField(max_length=8)
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
    