# Author: Alex Sheets
# Email: asheet3@lsu.edu
# Discord: dasein#8561

import requests
import re
import sys
import json
import time
import http.client
import base64
import threading

import cloudscraper
from requests.utils import dict_from_cookiejar

from bs4 import BeautifulSoup as bs
from multiprocessing.dummy import Pool as TP 
from getconf import *

#------------------------------------------------------------------------

def atc(session):
    # example of link use
    link = 'https://www.crocs.com'
    response = session.get(link)

    print('starting!..\n')
    
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.crocs.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        # 'referer': 'https://www.crocs.com/p/classic-tie-dye-graphic-clog/.html?cgid=men-footwear&cid=90H',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9'
    }
    # pid goes here after pid=
    data = 'action=add&updates=approaching&pid=207101-90H-M7W9&qty=1&sizeLabel=Men'
    response = session.post('https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/Cart-API', headers=headers, data=data)
    if response.status_code == 200:
        print(response.text)
        shipping(session)
    else:
        print(str(response.status_code))
    
def shipping(session):
    # now, make get request to the crocs checkout page to scrape csrf token
    response = session.get('https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/COCheckout-Step')
    soup = bs(response.text, 'lxml')
    csrfToken = soup.find('input',attrs = {'name':'csrf_token'})['value']

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/COCheckout-Step',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9'
    }
    params = (
        # ZIP code here
        ('address', '#####'),
        ('sensor', 'false'),
        ('csrf_token', csrfToken),
    )
    response = session.get('https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/GlobalData-USPSGeocode', headers=headers, params=params)
    if response.status_code == 200:
        print(response.text)
    else:
        print(str(response.status_code))
    
    headers = {
        'accept': '*/*',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.crocs.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/COCheckout-Step',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9'
    }
    data = {
        'dwfrm_root_singleshipping_shippingAddress_addressFields_states_state': 'LA',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_zip': '70769',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_address1': '17032+Old+Jefferson+Hwy.'
    }
    response = session.post('https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/SPShipping-GetApplicableShippingMethods', headers=headers, data=data)
    if response.status_code == 200:
        print('successfully got shipping methods')
        # print(response.text)
    
    # save form values
    headers = {
        'accept': '*/*',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.crocs.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/COCheckout-Step',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9'
    }
    data = 'dwfrm_root_singleshipping_shippingAddress_addressFields_firstName=Alex&dwfrm_root_singleshipping_shippingAddress_addressFields_lastName=Sheets&dwfrm_root_singleshipping_shippingAddress_addressFields_address1=17032+Old+Jefferson+Hwy.&dwfrm_root_singleshipping_shippingAddress_addressFields_address2=&dwfrm_root_singleshipping_shippingAddress_addressFields_zip=70769&dwfrm_root_singleshipping_shippingAddress_addressFields_city=Prairieville&dwfrm_root_singleshipping_shippingAddress_addressFields_states_state=LA&dwfrm_root_singleshipping_shippingAddress_addressFields_phone=(225)+937-3321&dwfrm_root_singleshipping_shippingAddress_email_emailAddress=asheet3%40lsu.edu&dwfrm_root_singleshipping_shippingAddress_email_emailAddressConfirm=asheet3%40lsu.edu&dwfrm_root_singleshipping_shippingAddress_addressFields_optinnewsletters=true&dwfrm_root_singleshipping_shippingAddress_addressFields_country=US&dwfrm_root_singleshipping_shippingAddress_addressID='
    response = session.post('https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/COCheckout-SaveFormValues', headers=headers, data=data)
    if response.status_code == 200:
        print('Successfully saved the shipping form.\n')
    
    # select the shipping method
    headers = {
        'authority': 'www.crocs.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.crocs.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/COCheckout-Step',
        'accept-language': 'en-US,en;q=0.9'  
    }
    data = {
        'cart_select_shipping_method_box': 'dayton-economy3',
        'return_taxes': 'true'
    }
    response = session.post('https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/SPShipping-SetShippingMethod', headers=headers, data=data)
    if response.status_code == 200:
        print('Successfully chose economy shipping.\n')
        billing(session)

def billing(session):
    # submit payment details (and computer details, apparently)
    headers = {
        'authority': 'www.crocs.com',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'origin': 'https://www.crocs.com',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/COCheckout-Step',
        'accept-language': 'en-US,en;q=0.9'
    }
    # addressID must be scraped, most of the rest is provided information
    data = {
        'dwfrm_root_browserinfo_colordepth': '24',
        'dwfrm_root_browserinfo_screenheight': '1080',
        'dwfrm_root_browserinfo_screenwidth': '1920',
        'dwfrm_root_browserinfo_timezoneoffset': '300',
        'dwfrm_root_browserinfo_javaenabled': 'false',
        'csrf_token': csrfToken,
        'dwfrm_root_singleshipping_shippingAddress_addressFields_firstName': '',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_lastName': '',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_address1': '',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_address2': '',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_zip': '',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_city': '',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_states_state': '',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_phone': '',
        'dwfrm_root_singleshipping_shippingAddress_email_emailAddress': '',
        'dwfrm_root_singleshipping_shippingAddress_email_emailAddressConfirm': '',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_optinnewsletters': 'true',
        'dwfrm_root_singleshipping_shippingAddress_addressFields_country': '',
        # empty val
        'dwfrm_root_singleshipping_shippingAddress_addressID': '',
        'donotcountme': 'on',
        'dwfrm_root_billing_guestBillingAddressIsTheSameAsShippingAddress': 'true',
        'dwfrm_root_billing_billingAddress_addressFields_country': '',
        'dwfrm_root_billing_billingAddress_addressFields_firstName': '',
        'dwfrm_root_billing_billingAddress_addressFields_lastName': '',
        'dwfrm_root_billing_billingAddress_addressFields_address1': '',
        'dwfrm_root_billing_billingAddress_addressFields_address2': '',
        'dwfrm_root_billing_billingAddress_addressFields_zip': '',
        'dwfrm_root_billing_billingAddress_addressFields_city': '',
        # empty val
        'billingstatemockselectcheckout': '',
        'dwfrm_root_billing_billingAddress_addressFields_states_state': '',
        'dwfrm_root_billing_billingAddress_addressFields_phone': '',
        'dwfrm_root_billing_billingAddress_addressID': '',
        # SHIPPING METHOD HERE
        'dwfrm_root_singleshipping_shippingMethod_shippingMethodID': 'dayton-economy3',
        'cardnumber': '',
        'pin': '',
        'dwfrm_root_billing_paymentMethods_selectedPaymentMethodID': 'AdyenDirect',
        'dwfrm_root_billing_paymentMethods_creditCard_owner_d0urmogmfpuj': '',
        # #################
        'dwfrm_root_billing_paymentMethods_creditCard_number_d0blewqwivve': '',
        # MASTER/VISA
        'dwfrm_root_billing_paymentMethods_creditCard_type_d0tqxjbhxuco': '',
        # MM/YY
        'dwfrm_root_billing_paymentMethods_creditCard_cardexpire': '',
        'cvvmasked16626': '***',
        # actual CV
        'dwfrm_root_billing_paymentMethods_creditCard_cvn_d0ptxyclfnxe': '',
        # MM
        'dwfrm_root_billing_paymentMethods_creditCard_month_d0jhyrrvsxuu': '',
        # YYYY
        'dwfrm_root_billing_paymentMethods_creditCard_year_d0woodhmxqtx': '',
        # empty val
        'dwfrm_root_submitorder': ''
    }
    response = session.post('https://www.crocs.com/on/demandware.store/Sites-crocs_us-Site/default/COCheckout-Step/C50290443', headers=headers, data=data)
    if response.status_code == 200:
        print('Successfully applied billing, submitting order...\n')

# create session, add user agent, pass to item collection
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"})
# crocs = queue(s)
crocs = atc(s)
