# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0002_auto_20151001_1916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customsortorder',
            name='order',
            field=models.TextField(default=b'', help_text='Comma separated List of reservable ids that determines its sort order'),
        ),
    ]
