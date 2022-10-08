import json
import logging
import re
from urllib import request
import requests
import urllib.parse

from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

_logger = logging.getLogger(__name__)

RETRY_STRATEGY = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["POST", "HEAD", "GET", "OPTIONS"]
)
ADAPTER = HTTPAdapter(max_retries=RETRY_STRATEGY)
http = requests.Session()
http.mount("https://", ADAPTER)
http.mount("http://", ADAPTER)

HEADERS = {"Content-Type": "application/json"}
BASEURL = '''https://ess.inseta.org.za/Sage300WebApi/v1.0/-/INSETA''' 
# BASEURL = request.env['ir.config_parameter'].sudo().get_param('bulksms.token.id')
USERNAME = 'WEBAPI'
PASSWORD = 'WEBAPI1'
TIMEOUT = 3600


# def _get_all_mandatory_grant_payment():
#     """Returns all mandatory grant payments

#     """

#     params = {
#         '$select':'VendorNumber,FiscalYear,FiscalPeriod,PaymentAmount,PaymentCode,AmountAdjusted,DocumentNumber,PaymentType,DocumentType,InvoiceNumber,PostingDate'
#     }
#     query = urllib.parse.urlencode(params)

#     try:
#         URL = f"{BASEURL}/AP/APPostedPayments?{query}"
#         _logger.info(f'Fetching All Mandatory Grant payments => {URL}')

#         req = requests.get(URL, headers=HEADERS, auth=HTTPBasicAuth(USERNAME, PASSWORD),timeout=TIMEOUT)
#         return req.json()
#     except Exception as ex:
#         _logger.exception(ex)
#         return {
#                 "error": {
#                     "code": "UnexpectedError",
#                     "message": {
#                     "lang": "en-US",
#                     "value": str(ex)
#                     }
#                 }
#             } 

def _create_mandatory_grant_batch(payload):

    try:
        URL = f"{BASEURL}/AP/APPaymentAndAdjustmentBatches"
        _logger.info(f'Creating Mandatory payments => {URL}')

        req = requests.post(URL, data=payload, headers=HEADERS, auth=HTTPBasicAuth(USERNAME, PASSWORD),timeout=TIMEOUT)
        return req.json()
    except Exception as ex:
        _logger.exception(ex)
        return {
                "error": {
                    "code": "UnexpectedError",
                    "message": {
                    "lang": "en-US",
                    "value": str(ex)
                    }
                }
            } 

def _get_mandatory_grant_payments(sdl_no="L540754886", fiscal_yr="2021"):
    """Returns mandatory grant payment for employer in a given financial year

    Args:
        sdl_no (str, required): SDL no of the employer. Eg. "L540754886".
        fiscal_yr (str, required): The financial year. Eg. "2021".

    Returns:
        [json]: json serialized response object
    """

    params = {
        '$filter': f"FiscalYear ge '{fiscal_yr}' and VendorNumber eq '{sdl_no}' ", 
        '$select':'VendorNumber,FiscalYear,FiscalPeriod,PaymentAmount,PaymentCode,AmountAdjusted,DocumentNumber,PaymentType,DocumentType,InvoiceNumber,PostingDate'
    }
    query = urllib.parse.urlencode(params)

    try:
        URL = f"{BASEURL}/AP/APPostedPayments?{query}"
        _logger.info(f'Fetching Mandatory payments for {sdl_no} >= fiscal year {fiscal_yr} => {URL}')

        req = requests.get(URL, headers=HEADERS, auth=HTTPBasicAuth(USERNAME, PASSWORD),timeout=TIMEOUT)
        return req.json()
    except Exception as ex:
        _logger.exception(ex)
        return {
                "error": {
                    "code": "UnexpectedError",
                    "message": {
                    "lang": "en-US",
                    "value": str(ex)
                    }
                }
            } 

def _get_levy_invoices_by_batch(batch_no='187'):
    """Returns list of invoices 

    Args:
        sdl_no ([type]): [description]
    """
    
    #?%24select=BatchNumber%2CInvoices
    params = {'$select':'Invoices'}
    query = urllib.parse.urlencode(params)

    try:
        URL = f"{BASEURL}/AR/ARInvoiceBatches({batch_no})?{query}"
        _logger.info(f'Fetching Invoices For Batch {batch_no} => {URL}')

        req = requests.get(URL, headers=HEADERS, auth=HTTPBasicAuth(USERNAME, PASSWORD),timeout=TIMEOUT)
        return req.json()
    except Exception as ex:
        _logger.exception(ex)
        return {
                "error": {
                    "code": "UnexpectedError",
                    "message": {
                    "lang": "en-US",
                    "value": str(ex)
                    }
                }
            } 


def _get_all_posted_documents():
    """ Returns a list of posted documents for employer with the provided SDL No
        response format {
        "@odata.context": "https://ess.inseta.org.za/Sage300WebApi/v1.0/-/PHADAT/AR/$metadata#ARPostedDocuments(CustomerNumber,BatchNumber,DocumentType)",
        "value": [
            {
                "CustomerNumber": "L010746552",
                "BatchNumber": 62,
                "DocumentType": "CreditNote"
            },
            {
                "CustomerNumber": "L010746552",
                "BatchNumber": 76,
                "DocumentType": "DebitNote"
            },
        }
    Args:
        sdl_no (string): Employer SDL no
    """

    #params = {'$filter': f"CustomerNumber eq '{sdl_no}' ", '$select': 'CustomerNumber,BatchNumber,DocumentType'}
    params = {'$select': 'CustomerNumber,BatchNumber,DocumentType'}

    query = urllib.parse.urlencode(params)
    URL = f"{BASEURL}/AR/ARPostedDocuments?{query}"
    _logger.info(f'Fetching all Posted Documents => {URL}')
    batch_numbers = []
    try:
        req = requests.get(URL, headers=HEADERS, auth=HTTPBasicAuth(USERNAME, PASSWORD),timeout=TIMEOUT)
        response = req.json()
        if req.status_code == 200:
            values = response.get("value")
            # dictfilt = lambda x, y: dict([ (i,x[i]) for i in x if i in set(y)]) 
            # wanted_keys = ("BatchNumber",) 
            # return dictfilt(values, wanted_keys)
            for val in values:
                if val.get('DocumentType') == "DebitNote":
                    batch_numbers.append(val.get('BatchNumber'))

        else:
            """{
                "error": {
                    "code": "InvalidParameters",
                    "message": {
                    "lang": "en-US",
                    "value": "Could not find a property named 'L010746552' on type 'Sage.CA.SBS.ERP.Sage300.AR.WebApi.Models.PostedDocument'."

                    }
                }
            } """
            _logger.error(f'Error: {json.dumps(response.get("error"))}')
    except Exception as ex:
        _logger.exception(ex)


    return list(set(batch_numbers)) #return unique batch numbers


def _get_gl_accounts():
    """Returns list of GL Accounts. The GL account is used for generating the levy history report
    """
    
    #?%24select=BatchNumber%2CInvoices
    #GL/GLAccounts?%24filter=AccountGroupCode%20eq%20'1000'&%24select=Description%2CAccountType%2CStatus%2CAccountNumber%2CAccountGroupCode&%24count=true


    """
        970 admin levy
        990 - Mandatory lev
        Discretionary - 980
        Penalty - 1000 & interest
    """

    ACCOUNT_GROUP_CODE = ("970", "980", "990", "1000" )
    accounts = []
    try:
        for code in ACCOUNT_GROUP_CODE:
            params = {'$select':'Description,AccountType,Status,AccountNumber,AccountGroupCode', "$filter": f"AccountGroupCode eq '{code}' "}
            query = urllib.parse.urlencode(params)
            URL = f"{BASEURL}/GL/GLAccounts?{query}"
            _logger.info(f'Fetching GL accounts => {URL}')
            req = requests.get(URL, headers=HEADERS, auth=HTTPBasicAuth(USERNAME, PASSWORD),timeout=TIMEOUT)
            if req.status_code == 200:
                response = req.json()
                accounts += response.get("value")
            else:
                _logger.error(f"{json.dumps(req.json())}")
        return accounts
    except Exception as ex:
        _logger.exception(ex)

    