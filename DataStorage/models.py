from django.db import models
from django.core.exceptions import ValidationError
import re


class StoredDataCodeDeclaration(models.Model):
    name = models.SlugField(max_length=32)
    description = models.CharField(max_length=255)
    code_regex = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class StoredDataCode(models.Model):
    code_type = models.ForeignKey(StoredDataCodeDeclaration, on_delete=models.CASCADE)
    identification_code = models.CharField(max_length=255)

    def clean(self):
        # Validate that the given code adheres the regex structure
        regex = self.code_type.code_regex
        regex_match = re.match(regex, self.identification_code)
        if regex_match is None:
            raise ValidationError("{code} does not match the required regex: {regex}".format(
                code=self.identification_code, regex=regex
            ))

        # Validate that the code type has not changed


    def __str__(self):
        return "{type}: {code}".format(code=self.identification_code, type=self.code_type.name)


class StoredDataDeclaration(models.Model):
    code_type = models.ForeignKey(StoredDataCodeDeclaration, on_delete=models.CASCADE)
    name = models.SlugField(max_length=32)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class StoredDataContent(models.Model):
    code = models.ForeignKey(StoredDataCode, on_delete=models.PROTECT)
    data_declaration = models.ForeignKey(StoredDataDeclaration, on_delete=models.CASCADE)
    content = models.CharField(max_length=255)
    batch = models.ForeignKey(DataBatch, on_delete=models.CASCADE)

    def clean(self):
        # Do not allow entries where the code declaration does not allow the given content type
        if self.data_declaration.code_type != self.code.code_type:
            raise ValidationError("Given data declaration is not allowed for given code type")


class DataBatch(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_lenth=128)


