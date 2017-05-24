# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('SilentD', '0003_remove_project_reference2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='user',
            field=models.CharField(default=' ', max_length=200),
        ),
        migrations.AlterField(
            model_name='profile',
            name='lab',
            field=models.CharField(blank=True, choices=[(1, 'St-Johns'), (2, 'Dartmouth'), (3, 'Charlottetown'), (4, 'St-Hyacinthe'), (5, 'Longeuil'), (6, 'Fallowfield'), (7, 'Carling'), (8, 'Greater Toronto Area'), (9, 'Winnipeg'), (10, 'Saskatoon'), (11, 'Calgary'), (12, 'Lethbridge'), (13, 'Burnaby'), (14, 'Sidney'), (15, 'Other')], max_length=100),
        ),
        migrations.AlterField(
            model_name='profile',
            name='rank',
            field=models.CharField(choices=[('Diagnostic', 'Diagnostic'), ('Research', 'Research'), ('Manager', 'Manager'), ('Quality', 'Quality'), ('Super', 'Super')], default='Diagnostic', max_length=100),
        ),
        migrations.AlterField(
            model_name='project',
            name='geneseekr_results',
            field=models.FileField(blank=True, upload_to='', null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='srst2_results',
            field=models.FileField(blank=True, upload_to='', null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='user',
            field=models.CharField(default=' ', max_length=200),
        ),
    ]
