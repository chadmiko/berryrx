from struct import pack
from django.db import models
from django.utils import timezone 

'''
"itemName": "Doxazosin Mesylate 8 Mg Tab",
    "NDC": "16729041501",
    "unitCost": 0.0309,
    "unitAWP": null,
    "PackageSizeQuantity": 100.0,
    "dispensingunitid": 1,
    "dispensingUnitName": "ea",
    "InvoiceCostPerUnit": 3.09,
    "InvoiceID": "DA6E5806-9E42-494D-A066-D8DEC34D9891",
    "ChangedOnUTC": 1666016183130,
    "InvoiceDate": 1665964800000,
    "DosageFormText": "Tablet",
    "cost": 3.09,
    "IsGeneric": 1,
    "recentFlag": "recent",
    "row#": 1,
    "deaschedule": 0,
    "Manufacturer": "Accord Healthca"

    "brand_name": "Flexeril",
      "form": "Tablet",
      "medication_name": "Cyclobenzaprine",
      "ndc": "52817033050",
      "pill_nonpill": "Pill",
      "slug": "cyclobenzaprine-5mg-tablet",
      "strength": "5mg",
      "unit_price": "$0.030",
      "url": "https://costplusdrugs.com/medications/cyclobenzaprine-5mg-tablet/"
'''

class BlueberryRxPriceItem(models.Model):
    date = models.DateField(default=timezone.now)
    name = models.CharField(max_length=200)
    invoice_id = models.CharField(max_length=40)
    ndc = models.CharField(max_length=20)
    unit_cost = models.DecimalField(decimal_places=4, max_digits=12)
    package_size_qty = models.DecimalField(decimal_places=2, max_digits=8)
    cost = models.DecimalField(decimal_places=2, max_digits=8)
    invoice_date = models.PositiveBigIntegerField()
    changed_on_utc = models.PositiveBigIntegerField()
    dispensing_unit_id = models.IntegerField()

    class Meta:
        unique_together = ('invoice_id', 'ndc',)
