from .models import RxcuiNdc
import requests
import logging
from time import sleep
logger = logging.getLogger(__name__)


BASE_URL = "https://rxnav.nlm.nih.gov/REST/"

def get_ndcs(rxcui, skip_db=False):
    url = BASE_URL + f"rxcui/{rxcui}/ndcs.json"
    if not skip_db:
        qs = RxcuiNdc.objects.filter(rxcui=rxcui)
        if len(qs) > 0:
            return [obj.ndc for obj in qs]
    logger.warn('ndcs for rxcui %s not found, calling API ' % rxcui)
    response = requests.get(url)
    print(response, response.status_code)
    
    if response.status_code != 200:
        logger.warn(f"Received response code of {str(response.status_code)} from RxNav API") 
    ndcs = []
    result = response.json()
    print('go to sleep...')
    sleep(2)
    print('awake!')
    try:
        for ndc in result['ndcGroup']['ndcList']['ndc']:
            ndcs.append(ndc)
        if len(ndcs) == 0:
            logger.error('Could not get ndcs for rxcui %s' % str(rxcui))
    except KeyError:
        logger.error(f"rxcui api failed to find rxcui {rxcui} (possible unquantified)")
   
    if not skip_db:
        RxcuiNdc.objects.bulk_create([
            RxcuiNdc(rxcui=rxcui, ndc=ndc)
            for ndc in ndcs
        ])
    return ndcs