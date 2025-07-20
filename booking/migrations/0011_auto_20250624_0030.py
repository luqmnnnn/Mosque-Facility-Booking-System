from django.db import migrations
import uuid

def generate_receipt_numbers(apps, schema_editor):
    Payment = apps.get_model('booking', 'Payment')
    for payment in Payment.objects.all():
        payment.receipt_number = str(uuid.uuid4())
        payment.save()

class Migration(migrations.Migration):
    dependencies = [
        ('booking', '0010_payment_receipt_file_payment_receipt_number'),
    ]

    operations = [
        migrations.RunPython(generate_receipt_numbers),
    ]
