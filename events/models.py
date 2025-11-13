from typing import TYPE_CHECKING
from django.db import models
from fighters.models import Fighter

if TYPE_CHECKING:
    from fights.models import Fight

# Create your models here.


class Event(models.Model):
    """
    Represents general information regarding an entire UFC event.
    """

    if TYPE_CHECKING:
        fights: models.Manager["Fight"]

    name = models.CharField(max_length=128)
    date = models.DateField()
    location = models.CharField(max_length=64)
    url = models.CharField(max_length=128)

    def __str__(self):
        return self.name

#Added for upcoming bouts on home.html // working finally
class Match(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='matches')
    fighter1 = models.ForeignKey(Fighter, on_delete=models.CASCADE, related_name='fighter1_matches')
    fighter2 = models.ForeignKey(Fighter, on_delete=models.CASCADE, related_name='fighter2_matches')