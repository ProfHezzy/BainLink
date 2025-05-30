# Generated by Django 5.2.1 on 2025-05-27 14:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_notification_content_type_notification_object_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ['-points'], 'verbose_name': 'User Profile', 'verbose_name_plural': 'User Profiles'},
        ),
        migrations.AlterModelOptions(
            name='skill',
            options={'ordering': ['name'], 'verbose_name': 'Skill', 'verbose_name_plural': 'Skills'},
        ),
        migrations.RemoveField(
            model_name='skill',
            name='profile',
        ),
        migrations.AlterField(
            model_name='profile',
            name='profile_pic',
            field=models.ImageField(blank=True, null=True, upload_to='profiles/%Y/%m/%d/'),
        ),
        migrations.RemoveField(
            model_name='profile',
            name='skills',
        ),
        migrations.AlterField(
            model_name='profile',
            name='subjects',
            field=models.ManyToManyField(blank=True, related_name='profiles_studying', to='core.subject'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='profile', serialize=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='skill',
            name='name',
            field=models.CharField(help_text="A specific skill (e.g., 'Python', 'Public Speaking').", max_length=50, unique=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='skills',
            field=models.ManyToManyField(blank=True, help_text='Select or add relevant skills.', related_name='profiles_with_skill', to='core.skill'),
        ),
    ]
