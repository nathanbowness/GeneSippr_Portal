# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('SilentD', '0002_project_reference2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='reference2',
        ),
    ]
