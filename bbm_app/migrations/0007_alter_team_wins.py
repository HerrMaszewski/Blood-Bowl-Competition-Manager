# Generated by Django 4.2.3 on 2023-08-06 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bbm_app', '0006_alter_player_passing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='wins',
            field=models.IntegerField(default=0),
        ),
    ]
