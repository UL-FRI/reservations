# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NRequirements',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('n', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NResources',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('n', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Reservable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True)),
                ('type', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'reservables',
                'permissions': (('reserve', 'Create a reservation using this reservable'), ('double_reserve', 'Create an overlapping reservation'), ('manage_reservations', 'Manage reservations using this reservable')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReservableSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('reservables', models.ManyToManyField(related_name=b'reservableset_set', to='reservations.Reservable')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reason', models.CharField(max_length=255, verbose_name='reason')),
                ('start', models.DateTimeField(verbose_name='start')),
                ('end', models.DateTimeField(verbose_name='end')),
                ('owners', models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='owners')),
            ],
            options={
                'permissions': (),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True)),
                ('type', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='reservation',
            name='requirements',
            field=models.ManyToManyField(help_text='Reservation requirements', to='reservations.Resource', verbose_name='resources', through='reservations.NRequirements'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reservation',
            name='reservables',
            field=models.ManyToManyField(to='reservations.Reservable', verbose_name='reservables'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reservable',
            name='resources',
            field=models.ManyToManyField(to='reservations.Resource', through='reservations.NResources'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nresources',
            name='reservable',
            field=models.ForeignKey(to='reservations.Reservable'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nresources',
            name='resource',
            field=models.ForeignKey(to='reservations.Resource'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nrequirements',
            name='reservation',
            field=models.ForeignKey(to='reservations.Reservation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nrequirements',
            name='resource',
            field=models.ForeignKey(to='reservations.Resource'),
            preserve_default=True,
        ),
    ]
