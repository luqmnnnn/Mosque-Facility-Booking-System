# Generated by Django 5.2.1 on 2025-06-25 16:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0013_alter_payment_receipt_number"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="booking",
            unique_together=set(),
        ),
    ]
