# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-30 13:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Visit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(editable=False)),
                ('page', models.CharField(max_length=255)),
                ('ip', models.CharField(max_length=20)),
                ('ua', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=128)),
                ('referrer', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('-date',),
            },
        ),
    ]
