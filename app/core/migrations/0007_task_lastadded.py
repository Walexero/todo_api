# Generated by Django 4.2.5 on 2023-10-30 15:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_todo_completed"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="lastAdded",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
