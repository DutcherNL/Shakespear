# In Django, models.py defines the database models. Because there are a lot of models in this particular module
# the models have been seperated over several files instead. These are:
# Base models, where all basic questionaire models are present
# tech_scoring models, where all the scoring relevant models are located
# external_input models, where all code to extract data from other databasesare located.

# This file functions as the root for a branch to seperate the several model files over several file
from .model_files.base_models import *
from .model_files.tech_scoring_models import *
from .model_files.external_input_models import *
from Questionaire import modules







