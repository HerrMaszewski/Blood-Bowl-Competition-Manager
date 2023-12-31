# Generated by Django 4.2.3 on 2023-07-30 00:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bbm_app', '0002_alter_team_coach'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='primary_skill_categories',
            field=models.ManyToManyField(related_name='primary_players', to='bbm_app.skillcategory'),
        ),
        migrations.AddField(
            model_name='player',
            name='secondary_skill_categories',
            field=models.ManyToManyField(blank=True, related_name='secondary_players', to='bbm_app.skillcategory'),
        ),
    ]
