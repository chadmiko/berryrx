from curses.ascii import isblank
import os
import requests 
from django.utils import timezone
from rxprices.models import BlueberryRxPriceItem
import logging

logger = logging.getLogger(__name__)

BASE_URL = 'https://us-central1-stealth-acquisition-price-tool.cloudfunctions.net/helloWorld'

def parse_record(record):
    model = BlueberryRxPriceItem(
        name = record['itemName'],
        invoice_id= record['InvoiceID'],
        ndc= record['NDC'],
        unit_cost= record['unitCost'],
        package_size_qty =  record['PackageSizeQuantity'],
        cost = record['cost'],
        invoice_date = record['InvoiceDate'],
        changed_on_utc = record['ChangedOnUTC'],
        dispensing_unit_id = record['dispensingunitid'],
    )
    return model

###
# Ping the BlueberryRx Price feed and save 
# new invoice data to DB
# @return tuple(list<PriceItem>, int)
# 
def request_current_prices(skip_db=True):
    # Call the API 
    # retrieve the price data json and return it
    response = requests.get(BASE_URL,
                            params={},
                            headers={'Content-Type': 'application/json'})

    if response.status_code != 200:
        raise ValueError("Received a response code of %d from API (%s)" % (
            response.status_code, response.content))
    
    new_items = []
    for result in response.json():
        model = parse_record(result)
        # Sometimes Invoice ID is missing
        if not (model.invoice_id and model.invoice_id.strip()):
            logger.warn("Skipping %s %s on %s" % (model.name, model.ndc, model.invoice_date))
            continue

        found = BlueberryRxPriceItem.objects.filter(ndc=model.ndc, invoice_id=model.invoice_id)
        if len(found) > 0:
            found = found[0]
            logger.warn("Found existing BB price record %s %s" % (found.ndc, found.invoice_id))
        else:
            model.save()
            new_items.append(model)
            logger.warn("Created new BB Price record %s %s" % (model.ndc, model.invoice_id))

    if len(new_items) == 0:
        logger.warn("Did not find any new price items.")

    return (new_items, len(new_items))