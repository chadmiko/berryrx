from genericpath import samestat
import pandas as pd 

CURRENT_PLAN_YEAR = 2023

plan_info_path = r'~/Downloads/resdac/files/plan information  20221130.txt'
_plans = pd.read_csv(plan_info_path, sep='|',  
            encoding='ISO-8859-1', 
            dtype={ 'CONTRACT_ID':'str', 
                    'PLAN_ID':'str', 
                    'SEGMENT_ID':'int', 
                    'FORMULARY_ID':'str', 
                    'COUNTY_CODE': 'str',
                    'PDP_REGION_CODE': 'str'})
# create full Plan Code column e.g. 'H3916-035-1' ... HM Complete Blue '1' Segment
# requires proper dtype on `plans` import
# NOTE: don't use lambda fn with apply(), takes forever
_plans['PLAN_CODE'] = _plans["CONTRACT_ID"]+ "-" + _plans["PLAN_ID"]+ "-" + _plans["SEGMENT_ID"].map(str)

# Read geographic file b/c CMS uses special SSA County codes (not FIPS)
geo_path = r'/Users/chadmiko/Downloads/resdac/files/geographic locator file 20221130.txt'
_geo = pd.read_csv(geo_path, sep='|', encoding='ISO-8859-1', 
            dtype={ 'COUNTY_CODE':'str',
                    'PDP_REGION_CODE': 'str'})

_formulary_basic = None


# Plan ID is the hyphenated CMS Plan ID consisting of:
# - Contract ID
# - Plan ID
# - Segment ID
# eg:  'H3916-035-1'  # HM Complete Blue Distinct PPO ($25)
# This returns multiple rows of data all having saving PLAN_CODE
def get_plan_by_id(plan_id):
    r = _plans.loc[_plans.PLAN_CODE == plan_id]
    return r

###
# 
# Must pass in 'pdp_region_code' to get PDP-only plans
# 'exclude_pdp' (bool): Optional - set True to exclude PDP plans
#
def get_plans(**kwargs):
    opts = {}
    plan_code = kwargs.pop('plan_code', None)
    county_code = kwargs.pop('county_code', None)

    if plan_code:
        opts['plan_code'] = plan_code
    if county_code:
        opts['county_code'] = county_code 
    if 'pdp_region_code' in kwargs:
        opts['pdp_region_code'] = kwargs.pop('pdp_region_code', None)
        return get_pdp_plans(opts)
    
    return get_mapd_plans(opts)

####
# 'county_code' (str):  uses the SSA County Id's, not FIPS
# 'plan_code' (str):  canoncial CMS Contract ID - Plan ID - Segment ID (e.g. H3502-046-1)
# 'include_snp' (optional) list<int64> or bool: 0=Non SNP(default), 1=C-SNP, 2=D-SNP, 3=I-SNP  
def get_mapd_plans(opts={}):
    query = []

    if 'county_code' in opts:
        county_code = opts['county_code']
        if type(county_code) == str:
            query.append('(COUNTY_CODE == "' + county_code + '")')
        elif type(county_code) == list:
            raise NotImplementedError('no lists to county_code yet')
            #query.append([f"(COUNTY_CODE in {opts['county_code']})"])

    if 'plan_code' in opts:
        query.append('(PLAN_CODE == "' + str(opts['plan_code']) + '")')
    
    if 'exclude_pdp' in opts:
        pass
        #_plans.PDP_REGION_CODE.isnull())

    if 'include_snp' in opts:
        if type(opts['include_snp']) == bool:
            if True == opts['include_snp']:
                pass # nothing to add or subtract here
            else: # non-standard way to explicitly exclude all SNP types
                query.append('(SNP == 0)')
        else:  # include specific SNP types as passed in an array
            snp_query = ''
            for i in opts['include_snp']:
                snp_query.append(f"(SNP == {i})")
            query.append( f"({' | '.join(snp_query)})")
    else:
        query.append('(SNP == 0)')

    if len(query) > 0:
        qs = ' & '.join(query)
        return _plans.query(qs)
    else:
        return _plans

####
# 'pdp_region_code' (str): uses the CMS PDP_REGION_CODE which includes a prefix '0' i.e. '06'
def get_pdp_plans(opts={}):
    query = []

    if 'pdp_region_code' in opts:
        region_code = opts['pdp_region_code']
        if type(region_code) == str:
            query.append('(PDP_REGION_CODE == "' + region_code + '")')
        elif type(region_code) == list:
            raise NotImplementedError('no lists to region_code yet')
            #query.append(['PDP_REGION_CODE in "' + opts['pdp_region_code'] +'"'])

    if 'plan_code' in opts:
        query.append('(PLAN_CODE == "' + opts['plan_code'] + '")')

    if len(query) > 0:
        qs = ' & '.join(query)
        print(query)
        return _plans.query(qs)
    else:
        return _plans

####
# Get a list of plan codes 
# @see `get_plans` for options/arguments
# @returns `list<str>` 
def get_plan_codes(**kwargs):
    plans = get_plans(**kwargs)
    return list(plans.PLAN_CODE.unique())


def _load_formulary():
    global _formulary_basic
    if type(_formulary_basic) != pd.core.frame.DataFrame:
        f_basic_path = r'/Users/chadmiko/Downloads/resdac/files/basic drugs formulary file  20221130.txt'
        formulary = pd.read_csv(f_basic_path, sep='|', encoding='ISO-8859-1', 
                dtype={ 'FORMULARY_ID':'str', 
                        'FORMULARY_VERSION':'str',
                        'CONTRACT_YEAR':'str',
                        'RXCUI':'str', 
                        'NDC':'str',
                        'QUANTITY_LIMIT_AMOUNT':'str'})
        _formulary_basic = formulary
  
# Returns a special struct having:
# - formulary_id (str):  key of this table and FK into Plans data
# - version (str):  the version this result represents as data contains all versions
# - drugs (Dict<pandas.Series>): keyed by Tier Value, containing all drugs in that tier as a Pandas NamedTuple obj
def get_plan_formulary(**kwargs):
    global _formulary_basic
    _load_formulary()

    result = {
        'formulary_id': '',
        'version': '',
        'drugs': [],
        #rxcuis: [], #Set
        #ndcs: [], #Set
    }

    if 'formulary_id' in kwargs:
        formulary_id = kwargs['formulary_id'] 
    if 'plan_code' in kwargs:
        plan = get_plan_by_id(kwargs['plan_code'])
        formulary_id = plan.FORMULARY_ID.unique().tolist()[0]
    
    f_all_versions = _formulary_basic.loc[_formulary_basic.FORMULARY_ID == formulary_id]

    if 'version' in kwargs:
        # try to find the requested version
        latest_version = f_all_versions.loc[f_all_versions.FORMULARY_VERSION == str(kwargs['version'])]
    else:
        #find latest version
        latest_version = str(max([int(v) for v in f_all_versions.FORMULARY_VERSION.unique()]))

    formulary_version = f_all_versions.loc[f_all_versions.FORMULARY_VERSION == latest_version]
    
    for item in formulary_version.itertuples():
        result['drugs'].append(item)
    result['version'] = latest_version
    result['formulary_id'] = formulary_id
    return result


###
# given a DF of Plans, return list of unique formulary ids
def get_forumlary_ids(plans):
    return plans.FORMULARY_ID.unique.tolist()
