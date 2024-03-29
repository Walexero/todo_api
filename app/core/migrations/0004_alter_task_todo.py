# Generated by Django 4.2.5 on 2023-10-16 20:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_task"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="todo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks",
                to="core.todo",
            ),
        ),
    ]
