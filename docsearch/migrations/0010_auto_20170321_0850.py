# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-21 08:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docsearch', '0009_auto_20170321_0843'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searcher',
            name='user_name',
        ),
        migrations.AddField(
            model_name='searcher',
            name='num_of_requests',
            field=models.IntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='searcher',
            name='num_of_visits',
            field=models.IntegerField(db_index=True, default=0),
        ),
    ]