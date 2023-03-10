# Generated by Django 4.1.5 on 2023-01-10 17:04

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BlueberryRxPriceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=200)),
                ('invoice_id', models.CharField(max_length=40)),
                ('ndc', models.CharField(max_length=20)),
                ('unit_cost', models.DecimalField(decimal_places=4, max_digits=12)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=8)),
                ('invoice_date', models.PositiveBigIntegerField()),
                ('changed_on_utc', models.PositiveBigIntegerField()),
                ('dispensing_unit_id', models.IntegerField()),
                ('package_size_qty', models.DecimalField(decimal_places=2, max_digits=6)),
            ],
            options={
                'unique_together': {('invoice_id', 'ndc')},
            },
        ),
    ]
