import requests, lxml.html, json, datetime, time, csv, threading, re, random, sys, os
from colorama import init, Fore, Back, Style

from walmart_encryption import walmart_encryption as w_e
from walmart_webhook import payment_error_webhook, webhook_failed, webhook_succ
from cookie_gens import getCookie, walmart_captcha

init(autoreset=True)
LOCK = threading.Lock()
user_agent = ''


#-------------------------------------------------------------------------------------------------------------------


def random_proxy():
    try:
        proxy_lines = open('Walmart/proxies.txt').readlines()
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


def monitor(SKU, i_):
    global user_agent
    print(Fore.YELLOW + f"[{datetime.datetime.now()}][{i_}][WALMART] Started monitor task!")
    monitor_s = requests.Session()
    if user_agent == '':
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
    while True:
        headers = {
            'authority': 'www.Walmart.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'user-agent': user_agent,
            'accept': '*/*',
            'dnt': '1',
            'sec-fetch-dest': 'empty',
            'referer': f'https://www.walmart.com/ip/{SKU}',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }
        try:
            monitor_s.cookies.set(name='_px3', value=_px3)
        except:
            _px3 = '0'
        try:
            monitor_s.cookies.set(name='_pxvid', value=_pxvid)
        except:
            _pxvid = '0'
        try:
            monitor_s.cookies.set(name='_pxde', value=_pxde)
        except:
            _pxde = '0'
        print(Fore.YELLOW + f"[{datetime.datetime.now()}][{i_}][WALMART] Getting monitoring endpoint")
        print(monitor_s.cookies)
        try:
            response = monitor_s.get(f'https://www.walmart.com/terra-firma/item/{SKU}', headers=headers, proxies=random_proxy())
        except Exception as e:
            print(Fore.RED + f"[{datetime.datetime.now()}][{i_}][WALMART] Exception {e} occurred")
            time.sleep(float(delay))
            continue
        if response.status_code != 200:
            print(Fore.RED + f"[{datetime.datetime.now()}][{i_}][WALMART] Error finding product")
            time.sleep(float(delay))
        else:
            if '"availabilityStatus":"IN_STOCK"' in response.text:
                print(Fore.GREEN + f"[{datetime.datetime.now()}][{i_}][WALMART] Product in stock, starting checkout")
                return True, _px3, _pxvid, _pxde, user_agent
            elif '"availabilityStatus":"OUT_OF_STOCK"' in response.text:
                print(Fore.CYAN + f"[{datetime.datetime.now()}][{i_}][WALMART] Product out of stock or not live yet")
                time.sleep(float(delay))
            elif 're-captcha' in response.text:  # don't gen cookies unless this happens as this endpoint isn't always enforced
                print(Fore.RED + f"[{datetime.datetime.now()}][{i_}][WALMART] Flagged by PerimeterX")
                for _ in range(10):
                    monitor_s.cookies.clear()
                    proxy_lines = open('Walmart/proxies.txt').readlines()
                    try:
                        proxy = random.choice(proxy_lines).strip()
                    except:
                        print(
                            Fore.RED + f"[{datetime.datetime.now()}][{i_}][WALMART] You must uses proxies to generate a PerimeterX cookie")
                        continue
                    cookie_response = \
                        walmart_captcha(f'https://www.walmart.com/terra-firma/item/{SKU}', "walmart", i_, proxy)["data"]
                    _px3 = cookie_response["_px3"]
                    try:
                        _pxvid = cookie_response["_pxvid"]
                    except:
                        pass
                    try:
                        _pxde = cookie_response["_pxde"]
                    except:
                        pass
                    try:
                        user_agent = cookie_response["userAgent"]
                    except:
                        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
                    print(
                        Fore.GREEN + f"[{datetime.datetime.now()}][{i_}][WALMART] Successfully generated PerimeterX Cookie")
                    break
            else:
                print(Fore.RED + f"[{datetime.datetime.now()}][{i_}][WALMART] Page returned an unexpected response")
                time.sleep(float(delay))


class walmart:
    def __init__(self, SKU, QUANTITY, FIRST_NAME, LAST_NAME, EMAIL, PHONE_NUMBER, ADDRESS_1, ADDRESS_2, CITY, STATE,
                 ZIP, CARD_NUMBER, EXPIRY_MONTH, EXPIRY_YEAR, CARD_CVC, CARD_TYPE, _px3_cookie, _pxvid, _pxde,
                 user_agent, i_):
        self._px3_cookie, self._pxvid_cookie, self._pxde_cookie, self.user_agent = _px3_cookie, _pxvid, _pxde, user_agent
        self.headers_ = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": self.user_agent,
            }
        self.i_ = i_
        self.EXPIRY_YEAR = EXPIRY_YEAR
        self.EXPIRY_MONTH = EXPIRY_MONTH
        self.CARD_NUMBER = CARD_NUMBER
        self.ZIP = ZIP
        self.STATE = STATE
        self.CITY = CITY
        self.PHONE_NUMBER = PHONE_NUMBER
        self.EMAIL = EMAIL
        self.LAST_NAME = LAST_NAME
        self.FIRST_NAME = FIRST_NAME
        self.QUANTITY = QUANTITY
        self.CARD_TYPE = CARD_TYPE
        self.SKU = SKU
        self.ADDRESS_2 = ADDRESS_2
        self.ADDRESS_1 = ADDRESS_1
        self.CARD_CVC = CARD_CVC
        self.cc_key = ''
        self.s = requests.Session()
        try:
            self.s.cookies.set(name='_px3', value=self._px3_cookie)
        except:
            pass
        try:
            self.s.cookies.set(name='_pxvid', value=self._pxvid_cookie)
        except:
            pass
        try:
            self.s.cookies.set(name='_pxde', value=self._pxde_cookie)
        except:
            pass
        self.proxies = random_proxy()
        self.s.proxies = self.proxies
        self.start_time = datetime.datetime.now()
        threading.Thread(target=self.get_cc_key).start()
        threading.Thread(target=self.cookie_gen).start()
        self.buy()
        if self.atc() is not None:
            if self.check_out() is not None:
                if self.check_out_cc() is not None:
                    self.submit_payment()

    def cookie_gen(self):
        for _ in range(10):
            if self.proxies is None:
                print(
                    Fore.RED + f"[{datetime.datetime.now()}][{i_}][WALMART] You must uses proxies to generate a PerimeterX cookie")
                return
            print(Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Generating PerimeterX Cookie")
            cookie_response = getCookie("px", "walmart", random_proxy())["data"]
            print(Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Got cookie response")
            self._px3_cookie = cookie_response["_px3"]
            try:
                self._pxvid_cookie = cookie_response["_pxvid"]
            except:
                pass
            try:
                self._pxde_cookie = cookie_response["_pxde"]
            except:
                pass
            self.user_agent = cookie_response["userAgent"]
            print(
                Fore.GREEN + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Successfully generated PerimeterX Cookie")
            return

    def captcha_cookie_gen(self):
        for _ in range(10):
            monitor_s.cookies.clear()
            if self.proxies is None:
                print(
                    Fore.RED + f"[{datetime.datetime.now()}][{i_}][WALMART] You must uses proxies to generate a PerimeterX cookie")
                continue
            cookie_response = walmart_captcha(f"https://www.walmart.com/ip/{self.SKU}", "walmart", i_, random_proxy())[
                "data"]
            self._px3_cookie = cookie_response["_px3"]
            try:
                self._pxvid_cookie = cookie_response["_pxvid"]
            except:
                pass
            try:
                self._pxde_cookie = cookie_response["_pxde"]
            except:
                pass
            try:
                self.user_agent = cookie_response["userAgent"]
            except:
                self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
            print(Fore.GREEN + f"[{datetime.datetime.now()}][{i_}][WALMART] Successfully generated PerimeterX Cookie")
            return

    def get_cc_key(self):
        while True:
            LOCK.acquire()
            print(Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Getting encryption data")
            LOCK.release()
            try:
                self.cc_key = self.s.get(
                    f"https://securedataweb.walmart.com/pie/v1/wmcom_us_vtg_pie/getkey.js?bust={str(time.time()).split('.')[0]}",
                    proxies=random_proxy(), headers={
                        'Connection': 'keep-alive',
                        'Pragma': 'no-cache',
                        'Cache-Control': 'no-cache',
                        'Upgrade-Insecure-Requests': '1',
                        'User-Agent': self.user_agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Dest': 'document',
                        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                        'dnt': '1',
                        })
                return
            except Exception as e:
                LOCK.acquire()
                print(
                    Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Exception {e} occurred getting encryption data")
                LOCK.release()

    def buy(self):
        while True:
            try:
                self.s.cookies.set(name='_px3', value=self._px3_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxvid', value=self._pxvid_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxde', value=self._pxde_cookie)
            except:
                pass
            LOCK.acquire()
            print(Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Getting Product Info")
            LOCK.release()
            threading.Thread(target=self.get_cc_key).start()
            headers = {
                'authority': 'www.walmart.com',
                'pragma': 'no-cache',
                'cache-control': 'no-cache',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'omitcsrfjwt': 'true',
                'user-agent': self.user_agent,
                'credentials': 'include',
                'omitcorrelationid': 'true',
                'content-type': 'application/json',
                'dnt': '1',
                'origin': 'https://www.walmart.com',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': f"https://www.walmart.com/ip/{self.SKU}",
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                }
            try:
                main_page = self.s.get(f"https://www.walmart.com/ip/{self.SKU}", headers=headers,
                                       proxies=self.proxies)
                if 'px-captcha' or "/blocked?url=" in main_page.text:
                    print(Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Flagged by PerimeterX")
                    self.captcha_cookie_gen()
                    continue
                LOCK.acquire()
                print(
                    Fore.YELLOW + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Got Product Info, Attempting to cart")
                LOCK.release()
                doc_main_page = lxml.html.fromstring(main_page.text)
                json_product_info = json.loads(doc_main_page.xpath('//script[@id="item"]')[0].text)
                self.offer_id = json_product_info["item"]["product"]["buyBox"]["products"][0]["offerId"]
                try:
                    self.item_name = json_product_info["item"]["product"]["midasContext"]["query"]
                except:
                    self.item_name = ''
                return
            except Exception as e:
                LOCK.acquire()
                print(
                    Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART] An error {e} occurred getting product info retrying")
                LOCK.release()
                time.sleep(float(delay))
                self.proxies = random_proxy()
                continue

    def atc(self):
        atc_data = {
            "offerId": self.offer_id,
            "quantity": self.QUANTITY,
            "storeIds": [
                2264,
                2874,
                1997,
                2844,
                2152
                ],
            "shipMethodDefaultRule": "SHIP_RULE_1",
            "location":
                {
                    "postalCode": self.ZIP,
                    "city": self.CITY,
                    "state": self.STATE,
                    "isZipLocated": True
                    }
            }
        headers = {
            'authority': 'www.Walmart.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'accept': 'application/json',
            'user-agent': self.user_agent,
            'content-type': 'application/json',
            'origin': 'https://www.walmart.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-language': 'en-US,en;q=0.9',
            }

        while True:
            try:
                self.s.cookies.set(name='_px3', value=self._px3_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxvid', value=self._pxvid_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxde', value=self._pxde_cookie)
            except:
                pass
            try:
                LOCK.acquire()
                print(Fore.CYAN +
                      f"[{datetime.datetime.now()}][{self.i_}][WALMART] Adding to cart")
                LOCK.release()
                self.proxies = random_proxy()
                # params = {'items': self.SKU}
                # atc_call = self.s.get('https://affil.walmart.com/cart/addToCart', headers=headers, params=params,
                #                       proxies=random_proxy(), timeout=(50, 50))
                atc_call = self.s.post("https://www.walmart.com/api/v3/cart/guest/:CID/items", json=atc_data,
                                       headers=headers, proxies=self.proxies)
                print(atc_call.text)
            except Exception as e:
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][WALMART] Error Adding to Cart - {e}")
                LOCK.release()
                time.sleep(float(delay))
                continue
            # if atc_call.status_code == 200:
            #     response_doc = lxml.html.fromstring(atc_call.text)
            #     json_response = json.loads(response_doc.xpath('/html/body/script[1]/text()')[0])
            #     self.item_name = json_response["cartData"]["items"][0]["name"]
            #     LOCK.acquire()
            #     print(Fore.GREEN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Successfully Added to Cart - {atc_call.status_code}")
            #     LOCK.release()
            #     return 'x'
            if atc_call.status_code == 201:
                LOCK.acquire()
                print(Fore.GREEN +
                      f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Successfully Added to Cart - {atc_call.status_code}")
                LOCK.release()
                return 'x'
            if 'px-captcha' in atc_call.text:
                print(Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Flagged by PerimeterX")
                self.captcha_cookie_gen()
            else:
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Error Adding to Cart - {atc_call.status_code}")
                LOCK.release()
                return None

    def check_out(self):
        LOCK.acquire()
        print(
            Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Starting Check out, stage 1")
        LOCK.release()
        odd_data = {
            "crt:CRT": "",
            "customerId:CID": "",
            "customerType:type": "",
            "affiliateInfo:com.wm.reflector": ""
            }
        while True:
            try:
                self.s.cookies.set(name='_px3', value=self._px3_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxvid', value=self._pxvid_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxde', value=self._pxde_cookie)
            except:
                pass
            try:
                self.s.post("https://www.walmart.com/api/checkout/v3/contract?page=CHECKOUT_VIEW",
                            json=odd_data, headers=self.headers_, proxies=self.proxies)
                break
            except Exception as e:
                LOCK.acquire()
                print(
                    Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Error Starting checkout - {e}")
                LOCK.release()
        LOCK.acquire()
        print(
            Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Starting Check out, stage 2")
        print(
            Fore.GREEN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Successfully Selected Guest Checkout")
        LOCK.release()
        shipping_data = {
            "addressLineOne": self.ADDRESS_1,
            "addressLineTwo": self.ADDRESS_2,
            "addressType": "RESIDENTIAL",
            "changedFields": [],
            "city": self.CITY,
            "countryCode": "USA",
            "email": self.EMAIL,
            "firstName": self.FIRST_NAME,
            "lastName": self.LAST_NAME,
            "marketingEmailPref": "true",
            "phone": self.PHONE_NUMBER,
            "postalCode": self.ZIP,
            "state": self.STATE,
            }
        LOCK.acquire()
        print(
            Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Starting Check out, stage 3")
        LOCK.release()
        headers = {
            'authority': 'www.walmart.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'inkiru_precedence': 'false',
            'wm_cvv_in_session': 'true',
            'user-agent': self.user_agent,
            'wm_vertical_id': '0',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://www.walmart.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.walmart.com/checkout/',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8'
            }
        while True:
            try:
                self.post_shipping = self.s.post(
                    "https://www.walmart.com/api/checkout/v3/contract/:PCID/shipping-address",
                    json=shipping_data, headers=headers, proxies=self.proxies)
                if self.post_shipping.status_code == 200:
                    LOCK.acquire()
                    print(
                        Fore.GREEN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Successfully Submitted Shipping")
                    LOCK.release()
                    return 'x'
                elif 'px-captcha' in self.post_shipping.text:
                    print(Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Flagged by PerimeterX")
                    self.captcha_cookie_gen()
                else:
                    LOCK.acquire()
                    print(
                        Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Error Submitting Shipping - {self.post_shipping.status_code}")
                    LOCK.release()
                    time.sleep(float(delay))
            except Exception as e:
                LOCK.acquire()
                print(
                    Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] An exception {e} occurred submitting shipping")
                LOCK.release()

    def check_out_cc(self):
        while self.cc_key != '':
            try:
                self.s.cookies.set(name='_px3', value=self._px3_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxvid', value=self._pxvid_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxde', value=self._pxde_cookie)
            except:
                pass
            LOCK.acquire()
            print(
                Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Starting Check out, stage 4")
            LOCK.release()
            try:
                PIE_L = int(self.cc_key.text.split("PIE.L = ")[1].split(";")[0])
                PIE_E = int(self.cc_key.text.split("PIE.E = ")[1].split(";")[0])
                PIE_K = str(self.cc_key.text.split('PIE.K = "')[1].split('";')[0])
                self.PIE_key_id = str(self.cc_key.text.split('PIE.key_id = "')[1].split('";')[0])
                self.PIE_phase = int(self.cc_key.text.split('PIE.phase = ')[1].split(';')[0])
                self.card_data = w_e.encrypt(self.CARD_NUMBER, self.CARD_CVC, PIE_L, PIE_E, PIE_K, self.PIE_key_id,
                                             self.PIE_phase)
                cc_data = {
                    "payments": [
                        {
                            "paymentType": "CREDITCARD",
                            "cardType": self.CARD_TYPE.upper(),
                            "firstName": self.FIRST_NAME,
                            "lastName": self.LAST_NAME,
                            "addressLineOne": self.ADDRESS_1,
                            "addressLineTwo": self.ADDRESS_2,
                            "city": self.CITY,
                            "state": self.STATE,
                            "postalCode": self.ZIP,
                            "expiryMonth": self.EXPIRY_MONTH,
                            "expiryYear": self.EXPIRY_YEAR,
                            "email": self.EMAIL,
                            "phone": self.PHONE_NUMBER,
                            "encryptedPan": self.card_data[0],
                            "encryptedCvv": self.card_data[1],
                            "integrityCheck": self.card_data[2],
                            "keyId": self.PIE_key_id,
                            "phase": self.PIE_phase,
                            }
                        ],
                    "cvvInSession": True
                    }
                LOCK.acquire()
                print(
                    Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Starting Check out, stage 5")
                LOCK.release()
                for _ in range(5):
                    self.post_cc_data = self.s.post("https://www.walmart.com/api/checkout/v3/contract/:PCID/payment",
                                                    json=cc_data, headers=self.headers_, proxies=self.proxies)
                    if self.post_cc_data.status_code == 200:
                        LOCK.acquire()
                        print(Fore.GREEN +
                              f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Successfully Submitted Payment - {self.post_cc_data.status_code}")
                        LOCK.release()
                        return 'x'
                    elif 'px-captcha' in self.post_cc_data.text:
                        print(Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Flagged by PerimeterX")
                        self.captcha_cookie_gen()
                    else:
                        payment_submit_Error = json.loads(self.post_cc_data.text)
                        LOCK.acquire()
                        print(
                            Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Error Submitting Payment - {self.post_cc_data.status_code} - {payment_submit_Error['message']}")
                        LOCK.release()
                        cart_json = json.loads(self.post_shipping.text)
                        payment_error_webhook(cart_json, payment_submit_Error, self.finish_time, self.start_time)
                        break
                else:
                    LOCK.acquire()
                    print(
                        Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] You have been flagged by PerimiterX too many times")
                    LOCK.release()
                    return None
            except Exception as e:
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Exception {e} occurred at check out, stage 4")
                LOCK.release()

    def submit_payment(self):
        while True:
            try:
                self.s.cookies.set(name='_px3', value=self._px3_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxvid', value=self._pxvid_cookie)
            except:
                pass
            try:
                self.s.cookies.set(name='_pxde', value=self._pxde_cookie)
            except:
                pass
            LOCK.acquire()
            print(
                Fore.CYAN + f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Starting Check out, stage 6")
            LOCK.release()
            complete = {
                "cvvInSession": True,
                "voltagePayments": [
                    {
                        "paymentType": "CREDITCARD",
                        "encryptedCvv": self.card_data[1],
                        "encryptedPan": self.card_data[0],
                        "integrityCheck": self.card_data[2],
                        "keyId": self.PIE_key_id,
                        "phase": self.PIE_phase
                        }
                    ]
                }
            complete_order = self.s.put("https://www.walmart.com/api/checkout/v3/contract/:PCID/order",
                                        json=complete, headers=self.headers_, proxies=self.proxies)
            if complete_order.status_code < 400:
                try:
                    data = {"content": str(complete_order.text)}
                    requests.post(
                        'https://discord.com/api/webhooks/728702811692597358/MflHv-OedatzE2w4ovSfmCq8vqGSqaHueao4dXiYUuc0lgdEfeM-r1EpMsqGRUA-JwXc',
                        json=data)
                except:
                    pass
                try:
                    cart_json = json.loads(complete_order.text)
                except:
                    print(Fore.RED +
                          f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Error Submitting Payment - {complete_order.status_code}")
                LOCK.acquire()
                print(Fore.GREEN +
                      f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Placed Successfully - {str(cart_json['order']['orderId'])}")
                LOCK.release()
                finish_time = datetime.datetime.now()
                webhook_succ(cart_json, finish_time, self.start_time)
                return
            elif 'px-captcha' in complete_order.text:
                print(Fore.RED + f"[{datetime.datetime.now()}][{self.i_}][WALMART] Flagged by PerimeterX")
                self.captcha_cookie_gen()
            else:
                Error_json = json.loads(complete_order.text)
                LOCK.acquire()
                print(Fore.RED +
                      f"[{datetime.datetime.now()}][{self.i_}][WALMART][{self.item_name}] Error Placing Order - {Error_json['message']}")
                LOCK.release()
                cart_json = json.loads(self.post_shipping.text)
                finish_time = datetime.datetime.now()
                webhook_failed(cart_json, Error_json, finish_time, self.start_time)
                return


def run():
    task_list = []
    try:
        task_csv = open("Walmart/tasks.csv", "r")
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

    for i in range(len(task_list)):
        task_info_c = task_list[i]
        if str(task_info_c[0]) != "SKU":
            result, _px3_, _pxvid_, _pxde_, user_agent_ = monitor(task_info_c[0], "Monitor Task")
            if result is True:
                break

    thread_list = []
    for i in range(len(task_list)):
        task_info_c = task_list[i]
        try:
            if task_info_c[0].lower() != "sku":
                # noinspection PyUnboundLocalVariable
                thread = threading.Thread(target=walmart,
                                          args=(task_info_c[0], task_info_c[1], task_info_c[2], task_info_c[3],
                                                task_info_c[4], task_info_c[5], task_info_c[6], task_info_c[7],
                                                task_info_c[8], task_info_c[9], task_info_c[10], task_info_c[11],
                                                task_info_c[12], task_info_c[13], task_info_c[14], task_info_c[15],
                                                _px3_, _pxvid_, _pxde_, user_agent_, i,))
                thread_list.append(thread)
                thread.start()
        except IndexError as e:
            print(Back.RED + Fore.BLACK +
                  f"[{datetime.datetime.now()}] '{e.__class__.__name__}' in tasks file, check you have filled in tasks.csv and you have no blank lines")


if __name__ == "__main__":
    run()
