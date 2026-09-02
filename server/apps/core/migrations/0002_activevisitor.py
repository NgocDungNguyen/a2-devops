from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActiveVisitor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("visitor_hash", models.CharField(max_length=64, unique=True)),
                ("last_seen", models.DateTimeField(db_index=True)),
            ],
            options={
                "verbose_name": "active visitor",
            },
        ),
    ]
