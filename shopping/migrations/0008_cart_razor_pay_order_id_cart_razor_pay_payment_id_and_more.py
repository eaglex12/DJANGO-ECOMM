# Generated by Django 4.2.5 on 2023-10-05 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopping', '0007_billing_details_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='razor_pay_order_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='cart',
            name='razor_pay_payment_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='cart',
            name='razor_pay_signature_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
