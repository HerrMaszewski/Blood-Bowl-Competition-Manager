# Generated by Django 4.2.3 on 2023-07-30 02:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bbm_app', '0003_player_primary_skill_categories_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='number',
            field=models.IntegerField(),
        ),
    ]