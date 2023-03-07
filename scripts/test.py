import pandas as pd 
import urllib.request, json 
from dataclasses import dataclass, field 
from typing import Optional 

### links
'''
https://clincalc.com/DrugStats/Top300Drugs.aspx

All HM Formularies (?) + Monthly Updates:
https://hbcbs.highmarkprc.com/Pharmacy-Program-Formularies/Formulary-Information

HM ACA formulary - name???: 
https://client.formularynavigator.com/Search.aspx?siteCode=6571849149
Download PDF:  https://fm.formularynavigator.com/FBO/9/HCR_Essential_Closed_State_Exchange_2018_Standard.pdf

HM 2023 ACA plans:
https://www.highmark.com/content/dam/digital-marketing/en/highmark/highmarkdotcom/plans/individuals-and-families/2023-ACA-Product-Brochure-WPA.pdf

UPMC 2023 ACA plans:
https://upmc.widen.net/view/pdf/fga8f1mk9d/INF-2023-Sales-Brochure_WEB.doc?t.download=true&u=oid6pr

UPMC 2023 ACA Formulary - Advantage Choice: 
https://upmc.widen.net/view/pdf/halhpywg3c/22IND3217364---Advantage-Choice-2023-formulary_WEB.pdf?t.download=true&u=oid6pr

UPMC List of Forumularies:
https://www.upmchealthplan.com/providers/medical/resources/other/pharmacy.aspx

CostPlusDrugs API Docs: 
https://costplusdrugs.github.io/apidocs/

!!!! THE CMS PART D FILES THAT MAKE THIS ALL WORK !!!
CMS Part D stuff
https://www.cms.gov/research-statistics-data-systems/prescription-drug-plan-formulary-pharmacy-network-and-pricing-information-files-download

CMS Data Leb - UMinn - ResDac
https://resdac.org/cms-data/files/pde/data-documentation

Avalere - Dist of Generic Drugs on Part D Tiers
https://avalere.com/insights/57-of-generic-drugs-are-not-on-2022-part-d-generic-tiers

Helpful List of Health Data APIs:  
https://www.altexsoft.com/blog/drug-data-openfda-dailymed-rxnorm-goodrx/

GET RXCUI Data in UMLS License data?  
https://www.nlm.nih.gov/databases/umls.html

UNDERSTANDING RXCUI Lingo:  https://academic.oup.com/jamia/article/18/4/441/734170

RXCUI Files:  https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html
TERM Types: https://www.nlm.nih.gov/research/umls/rxnorm/docs/appendix5.html

DailyMed API to query by RXCUI:  https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/rxcuis_api.cfm

RxNorm API: https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html
RxNorm browser (switch to simple view if necessary, search by drug name but make sure to get RXCUI's from TTY=SCD entries):
- https://mor.nlm.nih.gov/RxNav/search

'''
BB_DATA_URL = 'https://us-central1-stealth-acquisition-price-tool.cloudfunctions.net/helloWorld'
CP_DATA_URL = 'https://us-central1-costplusdrugs-publicapi.cloudfunctions.net/main'

@dataclass
class Item:
    medication_name: str
    ndc: str
    unit_price: float == 0.0
    # brand_name: Optional[str] = field(default="")
    # strength: Optional[str] = field(default="")
    # slug?


bb_items = {}
cp_items = {}

with urllib.request.urlopen(BB_DATA_URL) as url:
    bb_data = json.load(url)
    for item in bb_data:
        mn = item['itemName']
        up = item['unitCost']
        ndc = item['NDC']
        if ndc not in bb_items:
            bb_items[ndc] = []
        bb_items[ndc].append(Item(mn, ndc, up))


with urllib.request.urlopen(CP_DATA_URL) as url:
    cp_data = json.load(url)['results']
    for item in cp_data:
        mn = item['medication_name']
        up = float(item['unit_price'].replace('$', ''))
        ndc = item['ndc']
        if ndc not in cp_items:
            cp_items[ndc] = []
        cp_items[ndc].append(Item(mn, ndc, up))
    

def get_by_name(partial_str, haystack={}):
    results = []
    for ndc_tuple in haystack.items():
        ndc, items = ndc_tuple 
        for item in items:
            if item.medication_name.lower().startswith(partial_str.lower()):
                results.append(item)
    return results

#### 
# Because NDCs are manufacturer-specific (first 4 digits is in fact the Manufacturer),
# AND CMS data relies on RXCUIs (which are different from NDCs),
# we need a way to input an NDC (usually from pricing data) and get an RXCUI back
# so we can query a plans Formulary using the RXCUI
####

def get_rxcui_from_ndc(ndc):
    # there's also a `status` param available but default is 'active' in the endpoint
    api_url = "https://rxnav.nlm.nih.gov/REST/relatedndc.json?relation=product&ndc=" + str(ndc)
    rxcui = set([])
    with urllib.request.urlopen(api_url) as url:
        data = json.load(url)
        if 'ndcInfoList' in data:
            if 'ndcInfo' in data['ndcInfoList']:
                for item in data['ndcInfoList']['ndcInfo']:
                    rxcui.add(item['rxcui'])
    return list(rxcui)

# Read and import Plan Info file
# NOTE:  Even though all RESDAC data is ASCII encoding, pandas read_csv throws error unless ISO-8859-1 used
plan_info_path = r'~/Downloads/resdac/files/plan information  20221130.txt'
plans = pd.read_csv(plan_info_path, sep='|',  
            encoding='ISO-8859-1', dtype={'CONTRACT_ID':'str', 'PLAN_ID':'str', 'SEGMENT_ID':'int', 
            'FORMULARY_ID':'str', 'COUNTY_CODE': 'str'})

# create full Plan Code column e.g. 'H3916-035-1' HM Complete Blue '1' Segment
# requires proper dtype on `plans` import
# NOTE: don't use lambda fn with apply(), takes forever
plans['PLAN_CODE'] = plans["CONTRACT_ID"]+ "-" + plans["PLAN_ID"]+ "-" + plans["SEGMENT_ID"].map(str)

# Read geographic file b/c CMS uses special SSA County codes (not FIPS)
geo_path = r'/Users/chadmiko/Downloads/resdac/files/geographic locator file 20221130.txt'
geo = pd.read_csv(geo_path, sep='|', encoding='ISO-8859-1', dtype={'COUNTY_CODE':'str'})

# Read formulary file (very SLOW)
# Columns:  'FORMULARY_ID', 'FORMULARY_VERSION', 'CONTRACT_YEAR', 'RXCUI', 'NDC', 'TIER_LEVEL_VALUE', 'QUANTITY_LIMIT_YN', 
#           'QUANTITY_LIMIT_AMOUNT', 'QUANTITY_LIMIT_DAYS', 'PRIOR_AUTHORIZATION_YN', 'STEP_THERAPY_YN'
f_basic_path = r'/Users/chadmiko/Downloads/resdac/files/basic drugs formulary file  20221130.txt'
f_basic = pd.read_csv(f_basic_path, sep='|', encoding='ISO-8859-1', 
                dtype={'FORMULARY_ID':'str', 'FORMULARY_VERSION':'str','CONTRACT_YEAR':'str','RXCUI':'str', 
                    'NDC':'str','QUANTITY_LIMIT_AMOUNT':'str'})

# May have multiple contract years, so be careful
f_basic_years =  list(set(list(f_basic["CONTRACT_YEAR"])))

# Get List of Plans For given SSA County Code
ssa_county_code = '39770'  # Westmoreland County, PA
west_cty_plans = plans.loc[plans['COUNTY_CODE'] == ssa_county_code]

# Get A Plan From List of Plans in Given County
the_plan_code = 'H3916-035-1'  # HM Complete Blue Distinct PPO ($25)
the_plan = west_cty_plans.loc[west_cty_plans["PLAN_CODE"] == the_plan_code]

# Get the Plan's Forumulary ID
f_id = the_plan["FORMULARY_ID"].values[0]

# Get List of Drugs on a Given Plan's Formulary
the_plan_drug_df = f_basic.loc[f_basic["FORMULARY_ID"] == f_id]

# Get a Specific Drug BY RXCUI
rxcui = '966250' # Synthroid 0.1mg Oral Tablet
the_plan_drug_df.loc[the_plan_drug_df["RXCUI"] == '966250']

# GETTING A PDP IS DIFFERENT THAN MAPD PLAN
# Must use PDP_REGION_CODE 
pa_pdp_code = '06'  # geo file does not use the '0' prefix, but plans file does
value_script_code = 'S4802-141-0'
value_script = plans.loc[(plans.PLAN_CODE==value_script_code) & (plans.PDP_REGION_CODE==pa_pdp_code)]
value_script_formulary = f_basic.loc[f_basic.FORMULARY_ID == value_script.FORMULARY_ID.values[0]]



# For comparing to BlueBerry Pricing:  
# - Grab the NDCs from the selected plan's Formulary data
# - Compare the Plan Forumulary's NDCs to NDCs in BlueBerry Price Data 
# - Collect matches into a Dictionary keyed by Formulary Tiers
#    -- Any drugs in Tier 3+ is a target ripe for savings
#    


######
# Comparing a PDP Plan to Blueberry prices
# This is the motherlode where we see cost vs formulary copay/cost-sharing
# TODO: Fix the output path to "just work" whether PDP or MAPD plan
from rxnorm.api import get_ndcs
from rxprices.models import BlueberryRxPriceItem
from rxnorm.resdac import get_plan_formulary
from rxnorm.resdac import get_plan_codes
import csv
pdp_region = '12'
pdp_pc = get_plan_codes(pdp_region_code=pdp_region)
for code in pdp_pc:
    f = get_plan_formulary(plan_code=code)
    formulary_id = f['formulary_id']
    rows = []
    tiers = {1: 1, 2: 2, 3: 3, 4: 3, 5: 5, 6:6, 7:7}
    print("retrieving %s ndcs" % (code))
    for drug in f['drugs']:
        ndcs = get_ndcs(drug.RXCUI)
        for ndc in ndcs:
            record = BlueberryRxPriceItem.objects.filter(ndc=ndc)
            if len(record) > 0:
                record = record[0]
                if record.dispensing_unit_id > 1:
                        uc = record.package_size_qty * record.unit_cost
                else:
                        uc = 30 * record.unit_cost                                    
                rows.append([drug.RXCUI,drug.NDC,record.name,uc,tiers[drug.TIER_LEVEL_VALUE]])
    with open(f"/Users/chadmiko/Documents/Dev/berryrx/{pdp_region}_{code}_{formulary_id}.csv", "w", newline='') as f:
        w = csv.writer(f, delimiter=",")
        for row in sorted(rows, key=lambda drug: drug[-1]):
                w.writerow(row)
    f.close()
       