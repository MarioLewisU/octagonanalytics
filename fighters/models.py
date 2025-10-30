from typing import TYPE_CHECKING
from django.db import models

if TYPE_CHECKING:
    from fights.models import FightStat

# Create your models here.


class Fighter(models.Model):
    """
    Represents general information about a fighter in the UFC.
    """

    if TYPE_CHECKING:
        stats: models.Manager["FightStat"]

    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    nickname = models.CharField(max_length=32, null=True)
    height = models.CharField(max_length=16, null=True)
    weight = models.CharField(max_length=16, null=True)
    reach = models.CharField(max_length=16, null=True)
    stance = models.CharField(max_length=16, null=True)
    dob = models.DateField(null=True)
    url = models.CharField(max_length=128)

    @property
    def full_name(self):
        """Returns the fighters full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name_with_nickname(self):
        """Returns the fighters full name including their nickname if available"""
        if self.nickname is not None:
            return f"{self.first_name} '{self.nickname}' {self.last_name}"
        return self.full_name

    def __str__(self):
        return self.full_name_with_nickname
