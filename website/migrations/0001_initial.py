# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-13 12:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorName',
            fields=[
                ('name_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('last_searched', models.DateTimeField(blank=True, null=True)),
                ('is_name', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'author_names',
            },
        ),
        migrations.CreateModel(
            name='Cat',
            fields=[
                ('cat_id', models.AutoField(primary_key=True, serialize=False)),
                ('label', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('is_default', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'cats',
            },
        ),
        migrations.CreateModel(
            name='Doc',
            fields=[
                ('doc_id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.SmallIntegerField(blank=True, default=1)),
                ('url', models.URLField(max_length=512)),
                ('urlhash', models.CharField(editable=False, max_length=32, unique=True)),
                ('doctype', models.CharField(choices=[('article', 'article'), ('book', 'book'), ('chapter', 'book chapter'), ('thesis', 'thesis'), ('review', 'review')], default='article', max_length=16)),
                ('filetype', models.CharField(blank=True, max_length=8, null=True)),
                ('filesize', models.IntegerField(blank=True, null=True)),
                ('found_date', models.DateTimeField(blank=True, null=True)),
                ('earlier_id', models.IntegerField(blank=True, null=True)),
                ('authors', models.CharField(blank=True, max_length=255, null=True)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('abstract', models.TextField(blank=True, null=True)),
                ('numwords', models.PositiveIntegerField(blank=True, null=True)),
                ('numpages', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('source_url', models.URLField(blank=True, max_length=512, null=True)),
                ('source_name', models.CharField(blank=True, max_length=255, null=True)),
                ('meta_confidence', models.IntegerField(blank=True, null=True)),
                ('is_paper', models.IntegerField(blank=True, null=True)),
                ('is_philosophy', models.IntegerField(blank=True, null=True)),
                ('content', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'docs',
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('link_id', models.AutoField(primary_key=True, serialize=False)),
                ('url', models.URLField(max_length=512)),
                ('urlhash', models.CharField(editable=False, max_length=32)),
                ('status', models.SmallIntegerField(blank=True, default=0)),
                ('source_id', models.IntegerField()),
                ('found_date', models.DateTimeField()),
                ('last_checked', models.DateTimeField(blank=True, null=True)),
                ('etag', models.CharField(blank=True, max_length=255, null=True)),
                ('filesize', models.IntegerField(blank=True, null=True)),
                ('doc_id', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'links',
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('source_id', models.AutoField(primary_key=True, serialize=False)),
                ('sourcetype', models.CharField(choices=[('personal', 'personal website'), ('repo', 'repository'), ('journal', 'journal'), ('blog', 'weblog')], default='personal', max_length=16)),
                ('url', models.URLField(max_length=512)),
                ('urlhash', models.CharField(editable=False, max_length=32, unique=True)),
                ('status', models.SmallIntegerField(blank=True, default=0)),
                ('found_date', models.DateTimeField()),
                ('last_checked', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(blank=True, max_length=128, null=True)),
                ('default_author', models.CharField(blank=True, max_length=128, null=True)),
            ],
            options={
                'db_table': 'sources',
            },
        ),
        migrations.AlterUniqueTogether(
            name='link',
            unique_together=set([('source_id', 'urlhash')]),
        ),
    ]
