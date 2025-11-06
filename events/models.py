from typing import TYPE_CHECKING
from django.db import models

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