# Generated by Django 3.0.5 on 2020-06-09 23:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Displayer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subj', models.CharField(max_length=40)),
                ('content', models.CharField(max_length=400)),
            ],
        ),
    ]