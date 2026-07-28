
from django.db import models

class Level(models.IntegerChoices):
        VIEW = 1
        EDIT = 2