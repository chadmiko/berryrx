from django.db import models 

class RxcuiNdc(models.Model):
    rxcui = models.PositiveBigIntegerField()
    ndc = models.CharField(max_length=20)

    class Meta:
        unique_together = (("rxcui", "ndc"),)

