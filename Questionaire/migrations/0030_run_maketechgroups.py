from django.db import migrations

def make_tech_group(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Technology = apps.get_model("Questionaire", "Technology")
    TechGroup = apps.get_model("Questionaire", "TechGroup")
    for tech in Technology.objects.filter(name__startswith="GRP_"):
        t = TechGroup(technology_ptr=tech)
        t.name = tech.name
        t.short_text = tech.short_text
        t.icon = tech.icon
        t.save()


def reverse_tech_group(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0029_auto_20191007_1732'),
    ]

    operations = [
        migrations.RunPython(make_tech_group, reverse_tech_group),
    ]