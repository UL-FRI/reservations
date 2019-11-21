# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomSortOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Used to separate between custom sort orders.', max_length=64, verbose_name='Name of the custom sort order.')),
                ('order', models.TextField(help_text='Comma separated List of reservable ids that determines its sort order')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(related_name=b'reservations_profile', primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('sort_order', models.ForeignKey(verbose_name='Users choosen sort order', to='reservations.CustomSortOrder', help_text='How reservables should be sorted')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='reservation',
            options={},
        ),
    ]
