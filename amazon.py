import requests, re, json, time, base64, threading, lxml.html, random, datetime
from colorama import init, Fore, Back, Style

from bs4 import BeautifulSoup as bs

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# undetected chromedriver
import undetected_chromedriver as uc
from subprocess import check_output

init(autoreset=True)
LOCK = threading.Lock()
user_agent = ''

# ------------------------------------------------------------------------

# TODO:
# - figure out attaching cookies from other sessions
# - 

try:
    cookies = open('cookies.json').readlines()
except Exception as e:
    print(f"Exception {e} occurred when trying to get cookies, you must have a cookies.txt file")

def print_format(message):
    return print(f"[{datetime.datetime.now()}][AMAZON] {message.title()}")

def random_proxy():
    try:
        proxy_lines = open('Amazon/proxies.txt').readlines()
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
            splitted = random_line.split(':')
            return {
                'http': 'http://{0}:{1}@{2}:{3}'.format(splitted[2], splitted[3], splitted[0], splitted[1]),
                'https': 'https://{0}:{1}@{2}:{3}'.format(splitted[2], splitted[3], splitted[0], splitted[1])
                }
    except FileNotFoundError as proxy_file_not_found_error:
        print(Back.RED + Fore.BLACK +
              f"[{datetime.datetime.now()}] '{proxy_file_not_found_error.__class__.__name__}' in proxies.txt, please ensure proxies.txt exists in this folder")
        no_proxy_error = input(f"[{datetime.datetime.now()}] Would you like to continue with local IP? y/n \n")
        if no_proxy_error == "n":
            exit_option = input(f"[{datetime.datetime.now()}] Press X to exit \n")
            if exit_option == "X":
                sys.exit()
            else:
                sys.exit()


try:
    config = json.loads(open("config.json").read())
    delay = config["delay"]
except FileNotFoundError as config_file_not_found_error:
    print(Back.RED + Fore.BLACK +
          f"[{datetime.datetime.now()}] '{config_file_not_found_error.__class__.__name__}' in config.json, please ensure config.json exists in this folder")
    selection = input(f"[{datetime.datetime.now()}] Press X to exit \n")
    if selection == "X":
        sys.exit()
    else:
        sys.exit()
except json.decoder.JSONDecodeError as json_format_error:
    print(
        f"[{datetime.datetime.now()}] '{json_format_error.__class__.__name__}' in config.json, please ensure config.json is formatted correctly")
    selection = input(f"[{datetime.datetime.now()}] Press X to exit \n")
    if selection == "X":
        sys.exit()
    else:
        sys.exit()


class amazon:
    # init setup
    def __init__(self, FIRST_NAME, LAST_NAME, CARD_NUMBER, EXPIRY_MONTH, EXPIRY_YEAR, CARD_CVC, 
                    CARD_TYPE, LINK, MODE, user_agent, i_):
        options = uc.ChromeOptions()
        # options.headless=True
        # options.add_argument('--headless')
        options.add_argument('--window-size=1920x1080')
        # finding chrome version on user's computer
        try:
            cmd = r'wmic datafile where name="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" get Version /value'
            chrome_version = str(check_output(cmd)).split('Version=')[1].split(r"\r")[0]
        except:
            chrome_version = None
        # installs chrome version to the driver
        uc.install(target_version=chrome_version)
        self.driver = uc.Chrome(options=options)

        # session init
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"})
        self.i_ = i_
        self.link = LINK
        self.FIRST_NAME = FIRST_NAME
        self.LAST_NAME = LAST_NAME
        self.EXPIRY_YEAR = EXPIRY_YEAR
        self.EXPIRY_MONTH = EXPIRY_MONTH
        self.CARD_NUMBER = CARD_NUMBER
        self.QUANTITY = QUANTITY
        self.CARD_TYPE = CARD_TYPE
        self.CARD_CVC = CARD_CVC
        self.mode = MODE

        # vars
        self.csrf = ''
        self.rsid = ''
        self.widget_state = ''
        self.customerId = ''
        self.addressID = ''
        self.purchaseID = ''
        self.instrumentID = ''
        self.checkout_link = ''

        # flow, eliminated login from script
        self.proxies = random_proxy()
        if self.mode == "restock":
            self.monitor()
        self.get_cookies()
        self.atc()
        # self.cart_link = f'https://www.amazon.com/gp/cart/desktop/go-to-checkout.html/ref=ox_sc_proceed?partialCheckoutCart=1&isToBeGiftWrappedBefore=0&proceedToRetailCheckout=Proceed+to+checkout&proceedToCheckout=1&cartInitiateId={str(self.id_gen())}'
        # self.post_shipping_address(self.random_address())
        # self.payment()
        # self.prepare_final()
        # self.final()

    def get_cookies(self):
        while True:
            try:
                with open('cookies.txt', 'r') as c_file:
                    # each login session/cookies will be saved as one line
                    c_file_data = c_file.readline()
                    b64 = c_file_data[14:]
                    timestamp = c_file_data[-13:-3]
                    print(f"Timestamp: {timestamp}")
                    tokens = b64.split("b'")
                    for token in tokens:
                        if token.endswith("'"):
                            token = token[:-1]
                        elif token.endswith("\'"):
                            token = token[:-2]
                        base64_bytes = token.encode("ascii") 
                        str_bytes = base64.b64decode(base64_bytes) 
                        cookie_str = str_bytes.decode("ascii")
                        x = cookie_str.split()
                        if (len(x)) > 0:
                            try:
                                name, value = x[7], x[13]
                                name = name[1:-2]
                                value = value[1:-2]
                                value = value.replace('\\"', '')
                                self.session.cookies.set(name=name, value=value)
                                self.driver.add_cookie({'name': name, 'value': value})
                            except Exception as e:
                                print(e)
                                continue
                    # cookie name skin with value noskin
                    self.session.cookies.set(name='skin', value='noskin')
                    self.driver.add_cookie({'name': 'skin', 'value': 'noskin'})
                    return
            except Exception as e:
                print(e)
                continue

    @staticmethod
    def id_gen():
        return round(time.time() * 1000)

    @staticmethod
    def regex(string, response):
        try:
            return re.findall(f'{string}(.*?)"', response)[0]
        except:
            return re.findall(f'{string}(.*?)"', response)

    def atc(self):
        print_format('Attempting ATC. . .')
        if self.mode != "restock":
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-language': 'en-US,en;q=0.9'
            }
            response = self.session.get(self.link, headers=headers)
            # if 'captcha' in response.text:
            #     soup = bs(self.driver.text, 'html.parser')
            #     token = download_captcha(soup.find('div', {"id": "auth-captcha-image-container"}).img['src'])
            #     print(token)
            print_format("getting add to cart data")
            soup = bs(response.text, 'html.parser')

            # scrape values
            self.list_id = soup.find('input', {'name': 'offerListingID'})['value']
            self.asin = soup.find('input', {'name': 'ASIN'})['value']
            self.session_id = soup.find('input', {'name': 'session-id'})['value']
            self.merchant_id = soup.find('input', {'name': 'merchantID'})['value']
            self.csrf = soup.find('input', {'name': 'CSRF'})['value']
            self.rsid = soup.find('input', {'name': 'rsid'})['value']

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'en-US,en;q=0.9'
        }
        data = {
            'offerListingID': self.list_id,
            'session-id': self.session_id,
            'ASIN': self.asin,
            'isMerchantExclusive': '0',
            'merchantID': self.merchant_id,
            'isAddon': '0',
            'nodeID': '',
            'sellingCustomerID': '',
            'sr': '8-2',
            'storeID': '',
            'tagActionCode': '',
            'viewID': 'glance',
            'rebateId': '',
            'ctaDeviceType': 'desktop',
            'ctaPageType': 'detail',
            'usePrimeHandler': '0',
            'sourceCustomerOrgListID': '',
            'sourceCustomerOrgListItemID': '',
            'wlPopCommand': '',
            'quantity': '1',
            'submit.add-to-cart': 'Add to Cart',
            'dropdown-selection': 'add-new',
            'dropdown-selection-ubb': 'add-new',
            'isUSSControl': '1'
        }
        while True:
            try:
                self.proxies = random_proxy()
                atc_call = self.session.post('https://www.amazon.com/gp/product/handle-buy-box/ref=dp_start-bbf_1_glance', 
                                                headers=headers, data=data)
                if atc_call.status_code == 200:
                    LOCK.acquire()
                    print(Fore.GREEN +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Successfully Added to Cart - {atc_call.status_code}")
                    LOCK.release()
                   
                    return 'x'
                else:
                    LOCK.acquire()
                    print(Fore.RED +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Error Adding to Cart - {atc_call.status_code}")
                    LOCK.release()
                    return None
            except Exception as e:
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][AMAZON] Error Adding to Cart - {e}")
                LOCK.release()
                time.sleep(float(delay))
                continue

    def random_address(self):
        print_format('Selecting your address for shipping')
        while True:
            try:
                self.proxies = random_proxy()
                page = self.session.get(self.cart_link, proxies=self.proxies).text  
                if 'id="address-book-entry' in page:
                    soup = bs(page, "html.parser")
                    addresses = str(soup.find("form", {"class": "a-nostyle"}))
                    random_address = addresses.split(f'id="address-book-entry')
                    random_address.pop(0)
                    random_address = random.choice(random_address)
                    section = random_address.split("ship-to-this-address a-button a-button-primary a-button-span12 a-spacing-medium")[1]
                    address_link = section
                    address_link = address_link.split('href="')[1].split('"')[0]
                    address_link = address_link.replace("amp;", "")
                    address_link += "&hasWorkingJavascript=1"
                    self.addressID = address_link.split('addressID=')[1].split('&')[0]
                    self.purchaseID = address_link.split('purchaseId=')[1].split('&')[0]
                    
                    try:
                        page = self.session.get('http://www.amazon.com' + address_link).text
                        if page:
                            LOCK.acquire()
                            print(Fore.GREEN +
                                f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Successfully Chose Address - {atc_call.status_code}")
                            LOCK.release()
                            return page
                        else:
                            LOCK.acquire()
                            print(Fore.RED +
                                f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Error choosing address")
                            LOCK.release()
                            return None
                    except Exception as page_err:
                        LOCK.acquire()
                        print(Fore.RED +
                            f"[{datetime.datetime.now()}][{self.i_}][AMAZON] Error Getting Address Page - {page_err}")
                        LOCK.release()
                        time.sleep(float(delay))
                        continue
            except Exception as cart_err:
                LOCK.acquire()
                print(Fore.RED +
                    f"[{datetime.datetime.now()}][{self.i_}][AMAZON] Error Getting Cart Page - {cart_err}")
                LOCK.release()
                time.sleep(float(delay))
                continue

    def post_shipping_address(self, html_string):
        """
        Place your order means shipping address and method is already there

        Choose your shipping options means address is chosen but not method
        """

        if 'place your order' and 'choose your shipping options' not in html_string.lower():
            print(html_string)
            
        # what we expect
        if 'choose your shipping options' in html_string.lower():
            self.post_shipping_method(html_string)              

    def post_shipping_method(self, html_string):
        headers = {
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8;',
            'accept': 'text/plain, */*; q=0.01',
            'x-amz-checkout-transition': 'ajax',
            'x-requested-with': 'XMLHttpRequest',
            'accept-language': 'en-US,en;q=0.9',
        }
        data = {
            'groupCount': self.regex('name="groupCount" value="', html_string),
            'SSS_order_0_ShippingSpeed_second-isoa': self.regex('name="SSS_order_0_ShippingSpeed_second-isoa" value="', html_string),
            'shippingOfferingId_0_second-isoa': self.regex('name="shippingOfferingId_0_second-isoa" value="', html_string),
            'guaranteeType_0_second-isoa': 'GUARANTEED',
            'isShipWhenCompleteValid_0_second-isoa': self.regex('name="isShipWhenCompleteValid_0_second-isoa" value="', html_string),
            'isShipWheneverValid_0_second-isoa': self.regex('name="isShipWheneverValid_0_second-isoa" value="', html_string),
            'shipsplitpriority_0_second-isoa': self.regex('name="shipsplitpriority_0_second-isoa" value="', html_string),
            'order_0_ShippingSpeed': self.regex('name="order_0_ShippingSpeed" value="', html_string),
            'SSS_order_0_ShippingSpeed_std-us-5': self.regex('name="SSS_order_0_ShippingSpeed_std-us-5" value="', html_string),
            'shippingOfferingId_0_std-us-5': self.regex('name="shippingOfferingId_0_std-us-5" value="', html_string),
            'guaranteeType_0_std-us-5': 'GUARANTEED',
            'isShipWhenCompleteValid_0_std-us-5': self.regex('name="isShipWhenCompleteValid_0_std-us-5" value="', html_string),
            'isShipWheneverValid_0_std-us-5': self.regex('name="sShipWheneverValid_0_std-us-5" value="', html_string),
            'shipsplitpriority_0_std-us-5': self.regex('name="shipsplitpriority_0_std-us-5" value="', html_string),
            'SSS_order_0_ShippingSpeed_second': self.regex('name="SSS_order_0_ShippingSpeed_second" value="', html_string),
            'shippingOfferingId_0_second': self.regex('name="shippingOfferingId_0_second" value="', html_string),
            'guaranteeType_0_second': 'GUARANTEED',
            'isShipWhenCompleteValid_0_second': self.regex('name="isShipWhenCompleteValid_0_second" value="', html_string),
            'isShipWheneverValid_0_second': self.regex('isShipWheneverValid_0_second" value="', html_string),
            'shipsplitpriority_0_second': self.regex('name="shipsplitpriority_0_second" value="', html_string),
            'order_0_ShipSplitPreference': self.regex('name="order_0_ShipSplitPreference" value="', html_string),
            'lineItemEntityIds_0': self.regex('name="lineItemEntityIds_0" value="', html_string),
            'shippingOfferingId_0_sss-us-4': self.regex('name="lineItemEntityIds_0" value="', html_string),
            'SSS_order_0_ShippingSpeed_sss-us-4': self.regex('name="lineItemEntityIds_0" value="', html_string),
            'guaranteeType_0_sss-us-4': 'GUARANTEED',
            'isShipWhenCompleteValid_0_sss-us-4': self.regex('name="lineItemEntityIds_0" value="', html_string),
            'isShipWheneverValid_0_sss-us-4': self.regex('name="lineItemEntityIds_0" value="', html_string),
            'shipsplitpriority_0_sss-us-4': self.regex('name="lineItemEntityIds_0" value="', html_string),
            'hasWorkingJavascript': '1',
            'isAsync': '1',
            'isClientTimeBased': '1',
            'ie': 'UTF8',
            'fromAnywhere': '0',
            'handler': '/gp/buy/shipoptionselect/handlers/continue.html'
        }
        while True:
            try:
                self.proxies = random_proxy()
                ship_call = self.session.post('https://www.amazon.com/gp/buy/shared/handlers/async-continue.html/ref=chk_ship_option_continue', 
                                                data=data, headers=headers, proxies=self.proxies)
                if ship_call.status_code == 200:
                    if 'Select a payment method' in ship_call.text:
                        text = json.loads(ship_call.text.split('var options = ')[1].split(';')[0])
                        self.widget_state = text['serializedState']
                        self.customerId = text['customerId']
                    LOCK.acquire()
                    print(Fore.GREEN +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Successfully Submitted Shipping - {ship_call.status_code}")
                    LOCK.release()
                    return 'x'
                else:
                    LOCK.acquire()
                    print(Fore.RED +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Error With Your Shipping Address - {ship_call.status_code}")
                    LOCK.release()
                    return None
            except Exception as e:
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][AMAZON] Error Applying Shipping - Retrying... - {e}")
                LOCK.release()
                time.sleep(float(delay))
                continue
    
    def payment(self):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        data = {
            'ppw-widgetEvent:AddCreditCardEvent': '',
            'ppw-jsEnabled': 'true',
            'ppw-widgetState': self.widget_state,
            'ie': 'UTF-8',
            'addCreditCardNumber': self.CARD_NUMBER,
            'ppw-accountHolderName': str(self.FIRST_NAME) + ' ' + str(self.LAST_NAME),
            'ppw-expirationDate_month': self.EXPIRY_MONTH,
            'ppw-expirationDate_year': self.EXPIRY_YEAR
        }
        while True:
            try:
                self.proxies = random_proxy()
                pay_call = self.session.post(
                    f'https://apx-security.amazon.com/payments-portal/data/f1/widgets2/v1/customer/{self.customerId}/continueWidget',
                    headers=headers, params=(('sif_profile', 'APX-Encrypt-All-NA'),), data=data, proxies=self.proxies)
                if pay_call.status_code == 200:
                    self.instrumentID = pay_call.text[132:178]
                    LOCK.acquire()
                    print(Fore.GREEN +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Successfully Submitted Card Info - {ship_call.status_code}")
                    LOCK.release()
                    return 'x'
                else:
                    LOCK.acquire()
                    print(Fore.RED +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Error With Card Info - {ship_call.status_code}")
                    LOCK.release()
                    return None
            except Exception as e:
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][AMAZON] Error Applying Card Info - Retrying... - {e}")
                LOCK.release()
                time.sleep(float(delay))
                continue

    def prepare_final(self):
        # handle prime offer (rejects)
        prime_headers = {
            'authority': 'www.amazon.com',
            'rtt': '150',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8;',
            'accept': 'text/plain, */*; q=0.01',
            'x-amz-checkout-transition': 'ajax',
            'x-requested-with': 'XMLHttpRequest',
            'downlink': '9.2',
            'ect': '4g',
            'origin': 'https://www.amazon.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.amazon.com/gp/buy/billingaddressselect/handlers/display.html?hasWorkingJavascript=1',
            'accept-language': 'en-US,en;q=0.9'
        }
        prime_data = {
            'isClientTimeBased': '1',
            'subscriptionplanID': '0P89176973',
            'redirectPath': '/gp/prime/pip/proceed.html',
            'ie': 'UTF8',
            'action.checkoutInterstitialDecline': '1',
            'eventCode': '',
            'hasWorkingJavascript': '1',
            'isAsync': '1',
            'handler': '/gp/buy/prime/handler.html'
        }
        # handle choosing billing address
        billing1_headers = {
            'authority': 'www.amazon.com',
            'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            'rtt': '100',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8;',
            'accept': 'text/plain, */*; q=0.01',
            'x-amz-checkout-transition': 'ajax',
            'x-requested-with': 'XMLHttpRequest',
            'downlink': '9.1',
            'ect': '4g',
            'origin': 'https://www.amazon.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.amazon.com/gp/buy/payselect/handlers/display.html?hasWorkingJavascript=1',
            'accept-language': 'en-US,en;q=0.9',
        }
        billing1_data = {
            'ppw-widgetState': self.widget_state,
            'ie': 'UTF-8',
            'ppw-instrumentRowSelection': 'instrumentId=' + self.instrumentID + '&isExpired=false&paymentMethod=CC&tfxEligible=false',
            'ppw-jsEnabled': 'true',
            'ppw-widgetEvent:SetPaymentPlanSelectContinueEvent': '',
            'isAsync': '1',
            'isClientTimeBased': '1',
            'handler': '/gp/buy/payselect/handlers/apx-submit-continue.html'
        }
        billing2_headers = {
            'authority': 'www.amazon.com',
            'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            'rtt': '150',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8;',
            'accept': 'text/plain, */*; q=0.01',
            'x-amz-checkout-transition': 'ajax',
            'x-requested-with': 'XMLHttpRequest',
            'downlink': '5.15',
            'ect': '4g',
            'origin': 'https://www.amazon.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.amazon.com/gp/buy/payselect/handlers/display.html?hasWorkingJavascript=1',
            'accept-language': 'en-US,en;q=0.9'
        }
        billing2_data = {
            'isClientTimeBased': '1',
            'ie': 'UTF8',
            'action': 'select-billing',
            'addressID': self.addressID,
            'enableDeliveryPreferences': '1',
            'fromAnywhere': '0',
            'isCurrentAddress': '',
            'numberOfDistinctItems': '1',
            'paymentInstrumentId': self.instrumentID,
            'paymentMethodCode': 'CC',
            'purchaseId': self.purchaseID,
            'requestToken': '',
            'hasWorkingJavascript': '1',
            'isAsync': '1',
            'handler': '/gp/buy/addressselect/handlers/continue.html'
        }

        while True:
            try:
                self.proxies = random_proxy()
                prime_post = self.session.post('https://www.amazon.com/gp/buy/shared/handlers/async-continue.html/ref=prime_pdp_ho_nt_sov', 
                                                headers=headers, data=data, proxies=self.proxies)
                billing1_post = self.session.post('https://www.amazon.com/gp/buy/shared/handlers/async-continue.html', 
                                                headers=headers, data=data, proxies=self.proxies)
                billing2_post = self.session.post('https://www.amazon.com/gp/buy/shared/handlers/async-continue.html/ref=ox_billing_ship_to_this_1', 
                                                headers=headers, data=data, proxies=self.proxies)
                # we scrape continue link from response
                # its the final review order page link
                soup = bs(billing2_post.text, "html.parser")
                addresses = str(soup.find("form", {"class": "a-nostyle"}))
                random_address = addresses.split(f'id="address-book-entry')
                random_address.pop(0)
                random_address = random.choice(random_address)
                section = random_address.split("ship-to-this-address a-button a-button-primary a-button-span12 a-spacing-medium")[1]
                self.checkout_link = section
                self.checkout_link = checkout_link.replace("amp;", "")
                self.checkout_link = checkout_link.split('href="')[1].split('"')[0]
                if self.checkout_link:
                    LOCK.acquire()
                    print(Fore.GREEN +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Successfully Prepared Checkout")
                    LOCK.release()
                    return 'x'
                else:
                    LOCK.acquire()
                    print(Fore.RED +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Error Preparing Checkout - {billing2_post.status_code}")
                    LOCK.release()
                    return None
            except Exception as e:
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][AMAZON] Error Preparing Checkout - Retrying... - {e}")
                LOCK.release()
                time.sleep(float(delay))
                continue

    def final(self):

        self.session.get('http://www.amazon.com' + checkout_link)

        headers = {
            'authority': 'www.amazon.com',
            'cache-control': 'max-age=0',
            'rtt': '50',
            'downlink': '10',
            'ect': '4g',
            'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'origin': 'https://www.amazon.com',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.amazon.com/gp/buy/spc/handlers/display.html?hasWorkingJavascript=1',
            'accept-language': 'en-US,en;q=0.9'
        }
        data = {
            'submitFromSPC': self.regex('name="submitFromSPC" value="', response.text),
            'pickupType': self.regex('name="pickupType" value="', response.text),
            'searchCriterion': self.regex('name="searchCriterion" value="', response.text),
            'storeZip': self.regex('name="storeZip" value="', response.text),
            'storeZip2': self.regex('name="storeZip2" value="', response.text),
            'searchLockerFormAction': self.regex('name="searchLockerFormAction" value="', response.text),
            'claimCode': '',
            'primeMembershipTestData': self.regex('name="primeMembershipTestData" value="', response.text),
            'fasttrackExpiration': self.regex('name="fasttrackExpiration" value="', response.text),
            'countdownThreshold': self.regex('name="countdownThreshold" value="', response.text),
            'countdownId': self.regex('name="countdownId" value="', response.text),
            'showSimplifiedCountdown': self.regex('name="showSimplifiedCountdown" value="', response.text),
            'gift-message-text': '',
            'concealment-item-message': self.regex('name="concealment-item-message" value="', response.text),
            'dupOrderCheckArgs': self.regex('name="dupOrderCheckArgs" value="', response.text),
            'order0': self.regex('name="order0" value="', response.text),
            'shippingofferingid0.0': self.regex('name="shippingofferingid0.0" value="', response.text),
            'guaranteetype0.0': self.regex('name="guaranteetype0.0" value="', response.text),
            'issss0.0': self.regex('name="issss0.0" value="', response.text),
            'shipsplitpriority0.0': self.regex('name="shipsplitpriority0.0" value="', response.text),
            'isShipWhenCompleteValid0.0': self.regex('name="isShipWhenCompleteValid0.0" value="', response.text),
            'isShipWheneverValid0.0': self.regex('name="isShipWheneverValid0.0" value="', response.text),
            'shippingofferingid0.1': self.regex('name="shippingofferingid0.1" value="', response.text),
            'guaranteetype0.1': self.regex('name="guaranteetype0.1" value="', response.text),
            'issss0.1': self.regex('name="issss0.1" value="', response.text),
            'shipsplitpriority0.1': self.regex('name="shipsplitpriority0.1" value="', response.text),
            'isShipWhenCompleteValid0.1': self.regex('name="isShipWhenCompleteValid0.1" value="', response.text),
            'isShipWheneverValid0.1': self.regex('name="isShipWheneverValid0.1" value="', response.text),
            'shippingofferingid0.2': self.regex('name="shippingofferingid0.2" value="', response.text),
            'guaranteetype0.2': self.regex('name="guaranteetype0.2" value="', response.text),
            'issss0.2': self.regex('name="issss0.2" value="', response.text),
            'shipsplitpriority0.2': self.regex('name="shipsplitpriority0.2" value="', response.text),
            'isShipWhenCompleteValid0.2': self.regex('name="isShipWhenCompleteValid0.2" value="', response.text),
            'isShipWheneverValid0.2': self.regex('name="isShipWheneverValid0.2" value="', response.text),
            'previousshippingofferingid0': self.regex('name="previousshippingofferingid0" value="', response.text),
            'previousguaranteetype0': self.regex('name="previousguaranteetype0" value="', response.text),
            'previousissss0': self.regex('name="previousissss0" value="', response.text),
            'previousshippriority0': self.regex('name="previousshippriority0" value="', response.text),
            'lineitemids0': self.regex('name="lineitemids0" value="', response.text),
            'currentshippingspeed': self.regex('name="currentshippingspeed" value="', response.text),
            'previousShippingSpeed0': self.regex('name="previousShippingSpeed0" value="', response.text),
            'currentshipsplitpreference': self.regex('name="currentshipsplitpreference" value="', response.text),
            'shippriority.0.shipWhenComplete': self.regex('name="shippriority.0.shipWhenComplete" value="', response.text),
            'groupcount': self.regex('name="groupcount" value="', response.text),
            'snsUpsellTotalCount': self.regex('name="snsUpsellTotalCount" value=', response.text),
            'onmlUpsellSuppressedCount': self.regex('name="onmlUpsellSuppressedCount" value="', response.text),
            'vasClaimBasedModel': self.regex('name="vasClaimBasedModel" value="', response.text),
            'shiptrialprefix': self.regex('name="shiptrialprefix" value="', response.text),
            'isfirsttimecustomer': self.regex('name="isfirsttimecustomer" value="', response.text),
            'isTFXEligible': self.regex('name="isTFXEligible" id="isTFXEligible" value="', response.text),
            'isFxEnabled': self.regex('name="isFxEnabled" id="isFxEnabled" value="', response.text),
            'isFXTncShown': self.regex('name="isFXTncShown" id="isFXTncShown" value="', response.text),
            'fromAnywhere': self.regex('name="fromAnywhere" value="', response.text),
            'redirectOnSuccess': self.regex('name="redirectOnSuccess" value=', response.text),
            'purchaseTotal': self.regex('name="purchaseTotal" value="', response.text),
            'purchaseTotalCurrency': self.regex('name="purchaseTotalCurrency" value="', response.text),
            'purchaseID': self.regex('name="purchaseID" value="', response.text),
            'purchaseCustomerId': self.regex('name="purchaseCustomerId" value="', response.text),
            'useCtb': self.regex('name="useCtb" value="', response.text),
            'scopeId': self.regex('name="scopeId" value="', response.text),
            'isQuantityInvariant': self.regex('name="isQuantityInvariant" value="', response.text),
            'promiseTime-0': self.regex('name="promiseTime-0" value="', response.text),
            'promiseAsin-0': self.regex('name="promiseAsin-0" value="', response.text),
            'selectedPaymentPaystationId': self.regex('name="selectedPaymentPaystationId" value="', response.text),
            'hasWorkingJavascript': '1',
            'placeYourOrder1': '1'
        }
        while True:
            try:
                self.proxies = random_proxy()
                final = self.session.post('https://www.amazon.com/gp/buy/spc/handlers/static-submit-decoupled.html/ref=ox_spc_place_order?ie=UTF8&hasWorkingJavascript=',
                            headers=headers, data=data, proxies=self.proxies)
                if final.status_code == 200:
                    LOCK.acquire()
                    print(Fore.GREEN +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Placed order! Check email.")
                    LOCK.release()
                    return 'x'
                else:
                    LOCK.acquire()
                    print(Fore.RED +
                        f"[{datetime.datetime.now()}][{self.i_}][AMAZON][{self.asin}] Error Submitting Final Details - {final.status_code}")
                    LOCK.release()
                    return None
            except Exception as e:
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][AMAZON] Error Submitting Order - Retrying... - {e}")
                LOCK.release()
                time.sleep(float(delay))
                continue

def run():
    task_list = []
    try:
        task_csv = open("Amazon/tasks.csv", "r")
    except FileNotFoundError as task_file_not_found_error:
        print(
            f"[{datetime.datetime.now()}] '{task_file_not_found_error.__class__.__name__}' in tasks.csv, please ensure tasks.csv exists in this folder")
        input(f"[{datetime.datetime.now()}] Press X to exit \n")
        if selection == "X":
            sys.exit()
        else:
            sys.exit()
    reader_csv = csv.reader(task_csv)
    for line in reader_csv:
        task_list.append(line)

    task_csv.close()
    print(Fore.CYAN + f"{len(task_list) - 1} Tasks Loaded\n")
    input("Press enter to start!\n")


    thread_list = []
    for i in range(len(task_list)):
        task_info_c = task_list[i]
        try:
            if str(task_info_c[0]) != "LINK":
                thread = threading.Thread(target=amazon,
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
