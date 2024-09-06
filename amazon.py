import requests, re, json, time, base64, threading, lxml.html, random, datetime
import ast
from bs4 import BeautifulSoup as bs

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from amazoncaptcha import AmazonCaptcha

# undetected chromedriver
import undetected_chromedriver as uc
from subprocess import check_output


# ------------------------------------------------------------------------

def print_format(message):
    return print(f"[{datetime.datetime.now()}][AMAZON] {message.title()}")


def download_captcha(url):
    import urllib.request
    import urllib
    urllib.request.URLopener().retrieve(url, 'captcha_img.jpg')
    print_format("Successfully got captcha image, solving")
    files = {'file_contents': open('captcha_img.jpg', 'rb')}
    captcha_key = "d2acd4f5749452299eb834949c6de6b0"
    cap_in = requests.post(f'https://2captcha.com/in.php?key={captcha_key}&method=post&file_contents=', files=files)
    print_format("Captcha requested")
    if cap_in.text[0:2] == 'OK':
        captcha_id = cap_in.text[3:]
        cap_out = f'https://2captcha.com/res.php?key={captcha_key}&action=get&id={captcha_id}'
        while True:
            print_format("Waiting for Captcha")
            time.sleep(2)
            resp = requests.get(cap_out)
            if resp.text[0:2] == 'OK':
                print_format('captcha received')
                return resp.text[3:]
            else:
                continue

# noinspection PyAttributeOutsideInit
class amazon:
    def __init__(self):
        # options = uc.ChromeOptions()
        # options.headless=True
        # options.add_argument('--headless')
        # options.add_argument('--window-size=1920x1080')

        # try:
        #     cmd = r'wmic datafile where name="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" get Version /value'
        #     chrome_version = str(check_output(cmd)).split('Version=')[1].split(r"\r")[0]
        # except:
        #     chrome_version = None
        
        # uc.install(target_version=chrome_version)

        # self.driver = uc.Chrome(options=options)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"})
        self.mode = "drop"
        # self.link = 'https://www.www.amazon.com/dp/B07Y68P684'
        self.link = 'https://www.amazon.com/dp/B07Y68P684'
        
        # vars
        self.widget_state = ''
        self.customerId = ''
        self.addressID = ''
        self.purchaseID = ''
        self.instrumentID = ''
        self.address_link = ''

        # flow
        # if self.mode == "restock":
        #     self.monitor()
        self.get_cookies()
        time.sleep(1)
        self.atc()
        self.cart_link = f'https://www.amazon.com/gp/cart/desktop/go-to-checkout.html/ref=ox_sc_proceed?partialCheckoutCart=1&isToBeGiftWrappedBefore=0&proceedToRetailCheckout=Proceed+to+checkout&proceedToCheckout=1&cartInitiateId={str(self.id_gen())}'
        self.payment()
        # self.post_shipping_address(self.random_address())
        # self.random_address()
        # self.final()

    def get_cookies(self):
        while True:
            try:
                f = open(f"cookies.json", "r")
                data = json.load(f)
                f.close()
                cookie_str = ''

                cookie = random.choice([cookie["cookie"] for cookie in data["cookies"]])
                cookie_to_return = ast.literal_eval(base64.b64decode(cookie).decode("ascii"))
                
                for item in cookie_to_return:
                    # if item["name"] in ['sess-at-main', 'at-main', 'session-token', 'ubid-main', 'session-id', 'x-main', 'sst-main']:
                    self.session.cookies.set(item["name"], item["value"])
                    cookie_str = cookie_str + item['name'] + '=' + item['value'] + '; '

                cookie_str = cookie_str[:-2]
                self.session.headers.update({'cookie': cookie_str})
                return cookie_to_return
            except Exception as e:
                print_format(f"Exception {e} getting cookies")
                continue

    def rem_cookies(self):
        while True:
            try:
                # open file  
                f = open(f"cookies.json", "r+")  
                f.seek(0)  
                f.truncate()  
                f.close()
            except Exception as e:
                print_format(f"Exception {e} deleting cookies")
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

    def monitor(self):
        while True:
            main_page = self.session.get(self.link)
            if "Sign Out" not in main_page.text:
                threading.Thread(self.login())
            if "in stock" in main_page.text.lower():
                soup = bs(main_page.text, 'lxml')
                self.list_id = soup.find('input', {'name': 'offerListingID'})['value']
                self.asin = soup.find('input', {'name': 'ASIN'})['value']
                self.session_id = soup.find('input', {'name': 'session-id'})['value']
                self.merchant_id = soup.find('input', {'name': 'merchantID'})['value']
                print_format("in stock adding to cart")
                return
            else:
                print("out of stock")
                time.sleep(5)

    def atc(self):
        print_format('beginning add to cart')

        if self.mode != "restock":
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-language': 'en-US,en;q=0.9'
            }
            response = self.session.get(self.link, headers=headers)
            
            print_format("getting add to cart data")
            soup = bs(response.text, 'html.parser')

            
            
            target = soup.find('span', {'id': 'cr-state-object'})['data-state']
            dump = json.loads(target)
            self.customerId = dump['customerId']
            self.list_id = soup.find('input', {'name': 'offerListingID'})['value']
            self.asin = soup.find('input', {'name': 'ASIN'})['value']
            self.session_id = soup.find('input', {'name': 'session-id'})['value']
            self.merchant_id = soup.find('input', {'name': 'merchantID'})['value']
            csrf = soup.find('input', {'name': 'CSRF'})['value']
            rsid = soup.find('input', {'name': 'rsid'})['value']
            qid = soup.find('input', {'name': 'qid'})['value']
            sr = soup.find('input', {'name': 'sr'})['value']

            headers = {
                'authority': 'www.amazon.com',
                'cache-control': 'max-age=0',
                'rtt': '100',
                'downlink': '10',
                'ect': '4g',
                'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'upgrade-insecure-requests': '1',
                'origin': 'https://www.amazon.com',
                'content-type': 'application/x-www-form-urlencoded',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'referer': self.link,
                'accept-language': 'en-US,en;q=0.9'
            }
            data = {
                'CSRF': csrf,
                'offerListingID': self.list_id,
                'session-id': self.session_id,
                'ASIN': self.asin,
                'isMerchantExclusive': '0',
                'merchantID': self.merchant_id,
                'isAddon': '0',
                'nodeID': '',
                'sellingCustomerID': '',
                'qid': qid,
                'sr': sr,
                'storeID': '',
                'tagActionCode': '',
                'viewID': 'glance',
                'rebateId': '',
                'ctaDeviceType': 'desktop',
                'ctaPageType': 'detail',
                'usePrimeHandler': '0',
                'rsid': rsid,
                'sourceCustomerOrgListID': '',
                'sourceCustomerOrgListItemID': '',
                'wlPopCommand': '',
                'quantity': '1',
                'submit.add-to-cart': 'Add to Cart',
                'triggerTurboWeblab': '',
                'triggerTurboWeblabName': '',
                'turboPageRequestId': '',
                'turboPageSessionId': '',
                'dropdown-selection': '',
                'dropdown-selection-ubb': ''
            }
            while True:
                try:
                    # response = self.session.post('https://www.www.amazon.com/gp/product/handle-buy-box/ref=dp_start-bbf_1_glance', headers=headers, data=data)
                    response = self.session.post('https://www.amazon.com/gp/product/handle-buy-box/ref=dp_start-bbf_1_glance', headers=headers, data=data)
                    if response.status_code == 200:
                        # could potentially start receiving captcha for ATC (www.amazon captcha repository)
                        # returned lots of 503 errors during drop
                        print_format('atc done')
                        return
                    else:
                        print_format('error adding to cart: ' + str(response.status_code))   
                except Exception as e:
                    time.sleep(5)
                    continue  

    def random_address(self):
        headers = {
            'authority': 'www.amazon.com',
            'rtt': '50',
            'downlink': '10',
            'ect': '4g',
            'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.amazon.com/',
            'accept-language': 'en-US,en;q=0.9'
        }
        page = self.session.get(self.cart_link, headers=headers).text    

        if 'id="address-book-entry' in page:  # if you need to choose the address
            soup = bs(page, "html.parser")

            addresses = str(soup.find("form", {"class": "a-nostyle"}))
            random_address = addresses.split(f'id="address-book-entry')
            random_address.pop(0)
            random_address = random.choice(random_address)
            section = random_address.split("ship-to-this-address a-button a-button-primary a-button-span12 a-spacing-medium")[1]
            self.address_link = section
            self.address_link = self.address_link.split('href="')[1].split('"')[0]
            self.address_link = self.address_link.replace("amp;", "")
            self.address_link += "&hasWorkingJavascript=1"
            self.addressID = self.address_link.split('addressID=')[1].split('&')[0]
            self.purchaseID = self.address_link.split('purchaseId=')[1].split('&')[0]

            print('purchase id and address link')
            print_format(f"Purchase ID: {self.purchaseID}")
            print_format(f"Selecting address {self.address_link.split('addressID=')[1].split('&')[0]}")

            page = self.session.get('http://www.amazon.com' + self.address_link, headers=headers).text
        return page

    # noinspection PyMethodMayBeStatic
    def post_shipping_address(self, html_string):
        """
        Place your order means shipping address and method is already there

        Choose your shipping options means address is chosen but not method
        """


        if 'place your order' and 'choose your shipping options' not in html_string.lower():
            print_format('Cookies were expired, relogging to continue...')
            # self.rem_cookies()
            
            # print(html_string)
            print("FIX THIS POST SHIPPING SHIT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

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
            # 'guaranteeType_0_second-isoa': self.regex('name="guaranteeType_0_second-isoa" value="', html_string),
            'guaranteeType_0_second-isoa': 'GUARANTEED',
            'isShipWhenCompleteValid_0_second-isoa': self.regex('name="isShipWhenCompleteValid_0_second-isoa" value="', html_string),
            'isShipWheneverValid_0_second-isoa': self.regex('name="isShipWheneverValid_0_second-isoa" value="', html_string),
            'shipsplitpriority_0_second-isoa': self.regex('name="shipsplitpriority_0_second-isoa" value="', html_string),
            'order_0_ShippingSpeed': self.regex('name="order_0_ShippingSpeed" value="', html_string),
            'SSS_order_0_ShippingSpeed_std-us-5': self.regex('name="SSS_order_0_ShippingSpeed_std-us-5" value="', html_string),
            'shippingOfferingId_0_std-us-5': self.regex('name="shippingOfferingId_0_std-us-5" value="', html_string),
            # 'guaranteeType_0_std-us-5': self.regex('name="guaranteeType_0_std-us-5" value="', html_string),
            'guaranteeType_0_std-us-5': 'GUARANTEED',
            'isShipWhenCompleteValid_0_std-us-5': self.regex('name="isShipWhenCompleteValid_0_std-us-5" value="', html_string),
            'isShipWheneverValid_0_std-us-5': self.regex('name="sShipWheneverValid_0_std-us-5" value="', html_string),
            'shipsplitpriority_0_std-us-5': self.regex('name="shipsplitpriority_0_std-us-5" value="', html_string),
            'SSS_order_0_ShippingSpeed_second': self.regex('name="SSS_order_0_ShippingSpeed_second" value="', html_string),
            'shippingOfferingId_0_second': self.regex('name="shippingOfferingId_0_second" value="', html_string),
            # 'guaranteeType_0_second': self.regex('name="guaranteeType_0_second" value="', html_string),
            'guaranteeType_0_second': 'GUARANTEED',
            'isShipWhenCompleteValid_0_second': self.regex('name="isShipWhenCompleteValid_0_second" value="', html_string),
            'isShipWheneverValid_0_second': self.regex('isShipWheneverValid_0_second" value="', html_string),
            'shipsplitpriority_0_second': self.regex('name="shipsplitpriority_0_second" value="', html_string),
            'order_0_ShipSplitPreference': self.regex('name="order_0_ShipSplitPreference" value="', html_string),
            'lineItemEntityIds_0': self.regex('name="lineItemEntityIds_0" value="', html_string),
            'shippingOfferingId_0_sss-us-4': self.regex('name="lineItemEntityIds_0" value="', html_string),
            'SSS_order_0_ShippingSpeed_sss-us-4': self.regex('name="lineItemEntityIds_0" value="', html_string),
            # 'guaranteeType_0_sss-us-4': self.regex('name="lineItemEntityIds_0" value="', html_string),
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
        response = self.session.post('https://www.amazon.com/gp/buy/shared/handlers/async-continue.html/ref=chk_ship_option_continue', data=data, headers=headers)
        # print(response.text)
        if 'Select a payment method' in response.text:
            print_format('Application of shipping method successful.')
            # print(response.text)
            text = json.loads(response.text.split('var options = ')[1].split(';')[0])
            self.widget_state = text['serializedState']
            self.customerId = text['customerId']
        else:
            print_format('Error applying shipping method, retrying...')
            # print(response.text)
            # loop
            
    def payment(self):

        headers = {
            'authority': 'www.amazon.com',
            'rtt': '50',
            'downlink': '10',
            'ect': '4g',
            'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.amazon.com/',
            'accept-language': 'en-US,en;q=0.9'
        }
        response = self.session.get(self.cart_link, headers=headers)  
        # print(response.text)

        soup = bs(response.text, 'html.parser')
        self.widget_state = soup.find('input', {'name': 'ppw-widgetState'})['value']

        print(self.widget_state)

        # headers = {
        #     'Accept': 'application/json, text/javascript, */*; q=0.01',
        #     'X-Requested-With': 'XMLHttpRequest',
        #     'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        #     'Accept-Language': 'en-US,en;q=0.9',
        # }
        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'Widget-Ajax-Attempt-Count': '0',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'APX-Widget-Info': 'Checkout/desktop/h4sw4zzfGn27',
            'sec-ch-ua-platform': '"Windows"',
            'Origin': 'https://apx-security.amazon.com',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://apx-security.amazon.com/cpe/pm/register',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        data = {
            'ppw-widgetEvent:AddCreditCardEvent': '',
            'ppw-jsEnabled': 'true',
            'ppw-widgetState': self.widget_state,
            'ie': 'UTF-8',
            'addCreditCardNumber': '5297 3603 5673 1371',
            'ppw-accountHolderName': 'Alex Sheets',
            'ppw-expirationDate_month': '10',
            'ppw-expirationDate_year': '2024'
        }
        response = self.session.post(
            f'https://apx-security.www.amazon.com/payments-portal/data/f1/widgets2/v1/customer/{self.customerId}/continueWidget',
            headers=headers, params=(('sif_profile', 'APX-Encrypt-All-NA'),), data=data)
        if response.status_code == 200:
            print_format('successful submission of payment info')
            self.instrumentID = response.text[132:178]
            return

    def final(self):

        print_format('beginning finalize')

        # rejects prime offer
        headers = {
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
        data = {
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
        response = self.session.post('https://www.amazon.com/gp/buy/shared/handlers/async-continue.html/ref=prime_pdp_ho_nt_sov', headers=headers, data=data)

        # these two requests take us to choosing billing address
        headers = {
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
        data = {
            'ppw-widgetState': self.widget_state,
            'ie': 'UTF-8',
            'ppw-instrumentRowSelection': 'instrumentId=' + self.instrumentID + '&isExpired=false&paymentMethod=CC&tfxEligible=false',
            'ppw-jsEnabled': 'true',
            'ppw-widgetEvent:SetPaymentPlanSelectContinueEvent': '',
            'isAsync': '1',
            'isClientTimeBased': '1',
            'handler': '/gp/buy/payselect/handlers/apx-submit-continue.html'
        }
        response = self.session.post('https://www.amazon.com/gp/buy/shared/handlers/async-continue.html', headers=headers, data=data)

        headers = {
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
        data = {
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
        response = self.session.post('https://www.amazon.com/gp/buy/shared/handlers/async-continue.html/ref=ox_billing_ship_to_this_1', headers=headers, data=data)

        # we scrape continue link from response
        # its the final review order page link
        soup = bs(response.text, "html.parser")
        addresses = str(soup.find("form", {"class": "a-nostyle"}))
        random_address = addresses.split(f'id="address-book-entry')
        random_address.pop(0)
        random_address = random.choice(random_address)
        section = random_address.split("ship-to-this-address a-button a-button-primary a-button-span12 a-spacing-medium")[1]
        checkout_link = section
        checkout_link = checkout_link.replace("amp;", "")
        checkout_link = checkout_link.split('href="')[1].split('"')[0]

        response = self.session.get('https://www.amazon.com' + checkout_link)

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
        response = self.session.post('https://www.amazon.com/gp/buy/spc/handlers/static-submit-decoupled.html/ref=ox_spc_place_order?ie=UTF8&hasWorkingJavascript=',
            headers=headers, data=data)

        # will obv need better error handling, i just know if it gets here it works 
        if response.status_code == 200:
            print_format('check email!')
        else:
            print_format('error occurred finalizing checkout;')
            print_format('open the account in browser.')
            print_format('the item should still be in cart.')


amazon()
