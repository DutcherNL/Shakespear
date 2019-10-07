from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from string import Formatter

from decimal import *

from DataStorage.models import StoredDataCodeDeclaration, StoredDataDeclaration, StoredDataContent
from PageDisplay.models import Information
# Create your models here.

from .model_files.base_models import *
from .model_files.tech_scoring_models import *








