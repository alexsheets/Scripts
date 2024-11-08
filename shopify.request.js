// script imports, all installed to dependencies
import axios from 'axios';
import * as cheerio from 'cheerio';
import Captcha from '2captcha';

import { _log } from 'common/browser.js'
// import { SingleEntryPlugin } from 'webpack';
// import { window, document } from 'common/browser.js';

// -----------------------------------------------------------------

// setup local vars
let cookies = '';
let header_cookies_str = '';
let post_cap_cookies = '';
let token1 = '';
let token2 = '';
let new_link = '';
let total = '';
let ship_type = '';
let encrypted = '';
let instrumentID = '';
let choice = '';
let sitekey_chkpt = '';
let sitekey_cntct = '';
let cap_bool = false;

class Shopify {
    // init values
    // SITE IS SUPPLIED AT BOTTOM OF SCRIPT WHERE BOT IS INSTANTIATED
    constructor(site) {
        this.site = site;
    }

    /*
    Function for solving captcha and returning token.
    User's captcha key should be located in the solver parameters.
    */
    bypassCaptcha = async(sitekey) => {
        _log('Captcha received');
        const solver = new Captcha.Solver('d2acd4f5749452299eb834949c6de6b0');

        let cap_link = this.site + new_link;

        try {
            const { data } = await solver.recaptcha(
              sitekey,
              cap_link
            );
            _log('Captcha solved')
            return data;
        } catch (err) {
            _log('Error solving captcha');
        }
    }
    
    /*
    Grabs product based on keyword and size preference
    */
    keywordScrape = async() => {
        // vars for products to be looked through & boolean for item found
        let products;
        let bool = true;
        var keywords = payload.keywords + payload.style_name;
        var size_name = payload.size_name;
        try {
            await axios
                .get(this.site + '/products.json?limit=20', {
                    headers: {
                        'pragma': 'no-cache',
                        'cache-control': 'no-cache',
                        'upgrade-insecure-requests': '1',
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    },
                })
                .then(function (response) {
                    // store products as JSON
                    products = JSON.parse(JSON.stringify(response.data.products));
        
                    // loop through products
                    for (var i=0; i<products.length; i++) {
                        // create a string of the title and its description to look for keywords
                        var title = products[i].title;
                        var body = products[i].body_html;
                        var new_body = body.replace(/(<([^>]+)>)/ig, '');
                        var str = title + new_body;

                        // for each keyword
                        for (var j=0; j<keywords.length; j++) {
                            // look for positive keywords
                            if (str.includes(keywords[j])) {
                                // if string contains one of keywords currently bool is true
                                bool = true;
                            } else {
                                // if not then set false and continue to look
                                bool = false;
                            }
                            
                        }
                        // if boolean flag is still true, the product contains correct keywords
                        if (bool) {
                            if (products[i].variants.length > 1) {
                                // look for title in loop of variants that matches size we want
                                for (var j=0; j<products[i].variants.length; j++) {
                                    var size = products[i].variants[j].title;
                                    if (size === size_name) {
                                        choice = products[i].variants[j].id;
                                    }
                                }
                            } else {
                                // there is only one variant
                                choice = products[i].variants.id;
                            }
                        }
                    }
                })
                .catch(function (error) {
                    _log('Product not live yet, pausing for delay and retrying. . .');
                });
        } catch (error) {
            _log('Product not live yet, pausing for delay and retrying. . .');
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
        }
    }

    /*
    Request to checkpoint endpoint using cookies grabbed from keyword scraping
    */
    checkpointScrape = async() => {
        try {
            await axios
                .get(this.site + '/checkpoint', {
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'upgrade-insecure-requests': '1',
                    },
                })
                .then(function (response) {
                    var body = response.data;
                    const $ = cheerio.load(body);
                    var htmlStr = $.html();

                    // scrape checkpoint-specific sitekey and auth token
                    if (htmlStr.includes('sitekey')) {
                        var sk_html = htmlStr.split('sitekey: "')[1];
                        sitekey_chkpt = sk_html.split('",')[0];
                    }
                    let new_str = htmlStr.split('authenticity_token')[1];
                    token1 = new_str.split('value="')[1];
                    token1 = token1.split('"')[0];
                })
                .catch(function (error) {
                    // handle error
                    _log('Error retrieving checkpoint');
                    return this.checkpointScrape();
                });
        } catch (e) {
            _log('Error retrieving checkpoint');
            // set to config delay in future
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.checkpointScrape();
        }
    }

    /*
    Submit checkpoint data including first auth token and checkpoint captcha token
    */
    checkpointSubmit = async(captcha_token) => {

        // setup payload including scraped auth token and captcha response
        const chkpt_params = new URLSearchParams();
        chkpt_params.append('authenticity_token', token1);
        chkpt_params.append('g-recaptcha-response', captcha_token);
        chkpt_params.append('data_via', 'cookie');

        try {
            await axios
                .post(this.site + '/checkpoint', chkpt_params, {
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'cookie': init_cookies,
                        'origin': this.site,
                        'referer': this.site + '/checkpoint',
                        'upgrade-insecure-requests': '1',
                    },
                })
                .then(function (response) {
                    // grab cookies, should now be attributed to solved checkpoint
                    _log('Checkpoint passed')
                    post_cap_cookies = response.headers['set-cookie'];
                })
                .catch(function (error) {
                    // handle error
                    _log('Checkpoint submission error');
                    return this.checkpointScrape();
                });
        } catch (e) {
            _log('Checkpoint submission error');
            // set to config delay in future
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.checkpointScrape();
        }
    }

    /*
    ATC; uses the add.js file most shopify sites have.
    */
    addToCart = async() => {
        // add to cart using cookies from submitted checkpoint
        try {
            await axios
                .post(this.site + '/cart/add.js', {
                    form_type: 'product',
                    id: choice,
                    headers: {
                        'cookies': post_cap_cookies,
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'x-requested-with': 'XMLHttpRequest'
                    },
                })
                .then(function (response) {
                    // log success of atc
                    _log('ATC success');
                    cookies = response.headers['set-cookie'];
                })
                .catch(function (error) {
                    _log('ATC error');
                    return this.addToCart();
                });
        } catch (e) {
            _log('ATC error');
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.addToCart();
        }
    }

    /*
    Submits the cart change, important to retrieve cookies from this req.
    Also will scrape sitekey if there is a captcha on the cart page (ie kith).
    */
    postATC = async() => {

        // submits the atc, proceeds the checkout
        const atc_params = new URLSearchParams();
        atc_params.append('updates[]', '1');
        atc_params.append('attributes[checkout_clicked]', 'true');
        atc_params.append('checkout', '');

        try {
            await axios
                .post(this.site + '/cart', atc_params, { 
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'cookie': cookies,
                        'upgrade-insecure-requests': '1',
                    } 
                })
                .then(function (response) {
                    var body = response.data;
                    const $ = cheerio.load(body);
                    var htmlStr = $.html();

                    // if the page includes a captcha this will scrape the sitekey associated
                    if (htmlStr.includes('sitekey')) {
                        var sk_html = htmlStr.split('sitekey: "')[1];
                        sitekey_cntct = sk_html.split('",')[0];
                        cap_bool = true;
                    }
                    // scrapes new path for checkout link 
                    // as well as a new auth token
                    new_link = htmlStr.split('edit_checkout')[1];
                    token2 = new_link.split('token" value="')[1];
                    token2 = token2.split('"')[0];
                    new_link = new_link.split('action="')[1];
                    new_link = new_link.split('" ')[0];

                    // set new cookies
                    header_cookies_str = response.headers['set-cookie'];

                })
                .catch(function (error) {
                    // handle error
                    _log('Cart error');
                    return this.postATC();
                });
        } catch (e) {
            _log('Cart error');
            // set to config delay in future
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.postATC();
        }
    }

    /*
    Inputs user contact info and supplies captcha token if necessary
    */
    autofillContactInformation = async(captcha_token) => {
    
        const form_data = new URLSearchParams();
        form_data.append('_method', 'patch');
        form_data.append('authenticity_token', token2);
        form_data.append('previous_step', 'contact_information');
        form_data.append('step', 'shipping_method');
        form_data.append('checkout[email]', profile.contact.email);
        form_data.append('checkout[buyer_accepts_marketing]', '0');
        form_data.append('checkout[buyer_accepts_marketing]', '1');
        form_data.append('checkout[shipping_address][first_name]', profile.contact.firstName);
        form_data.append('checkout[shipping_address][last_name]', profile.contact.lastName);
        form_data.append('checkout[shipping_address][address1]', profile.shipping.street);
        form_data.append('checkout[shipping_address][address2]', );
        form_data.append('checkout[shipping_address][city]', profile.shipping.city);
        form_data.append('checkout[shipping_address][country]', profile.shipping.country);
        form_data.append('checkout[shipping_address][province]', profile.shipping.state);
        form_data.append('checkout[shipping_address][zip]', profile.shipping.zipcode);
        form_data.append('checkout[shipping_address][phone]', profile.contact.phone);
        // HARD CODED INFORMATION
        form_data.append('checkout[client_details][browser_height]', '625');
        form_data.append('checkout[client_details][browser_width]', '786');
        form_data.append('checkout[client_details][javascript_enabled]', '1');
        form_data.append('checkout[client_details][color_depth]', '24');
        form_data.append('checkout[client_details][java_enabled]', 'false');
        form_data.append('checkout[client_details][browser_tz]', '300');
        // CAPTCHA SOLVED RESPONSE TOKEN
        form_data.append('g-recaptcha-response', captcha_token);

        // submit request to the site's new link we scraped from submitting atc
        try {
            await axios
                .post(this.site + new_link, form_data, { 
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'cookie': header_cookies_str,
                        'content-type': 'application/x-www-form-urlencoded',
                        'upgrade-insecure-requests': '1',
                    } 
                })
                .then(function (response) {
                    _log('Successfully submitted contact info');
                })
                .catch(function (error) {
                    // handle error
                    _log('Contact info submission error');
                    return this.autofillContactInformation();
                });
        } catch (e) {
            _log('Contact info submission error');
            // set to config delay in future
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.autofillContactInformation();
        }
    }

    /*
    Inputs user contact info without the need for a captcha token
    */
    autofillContactInformationNoCaptcha = async() => {
        const form_data = new URLSearchParams();
        form_data.append('_method', 'patch');
        form_data.append('authenticity_token', token2);
        form_data.append('previous_step', 'contact_information');
        form_data.append('step', 'shipping_method');
        form_data.append('checkout[email]', profile.contact.email);
        form_data.append('checkout[buyer_accepts_marketing]', '0');
        form_data.append('checkout[buyer_accepts_marketing]', '1');
        form_data.append('checkout[shipping_address][first_name]', profile.contact.firstName);
        form_data.append('checkout[shipping_address][last_name]', profile.contact.lastName);
        form_data.append('checkout[shipping_address][address1]', profile.shipping.street);
        form_data.append('checkout[shipping_address][address2]', '');
        form_data.append('checkout[shipping_address][city]', profile.shipping.city);
        form_data.append('checkout[shipping_address][country]', profile.shipping.country);
        form_data.append('checkout[shipping_address][province]', profile.shipping.state);
        form_data.append('checkout[shipping_address][zip]', profile.shipping.zipcode);
        form_data.append('checkout[shipping_address][phone]', profile.contact.phone);
        // HARD CODED INFORMATION
        form_data.append('checkout[client_details][browser_height]', '625');
        form_data.append('checkout[client_details][browser_width]', '786');
        form_data.append('checkout[client_details][javascript_enabled]', '1');
        form_data.append('checkout[client_details][color_depth]', '24');
        form_data.append('checkout[client_details][java_enabled]', 'false');
        form_data.append('checkout[client_details][browser_tz]', '300');
        // NO CAPTCHA TOKEN
        // form_data.append('checkout[attributes][I-agree-to-the-Terms-and-Conditions]', 'Yes');
    
        try {
            await axios
                .post(this.site + new_link, form_data, { 
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'cookie': header_cookies_str,
                        'content-type': 'application/x-www-form-urlencoded',
                        'upgrade-insecure-requests': '1',
                    } 
                })
                .then(function (response) {
                    _log('Successfully submitted contact info');
                })
                .catch(function (error) {
                    // handle error
                    _log('Contact info submission error');
                    return this.autofillContactInformationNoCaptcha();
                });
        } catch (e) {
            _log('Contact info submission error');
            // set to config delay in future
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.autofillContactInformationNoCaptcha();
        }
    }

    /*
    Scrapes shipping method from the shipping choice page
    */
    scrapeShippingMethod = async() => {
        try {
            await axios
                .get(this.site + new_link, { 
                    params: {
                        'previous_step': 'contact_information',
                        'step': 'shipping_method'
                    },
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'cookie': header_cookies_str,
                        'content-type': 'application/x-www-form-urlencoded',
                        'upgrade-insecure-requests': '1',
                    } 
                })
                .then(function (response) {
                    // scrapes the shipping method
                    var body = response.data;
                    const $ = cheerio.load(body);
                    // uses cheapest one /first one found
                    ship_type = $(".input-radio").attr('value');
                })
                .catch(function (error) {
                    // handle error
                    return this.scrapeShippingMethod();
                });
        } catch(err) {
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.scrapeShippingMethod();
        }
    }

    /*
    Important request as it submits the shipping choice and we retrieve total price for checkout
    */
    submitShipping = async() => {

        const form_data = new URLSearchParams();
        form_data.append('_method', 'patch');
        form_data.append('authenticity_token', token2);
        form_data.append('previous_step', 'shipping_method');
        form_data.append('step', 'payment_method');
        form_data.append('checkout[shipping_rate][id]', ship_type);
        form_data.append('checkout[client_details][browser_width]', '786');
        form_data.append('checkout[client_details][browser_height]', '625');
        form_data.append('checkout[client_details][javascript_enabled]', '1');
        form_data.append('checkout[client_details][color_depth]', '24');
        form_data.append('checkout[client_details][java_enabled]', 'false');
        form_data.append('checkout[client_details][browser_tz]', '300');

        try {
            await axios
                .post(this.site + new_link, form_data, { 
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'cookie': header_cookies_str,
                        'content-type': 'application/x-www-form-urlencoded',
                        'upgrade-insecure-requests': '1',
                    } 
                })
                .then(function (response) {
                    let body = response.data;
                    const $ = cheerio.load(body);
                    // scrapes total price after attributing shipping
                    total = $(".payment-due__price").attr('data-checkout-payment-due-target');
                    _log('Shipping choice submitted');
                })
                .catch(function (error) {
                    // handle error
                    _log('Shipping submission error');
                    return this.submitShipping();
                });
        } catch(err) {
            _log('Shipping submission error');
            // set to config delay in future
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.submitShipping();
        }
    } 

    /*
    Scrapes the payment instrument id that comes with the site/card payment
    */
    scrapeInstrumentID = async() => {

        let link = this.site + new_link + '?previous_step=shipping_method&step=payment_method';

        try {
            await axios
                .get(link, { 
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'cookie': header_cookies_str,
                        'content-type': 'application/x-www-form-urlencoded',
                        'upgrade-insecure-requests': '1',
                    } 
                })
                .then(function (response) {
                    var body = response.data;
                    const $ = cheerio.load(body);
                    var htmlStr = $.html();
                    // scrapes payment instrument ID
                    let gateway = htmlStr.split('checkout_payment_gateway_')[1];
                    instrumentID = gateway.split('"')[0];
                })
                .catch(function (error) {
                    // handle error
                    return this.scrapeInstrumentID();
                });
        } catch(err) {
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.scrapeInstrumentID();
        }
    }

    /*
    Request to encrypt payment, could be done at any point in the script 
    */
    encryptPayment = async() => {

        var site = this.site;
        var scope = site.slice(8);
    
        const json = JSON.stringify({
            'credit_card': {
                'number': profile.payment.card,
                'name': profile.payment.name,
                'month': profile.payment.expMonth,
                'year': profile.payment.expYear,
                'verification_value': profile.payment.cvv
            },
            'payment_session_scope': scope
        });
    
        axios
            .post('https://deposit.us.shopifycs.com/sessions', json, { 
                headers: {
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/json',
                } 
            })
            .then(function (response) {
                // retrieve encrypted value from submitting card info
                encrypted = response.data['id'];
            })
            .catch(function (error) {
                // handle error
                return encryptPayment();
            });
    }

    /*
    Submits final payment with encrypted card value, scraped instrumentID and final total
    */
    submitPayment = async() => {

        const form_data = new URLSearchParams();
        form_data.append('_method', 'patch');
        form_data.append('authenticity_token', token2);
        form_data.append('previous_step', 'payment_method');
        form_data.append('step', '');
        form_data.append('s', encrypted);
        form_data.append('checkout[payment_gateway]', instrumentID);
        form_data.append('checkout[credit_card][vault]', 'false');
        form_data.append('checkout[different_billing_address]', 'false');
        form_data.append('checkout[remember_me]', 'false');
        form_data.append('checkout[remember_me]', '0');
        form_data.append('checkout[vault_phone]', '+1' + profile.contact.phone);
        form_data.append('checkout[total_price]', total);
        form_data.append('complete', '1');
        form_data.append('checkout[client_details][browser_height]', '625');
        form_data.append('checkout[client_details][browser_width]', '786');
        form_data.append('checkout[client_details][javascript_enabled]', '1');
        form_data.append('checkout[client_details][color_depth]', '24');
        form_data.append('checkout[client_details][java_enabled]', 'false');
        form_data.append('checkout[client_details][browser_tz]', '300');

        try {
            await axios
                .post(this.site + new_link, form_data, { 
                    headers: {
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'cookie': header_cookies_str,
                        'upgrade-insecure-requests': '1',
                    } 
                })
                .then(function (response) {
                    // log success of submitting payment
                    _log('Payment submitted');
                })
                .catch(function (error) {
                    // handle error
                    _log('Error submitting payment');
                    return this.submitPayment();
                });
        } catch (e) {
            _log('Error submitting payment');
            // set to config delay in future
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.submitPayment();
        }
    }

    start = async() => {
        try {

            await this.keywordScrape();

            // then bypass the captcha using the sitekey from checkpoint
            await this.checkpointScrape();
            var data = await this.bypassCaptcha(sitekey_chkpt);
            await this.checkpointSubmit(data);

            // add item to cart
            await this.addToCart();
            await this.postATC();

            // complete captcha on contact page if there is one
            if (cap_bool) {
                var data = await this.bypassCaptcha(sitekey_cntct);   
                await this.autofillContactInformation(data);
            }
            else {
                await this.autofillContactInformationNoCaptcha();
            }

            // complete rest of checkout
            await this.scrapeShippingMethod();
            await this.submitShipping();
            await this.scrapeInstrumentID();
            await this.encryptPayment();
            await this.submitPayment();

        } catch (error) {
            _log(`Bot error on ${this.site} with product ${choice}`);
            await new Promise(done => setTimeout(() => done(), payload.checkout_delay));
            return this.start();
        }
    }
}

// supply the site here
let bot = new Shopify(payload.entry_url);
bot.start();
