# Author: Alex Sheets
# Email: asheet3@lsu.edu
# Discord: dasein#8561


import requests, json, sys, re, time, random, datetime, threading, csv, lxml.html, os, base64

from bs4 import BeautifulSoup as bs
from selenium import webdriver
from urllib.request import urlopen


#-----------------------------------------------------------------------------------------------------------

def random_proxy():
    proxy_lines = open('NB/proxies.txt').readlines()
    if len(proxy_lines) > 0:
        random_line = random.choice(proxy_lines).strip()
    else:
        return None
    if len(random_line.split(':')) == 2:
        return {
            'http': 'http://{}'.format(random_line),
            'https': 'http://{}'.format(random_line)
            }
    elif len(random_line.split(':')) == 4:
        parts = random_line.split(':')
        return {
            'http': 'http://{0}:{1}@{2}:{3}'.format(parts[2], parts[3], parts[0], parts[1]),
            'https': 'https://{0}:{1}@{2}:{3}'.format(parts[2], parts[3], parts[0], parts[1])}


try:
    cookies = open('NB/cookies.txt').readlines()
except Exception as e:
    print(f"Exception {e} occurred when trying to get cookies, you must have a cookies.txt file")

try:
    config = json.loads(open("config.json").read())
    delay = float(config["delay"])
except FileNotFoundError as config_file_not_found_error:
    print(
        f"'{config_file_not_found_error.__class__.__name__}' in config.json, please ensure config.json exists in this folder")
    selection = input(f"Press X to exit \n")
    if selection == "X":
        sys.exit()
    else:
        sys.exit()
except json.decoder.JSONDecodeError as json_format_error:
    print(
        f"'{json_format_error.__class__.__name__}' in config.json, please ensure config.json is formatted correctly")
    selection = input(f"Press X to exit \n")
    if selection == "X":
        sys.exit()
    else:
        sys.exit()
except:
    print(f"An error occured, please check your config.json")


def get_random_cookie(i_):
    global cookies
    if len(cookies) > 0:
        cookie = random.choice(cookies)
        cookies.remove(cookie)
        os.truncate('NB/cookies.txt', 0)
        with open('NB/cookies.txt', 'r+') as f:
            for item in cookies:
                f.write(item)
        cookie = cookie.strip()
        return cookie
    else:
        print(f"[{datetime.datetime.now()}][{i_}][NEW BALANCE] No cookies available")
        return None


class Checkout:
    def __init__(self, link, size, CITY, FIRST_NAME, LAST_NAME, STATE, ADDRESS_1, ADDRESS_2, ZIPCODE, EMAIL, PHONE,
                 CARD_NUMBER, CVV, CC_EXPIRY_MONTH, CC_EXPIRY_YEAR, CARD_TYPE, i_, mode):
        self.size = size
        self.CITY = CITY
        self.FIRST_NAME = FIRST_NAME
        self.LAST_NAME = LAST_NAME
        self.STATE = STATE
        self.ADDRESS_2 = ADDRESS_2
        self.ZIPCODE = ZIPCODE
        self.EMAIL = EMAIL
        self.PHONE = PHONE
        self.CVV = CVV
        self.CC_EXPIRY_MONTH = CC_EXPIRY_MONTH
        self.CC_EXPIRY_YEAR = CC_EXPIRY_YEAR
        self.i_ = i_
        self.mode = mode
        self.CARD_TYPE = CARD_TYPE
        self.CARD_NUMBER = CARD_NUMBER
        self.ADDRESS_1 = ADDRESS_1
        self.link = link
        self.session = requests.Session()
        try:
            self.session.proxies.update(random_proxy())
        except:
            pass
        # instantiate so that when we assign, the value carries over methods
        # because it has to be used in post shipping and post billing
        self.uuid = ''
        self.keyword_scraper()
        self.atc()
        self.get_cart()
        self.post_shipping()
        self.post_billing()
        self.submit_payment()
        

    def keyword_scraper(link, thread_current, positive_keywords, negative_keywords, headers):
        positive_keywords = [item.lower() for item in positive_keywords]
        negative_keywords = [item.lower() for item in negative_keywords]
        headers = {
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-US;q=0.9',
            'dnt': '1',
        }
        while True:
            print(f"[{datetime.datetime.now()}][{thread_current}][NB] Waiting for link from keywords")
            response = self.session.get(link, headers=headers)
            products = response.text.split('<div class="product w-100"')
            for item in products:
                tit = item.split('title="')[1].split('"')[0]
                title = tit.split(',', 1)[0].lower()
                if all(keyword in title for keyword in positive_keywords) is True and any(keyword in title for keyword in negative_keywords) is False:
                    pid = item.split('<div class="product-id d-none">')[1].split('<')[0]
                    link = "https://www.newbalance.com/pd/" + pid + ".html"
                    return link

    def atc(self):
        # should go to our scraped link from above
        response = self.session.get(link)
        # grab variant according to size
        variants = json.loads(response.text.split(f"<script>productInfo['{self.pid}'] = ")[1].split(';')[0])
        variants = variants["variants"]
        for item in variants:
            if item["size"] == self.size
                variant = item["id"]
        # add to cart
        while True:
            print("Adding to cart")
            headers = {
                'authority': 'www.newbalance.com',
                'accept': '*/*',
                'x-requested-with': 'XMLHttpRequest',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                'origin': 'https://www.newbalance.com',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': link,
                'accept-language': 'en-US,en;q=0.9'
            }
            data = {
                'pid': variant,
                'quantity': '1',
                'options': '[]'
            }
            response = self.session.post('https://www.newbalance.com/on/demandware.store/Sites-NBUS-Site/en_US/Cart-AddProduct', headers=headers, data=data)
            if response.status_code == 200:
                print("Added to cart...\n")
                return
            else:
                time.sleep(delay)
                continue
      
    def get_cart(self):
        while True:
            print("Getting cart...\n")
            headers = {
                'accept': '*/*',
                'x-requested-with': 'XMLHttpRequest',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': self.link,
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9',
            }
            try:
                response = self.session.get('https://www.newbalance.com/on/demandware.store/Sites-NBUS-Site/en_US/Cart-MiniCartShow', headers=headers)
                print("Grabbed your cart.\n")
                if response.status_code == 200:
                    return
                else:
                    time.sleep(delay)
                    continue
            except:
                time.sleep(delay)
                continue

    def post_shipping(self):
        # first submit
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.newbalance.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.newbalance.com/checkout-begin/?stage=shipping',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',    
        }
        data = {
            'firstName': self.FIRST_NAME,
            'lastName': self.LAST_NAME,
            'address1': self.ADDRESS_1,
            'address2': self.ADDRESS_2,
            'city': self.CITY,
            'postalCode': self.ZIPCODE,
            'stateCode': self.STATE,
            'countryCode': 'US',
            'phone': self.PHONE,
            'shipmentUUID': ''
        }
        response = self.session.post('https://www.newbalance.com/on/demandware.store/Sites-NBUS-Site/en_US/CheckoutShippingServices-UpdateShippingMethodsList', headers=headers, data=data)
        # scrapes the shipping UUID passed back
        json_text = json.loads(response.text)
        self.uuid = json_text['order']['items']['items'][0]['shipmentUUID']

        # get shipping csrf token
        response = self.session.get('https://www.newbalance.com/checkout-begin/?stage=shipping#shipping')
        soup = bs(response.text, 'lxml')
        token = soup.find('input', {'name':'csrf_token'})['value']
        
        while True:
            print("Posting shipping")
            headers = {
                'authority': 'www.newbalance.com',
                'accept': '*/*',
                'x-requested-with': 'XMLHttpRequest',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                'origin': 'https://www.newbalance.com',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': 'https://www.newbalance.com/checkout-begin/?stage=shipping',
                'accept-language': 'en-US,en;q=0.9',
            }
            data = {
                'originalShipmentUUID': self.uuid,
                'shipmentUUID': self.uuid,
                'zipCodeErrorMsg': 'Please enter a valid Zip/Postal code',
                'shipmentSelector': 'new',
                'dwfrm_shipping_shippingAddress_addressFields_country': 'US',
                'dwfrm_shipping_shippingAddress_addressFields_firstName': self.FIRST_NAME,
                'dwfrm_shipping_shippingAddress_addressFields_lastName': self.LAST_NAME,
                'dwfrm_shipping_shippingAddress_addressFields_address1': self.ADDRESS_1,
                'dwfrm_shipping_shippingAddress_addressFields_address2': self.ADDRESS_2,
                'dwfrm_shipping_shippingAddress_addressFields_city': self.CITY,
                'dwfrm_shipping_shippingAddress_addressFields_states_stateCode': self.STATE,
                'dwfrm_shipping_shippingAddress_addressFields_postalCode': self.ZIPCODE,
                'dwfrm_shipping_shippingAddress_addressFields_phone': self.PHONE,
                'dwfrm_shipping_shippingAddress_addressFields_email': self.EMAIL,
                'dwfrm_shipping_shippingAddress_addressFields_addtoemaillist': 'true',
                'csrf_token': token,
                'saveShippingAddr': 'false'
            }
            try:
                response = self.session.post('https://www.newbalance.com/on/demandware.store/Sites-NBUS-Site/en_US/CheckoutShippingServices-SubmitShipping', headers=headers, data=data)
                print("Posted shipping")
                if response.status_code == 200:
                    print('Pass was successful. Directing to checkout...\n')
                    return
                else:
                    time.sleep(delay)
                    continue
            except:
                time.sleep(delay)
                continue

    def post_billing(self):
        # get payment csrf token
        response = self.session.get('https://www.newbalance.com/checkout-begin/?stage=payment#payment')
        soup = bs(response.text, 'lxml')
        token2 = soup.find('input', {'name':'csrf_token'})['value']

        while True:
            print("Posting billing")
            headers = {
                'authority': 'www.newbalance.com',
                'accept': '*/*',
                'x-requested-with': 'XMLHttpRequest',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                'origin': 'https://www.newbalance.com',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': 'https://www.newbalance.com/checkout-begin/?stage=payment',
                'accept-language': 'en-US,en;q=0.9'
            }
            data = {
                'csrf_token': token2,
                'localizedNewAddressTitle': 'New Address',
                'dwfrm_billing_paymentMethod': 'CREDIT_CARD',
                'dwfrm_billing_creditCardFields_cardNumber': self.CARD_NUMBER,
                'dwfrm_billing_creditCardFields_expirationMonth': self.CC_EXPIRY_MONTH,
                'dwfrm_billing_creditCardFields_expirationYear': self.CC_EXPIRY_YEAR,
                'dwfrm_billing_creditCardFields_securityCode': self.CVV,
                'dwfrm_billing_creditCardFields_cardType': self.CARD_TYPE,
                'dwfrm_billing_realtimebanktransfer_iban': '', 
                'dwfrm_billing_shippingAddressUseAsBillingAddress': 'true',
                'addressSelector': self.uuid,
                'dwfrm_billing_addressFields_country': 'US',
                'dwfrm_billing_addressFields_firstName': self.FIRST_NAME,
                'dwfrm_billing_addressFields_lastName': self.LAST_NAME,
                'dwfrm_billing_addressFields_address1': self.ADDRESS_1,
                'dwfrm_billing_addressFields_address2': self.ADDRESS_2,
                'dwfrm_billing_addressFields_city': self.CITY,
                'dwfrm_billing_addressFields_states_stateCode': self.STATE,
                'dwfrm_billing_addressFields_postalCode': self.ZIPCODE,
                'dwfrm_billing_addressFields_phone': self.PHONE,
                # LEAVE empty
                '': '',
                'dwfrm_billing_paymentMethod': 'CREDIT_CARD',
                'dwfrm_billing_creditCardFields_cardNumber': self.CARD_NUMBER,
                'dwfrm_billing_creditCardFields_expirationMonth': self.CC_EXPIRY_MONTH,
                'dwfrm_billing_creditCardFields_expirationYear': self.CC_EXPIRY_YEAR,
                'dwfrm_billing_creditCardFields_securityCode': self.CVV,
                'dwfrm_billing_creditCardFields_cardType': self.CARD_TYPE,
                'dwfrm_billing_realtimebanktransfer_iban': '',
                'addressId': self.uuid,
                'saveBillingAddr': 'false'
            }
            response = self.session.post('https://www.newbalance.com/on/demandware.store/Sites-NBUS-Site/en_US/CheckoutServices-SubmitPayment', headers=headers, data=data)
            print(response.status_code)    
            print("Posted billing")
            print(response.json())
            if response.status_code == 200:
                print("Successfully posted billing data")
                return
            else:
                time.sleep(delay)
                continue
    
    def submit_payment(self):
        headers = {
            'authority': 'www.newbalance.com',
            'content-length': '0',
            'accept': '*/*',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
            'origin': 'https://www.newbalance.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.newbalance.com/checkout-begin/?stage=placeOrder',
            'accept-language': 'en-US,en;q=0.9'
        }
        response = self.session.post('https://www.newbalance.com/on/demandware.store/Sites-NBUS-Site/en_US/CheckoutServices-PlaceOrder?termsconditions=undefined', headers=headers)
        if response.status_code == 200:
            # if invalid, you will see a response saying there was an error processing.
            # if successful, there will be a json response with an order ID
            # and you will receive email confirmation.
            print(response.text)


def run():
    print('Hello')
    task_list = []
    try:
        task_csv = open("NB/tasks.csv", "r")
    except FileNotFoundError as task_file_not_found_error:
        print(
            f"[{datetime.datetime.now()}] '{task_file_not_found_error.__class__.__name__}' in tasks.csv, please ensure tasks.csv exists in this folder")
        selection = input(f"[{datetime.datetime.now()}] Press X to exit \n")
        if selection == "X":
            sys.exit()
        else:
            sys.exit()
    reader_csv = csv.reader(task_csv)
    for line in reader_csv:
        task_list.append(line)

    task_csv.close()
    print(f"{len(task_list) - 1} Tasks Loaded")
    input("Press enter to start!")

    thread_list = []
    for i in range(len(task_list)):
        task_info_c = task_list[i]
        try:
            # use PIDS instead of links because nvidia does not have separate links
            if str(task_info_c[0]) != "LINK":
                thread = threading.Thread(target=Checkout,
                                          args=(task_info_c[0], task_info_c[1], task_info_c[2], task_info_c[3],
                                                task_info_c[4],
                                                task_info_c[5], task_info_c[6], task_info_c[7], task_info_c[8],
                                                task_info_c[9],
                                                task_info_c[10], task_info_c[11], task_info_c[12], task_info_c[13],
                                                task_info_c[14], i, task_info_c[15]))
                thread_list.append(thread)
                thread.start()
        except IndexError as e:
            print(
                f"[{datetime.datetime.now()}] '{e.__class__.__name__}' in tasks file, check you have filled in tasks.csv and you have no blank lines")

if __name__ == "__main__":
    run()
