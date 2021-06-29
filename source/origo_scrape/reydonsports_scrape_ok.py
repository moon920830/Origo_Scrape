import time, os, csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent
from selenium.webdriver.common.action_chains import ActionChains
from os.path import join, dirname
from dotenv import load_dotenv
import xlsxwriter
from threading import Thread
import logging
from logging.handlers import RotatingFileHandler
import platform

from bs4 import BeautifulSoup
import requests


cur_path = dirname(__file__)
root_path = cur_path[:cur_path.rfind(os.path.sep)]
# root_path = root_path[:root_path.rfind(os.path.sep)]
load_dotenv(join(root_path, '.env'))
log_file_size = 10
formatter = logging.Formatter('%(asctime)s    %(message)s')
scrape_status = ""


def my_logging(log, msg):
    global root_path

    log.propagate = True
    fileh = RotatingFileHandler(join(root_path, "log", "reydonsports.log"), mode='a', maxBytes=log_file_size*1024, backupCount=2, encoding='utf-8', delay=0)
    # ('logs/' + f_name + '.log', 'a')
    fileh.setFormatter(formatter)
    for hdlr in log.handlers[:]:  # remove all old handlers
        log.removeHandler(hdlr)
    log.addHandler(fileh)
    log.critical(msg)
    log.propagate = False


class RDS_Thread(Thread):
 
    def __init__(self, scrape_type):
        Thread.__init__(self)
        self.scrape_type = scrape_type
        self.log = logging.getLogger("a")  # root logger
        self.status = ""


    def login(self, mail, driver) :   
        self.status_publishing("loging in") 
        my_logging(self.log, "login ...")
        driver.get('https://www.reydonsports.com/web/login')
        mail_address = mail[0]
        mail_pass = mail[1]
        time.sleep(5)

    # Login Id
        while True:
            try:
                login_id_field = driver.find_element_by_id("login")
                login_id_field.send_keys(mail_address)
                self.status_publishing("Login Id is inserted")
                break
            except TimeoutException:
                self.status_publishing("Login Id field has not found")
                time.sleep(1)

    # Password
        while True:
            try:
                password_field = driver.find_element_by_id("password")
                password_field.send_keys(mail_pass)
                self.status_publishing("Password is inserted")
                break
            except TimeoutException:
                self.status_publishing("Password field has not found")
                time.sleep(1)
       
    # Sign In Button
        while True:
            try:
                sign_in = driver.find_element_by_xpath("//button[text()='Log in']")
                sign_in.click()
                self.status_publishing("Sign In Button is clicked")
                break
            except TimeoutException:
                self.status_publishing("Sign In Button has not found")
                time.sleep(1)


                # <a href="/shop/page/21?attrib_price=0-1.0">Next</a> - page navigation
                # <a href="">Next</a>
                # //a[@href="" and text()='Next']

                # //div[@class='oe_product oe_shop_left oe_product_cart']
        
         
    def run(self):
        now = datetime.now()
        mail_address = os.environ.get('RDS_LOGIN_ID')
        mail_password = os.environ.get('RDS_PASSWORD')
        mail = [mail_address, mail_password]

        # ua = UserAgent()
        # # userAgent = ua.random
        # # userAgent = userAgent.split(" ")
        # # userAgent[0] = "Mozilla/5.0"
        # # userAgent = " ".join(userAgent)
        # # print("userAgent = " + userAgent)
        # chrome_options = webdriver.ChromeOptions()
        # # chrome_options.add_argument('user-agent={0}'.format(userAgent))
        # # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("window-size=1280,800")
        # chrome_options.add_argument('--log-level=0')
        # path = join(dirname(__file__), 'webdriver', 'chromedriver.exe') # Windows
        # if platform.system() == "Linux":
        #     path = join(dirname(__file__), 'webdriver', 'chromedriver') # Linux

        # driver = webdriver.Chrome (executable_path = path, options = chrome_options )
        # # driver.maximize_window()
        # self.status_publishing("start chrome")
        # my_logging(self.log, "start chrome")
        # #Remove navigator.webdriver Flag using JavaScript
        # driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # # driver.set_window_size(1200,900)
        try:
            # my_logging(self.log, "try")
            # self.login(mail, driver)
            # time.sleep(5)
            # if self.scrape_type == "stock":
            #     self.loop_main_category(driver, 1)
            # else:
            #     self.loop_main_category(driver)
            # print("#" * 50)
            # print("time = " + str(datetime.now() - now))
            self.main_loop(mail_address, mail_password)
        except Exception as e:
            # driver.save_screenshot(datetime.now().strftime("screenshot_%Y%m%d_%H%M%S_%f.png"))
            self.status_publishing(e)
        finally:
            pass


    def main_loop(self, user_email, user_password, stock_scrape=0):
        BASE_URL = "https://www.reydonsports.com"        
        category_link_list = []
        products_link_list = []
        products_dict = {}

        fields = ['SKU', 'Name', 'Description', 'Trade Price', 'SRP Price', 'Price', 'Stock', 'URL', 'Image', 'Category', 'Commodity Code', 'Barcode', 'Shipping Dimensions', 'Shipping Weight', 'Country of Origin', 'Colour', 'Length']
        if stock_scrape == 1: fields = ['sku', 'stock']

        # generate .xlsx file name
        timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")
        xlsfile_name = 'products-' + timestamp + '.xlsx'
        if stock_scrape == 1: xlsfile_name = 'stock-' + timestamp + '.xlsx'
        xlsfile_name = join(root_path, "xls", "reydonsports", xlsfile_name)
        print(xlsfile_name)

        workbook = xlsxwriter.Workbook(xlsfile_name)
        worksheet = workbook.add_worksheet()

        with requests.Session() as s:
            # Get CSRF_TOKEN
            page = s.get("https://www.reydonsports.com")
            soup = BeautifulSoup(page.content, 'html.parser')
            script_snippet = str(soup.find("script"))
            script_snippet = script_snippet[script_snippet.find('csrf_token'):]
            script_snippet = script_snippet[script_snippet.find('"') + 1:]
            csrf_token = script_snippet[:script_snippet.find('"')]
            
            
            p = s.post("https://www.reydonsports.com/web/login", data={
                "login": user_email,
                "password": user_password,
                "csrf_token": csrf_token
            })

            # Get SESSION_ID
            cookie = p.headers["Set-Cookie"]
            cookie = cookie[cookie.find("session_id"):]
            cookie = cookie[cookie.find("=") + 1:]
            session_id = cookie[:cookie.find(";")]

            # Set HEADER
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'cookie': 'frontend_lang=en_GB; session_id=e065a7444d4a835d3a1969bd5ee64520ed8438d7; _ga=GA1.2.248003462.1624860338; _gid=GA1.2.482944600.1624860338'
            }

            # products_url_txt = open("reydonsports_products_url.txt","w")
            # base_page = s.get('https://www.reydonsports.com/shop')
            # soup = BeautifulSoup(base_page.content, 'html.parser')
            # for dropdown in soup.select(".dropdown ul")[3:7]:
            #     print(" ===============  dropdown = ")
            #     # print(dropdown)
            #     for category in dropdown.select("li a"):
            #         print(category['href'])
            #         category_link_list.append(category['href'])
            
            # # Get Products Links
            # for category_link in category_link_list:
            #     link = category_link
            #     if link[0] == "/": 
            #         link = BASE_URL + link
            #     page = s.get(link)
            #     soup = BeautifulSoup(page.content, 'html.parser')
            #     page_num = 1
            #     while True:
            #         self.status_publishing("Category Link : " + category_link + ", Page number : " + str(page_num))
            #         products = soup.find_all('div', attrs={'class':'oe_product oe_shop_left oe_product_cart'})
            #         for product in products:
            #             a = product.find('a', attrs={'itemprop': 'url'})
            #             print(a['href'])
            #             products_link_list.append(a['href'])
            #             products_url_txt.write(a['href'] + "\n")

            #         next_btn = soup.find("a", string="Next")
            #         if next_btn and next_btn['href'] != "":
            #             page_num += 1
            #             if link.find("?"):
            #                 link_1 = link[:link.find("?")]
            #                 # link_2 = link[link.find("?"):]
            #                 page = s.get(link_1 + "/page/" + str(page_num))
            #             else:
            #                 page = s.get(link + "/page/" + str(page_num))
            #             soup = BeautifulSoup(page.content, 'html.parser')
            #         else:
            #             break

            # products_url_txt.close()

            products_url_txt = open("reydonsports_products_url.txt","r")

            
            
            i = -1  
            for head in fields:
                i += 1            
                worksheet.write(0, i, head)
            i = 0
            for product_link in products_url_txt.readlines():
            # for product_link in products_link_list:
                i += 1
                link = product_link[:-1]
                self.status_publishing("Product " + str(i) + " : " + link)                
                if link[0] == "/": 
                    link = BASE_URL + link
                page = s.get(link, headers=headers)
                soup = BeautifulSoup(page.content, 'html.parser')
                print(soup.find('div', attrs={'class':'c_product_name'}))
                product_name = soup.find('div', attrs={'class':'c_product_name'}).get_text()
                print(product_name)

                product_desc = soup.find('div', attrs={'class':'o_not_editable prod_des'}).get_text()
                print("product desc :: ", product_desc)

                product_price_trade = soup.find('h6', attrs={'id':'rey_trade_price'}).get_text().split(":")
                if len(product_price_trade) > 1: 
                    product_price_trade = product_price_trade[1].strip()
                else:
                    product_price_trade = product_price_trade[0].strip()
                print("product trade price :: ", product_price_trade)

                product_price_srp = soup.find('h6', attrs={'id':'rey_srp_price'}).get_text().split(":")
                print("product SRP price :: ", product_price_srp)
                if len(product_price_srp) > 1: 
                    product_price_srp = product_price_srp[1].strip()
                else:
                    product_price_srp = product_price_srp[0].strip()

                product_price = soup.find('h4', attrs={'class':'oe_price_h4 css_editable_mode_hidden'}).b.get_text().replace(u'\xa0', u' ')

                product_stock = soup.find('div', attrs={'class':'availability_messages css_rey_is_not_available'}).div.get_text().strip()
                product_img = soup.find('img', attrs={'class':'img img-responsive product_detail_img js_variant_img'})['src']
                print("img = ", product_img)

                product_category = soup.find('p', attrs={'class':'category_label'}).a.get_text()
                product_sku = soup.find('p', attrs={'class':'sku_label'}).get_text().strip()
                if product_sku == "":
                    product_sku = soup.find('span', attrs={'id':'rey_sku_label'}).get_text().strip()
                print("sku = #", product_sku , "#")
                product_sku = product_sku.split(":")
                print(len(product_sku))
                if len(product_sku) > 1: 
                    product_sku = product_sku[1].strip()
                else:
                    product_sku = product_sku[0].strip()

                print("SKU = ", product_sku)
                
                try:
                    product_intrastat = soup.find('td', attrs={'id':'product_intrastat'}).get_text().strip()
                except:
                    product_intrastat = ""

                try:
                    product_barcode = soup.find('td', attrs={'id':'product_barcode'}).get_text().strip()
                except:
                    product_barcode = ""

                try:                
                    product_dimensions = soup.find('td', attrs={'id':'product_dimensions'}).get_text().strip()
                except:
                    product_dimensions = ""

                try:
                    product_weight = soup.find('td', attrs={'id':'product_weight'}).get_text().strip()
                except:
                    product_weight = ""

                try:
                    product_origin = soup.find('td', attrs={'id':'product_origin'}).get_text().strip()
                except:
                    product_origin = ""
                
                try:
                    product_color = soup.find("td", string="Colour").find_next_sibling("td").get_text().strip()
                except:
                    product_color = ""
                
                try:
                    product_length = soup.find("td", string="Length").find_next_sibling("td").get_text().strip()
                except:
                    product_length = ""

                # if product_name not in products_dict: 
                #     product = {}
                #     product["name"] = product_name
                #     product["url"] = product_link[:-1]
                #     product["desc"] = product_desc
                #     product["price_trade"] = product_price_trade
                #     product["price_srp"] = product_price_srp
                #     product["price"] = product_price
                #     product["stock"] = product_stock
                #     product["img"] = product_img
                #     product["intrastat"] = product_intrastat
                #     product["barcode"] = product_barcode
                #     product["dimensions"] = product_dimensions
                #     product["weight"] = product_weight
                #     product["origin"] = product_origin
                #     product["category"] = product_category
                #     product["sku"] = product_sku
                #     product["color"] = product_color
                #     product["length"] = product_length

                #     print("\n == product == ", product, "\n")

                worksheet.write(i, 0, product_sku)
                worksheet.write(i, 1, product_name)
                worksheet.write(i, 2, product_desc)
                worksheet.write(i, 3, product_price_trade)
                worksheet.write(i, 4, product_price_srp)
                worksheet.write(i, 5, product_price)
                worksheet.write(i, 6, product_stock)
                worksheet.write(i, 7, product_link[:-1])
                worksheet.write(i, 8, product_img)
                worksheet.write(i, 9, product_category)
                worksheet.write(i, 10, product_intrastat)
                worksheet.write(i, 11, product_barcode)
                worksheet.write(i, 12, product_dimensions)
                worksheet.write(i, 13, product_weight)
                worksheet.write(i, 14, product_origin)
                worksheet.write(i, 15, product_color)
                worksheet.write(i, 16, product_length)

            workbook.close()
                

    def fail_with_error(self, message):
        def decorator(fx):
            def inner(*args, **kwargs):
                try:
                    return fx(*args, **kwargs)
                except Exception as e:
                    self.status_publishing(message)
                    raise e
            return inner
        return decorator


    def loop_main_category(self, driver, stock_scrape=0):
        global root_path
        # products_url_txt = open("reydonsports_products_url.txt","w")

        print("== loop_main_category ==")
        products_dict = {}
        global_head_list = []
        product_count = 0
        fields = ['SKU', 'Name', 'Description', 'Trade Price', 'SRP Price', 'Price', 'Stock', 'URL', 'Image', 'Category', 'Commodity Code', 'Barcode', 'Shipping Dimensions', 'Shipping Weight', 'Country of Origin', 'Colour', 'Length']
        if stock_scrape == 1: fields = ['sku', 'stock']

        # generate .xlsx file name
        timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")
        xlsfile_name = 'products-' + timestamp + '.xlsx'
        if stock_scrape == 1: xlsfile_name = 'stock-' + timestamp + '.xlsx'
        xlsfile_name = join(root_path, "xls", "reydonsports", xlsfile_name)

        workbook = xlsxwriter.Workbook(xlsfile_name)
        worksheet = workbook.add_worksheet()

        # Get Category Links
        # self.status_publishing("finding category link list ...")
        # category_link_list = []
        # drop_down_list = driver.find_elements_by_xpath("//li[@class='dropdown ']")
        # i = 0
        # for drop_down in drop_down_list:
        #     print(i, drop_down, drop_down.find_element_by_xpath("./a/span").text)
        #     i += 1
        #     if i < 3: continue
        #     lis = drop_down.find_elements_by_xpath(".//li/a")
        #     for li in lis:
        #         category_link_list.append(li.get_attribute("href"))

        # print("category_link_list = ", category_link_list)


        # # Get Products Links
        # products_link_list = []
        # print(" == leng of category = ", len(category_link_list))
        # self.status_publishing("finding Product link list ...")
        # for category_link in category_link_list:
        #     self.status_publishing("Category Link : " + category_link)
        #     driver.get(category_link)
        #     time.sleep(5)

        #     while True:
        #         while True:
        #             try:
        #                 products = driver.find_elements_by_xpath("//div[@class='oe_product oe_shop_left oe_product_cart']//div[@class='product-image oe_product_image']/a")
        #                 break
        #             except TimeoutException:
        #                 self.status_publishing("products has not found")
        #                 print("products has not found")
        #                 time.sleep(1)

        #         for product in products:
        #             products_link_list.append(product.get_attribute("href"))
        #             products_url_txt.write(product.get_attribute("href") + "\n")
        #             print(product.get_attribute("href"))

        #         try:
        #             next_btn = driver.find_element_by_xpath("//a[contains(text(), 'Next')]")
        #             if next_btn.get_attribute("href") == "": break
        #             next_btn.click()
        #             time.sleep(2)
        #         except :
        #             break

        # products_url_txt.close()

        # products_url_txt = open("reydonsports_products_url.txt","r")

        # for product_link in products_link_list:
        # i = 0
        # for product_link in products_url_txt.readlines():
        #     i += 1
        #     page = requests.get(product_link)
        #     soup = BeautifulSoup(page.content, 'html.parser')
        #     print(soup.prettify())
            # if i == 5 : 
            #     print(" ====       break             ==")
            #     break
            # self.status_publishing("Product : " + product_link)
            # driver.get(product_link)
            # time.sleep(2)

            # while True:
            #     try:
            #         product_name = driver.find_element_by_xpath("//div[@class='c_product_name']").text
            #         break
            #     except TimeoutException:
            #         self.status_publishing("product has not found")
            #         time.sleep(1)

            # product_desc = driver.find_element_by_xpath("//div[@class='o_not_editable prod_des']").text
            # product_price_trade = driver.find_element_by_xpath("//h6[@id='rey_trade_price']").text.split(":")[1].strip()
            # product_price_srp = driver.find_element_by_xpath("//h6[@id='rey_srp_price']").text.split(":")[1].strip()
            # product_price = driver.find_element_by_xpath("//h4[@class='oe_price_h4 css_editable_mode_hidden']/b").text

            # product_stock = driver.find_element_by_xpath("//div[@class='availability_messages css_rey_is_not_available']/div").text
            # product_img = driver.find_element_by_xpath("//img[@class='img img-responsive product_detail_img js_variant_img']").get_attribute("src")
            # product_category = driver.find_element_by_xpath("//p[@class='category_label']/a").text
            # product_sku = driver.find_element_by_xpath("//p[@class='sku_label']").text.split(":")[1].strip()
            
            # try:
            #     product_intrastat = driver.find_element_by_id("product_intrastat").text
            # except:
            #     product_intrastat = ""

            # try:
            #     product_barcode = driver.find_element_by_id("product_barcode").text
            # except:
            #     product_barcode = ""

            # try:                
            #     product_dimensions = driver.find_element_by_id("product_dimensions").text
            # except:
            #     product_dimensions = ""

            # try:
            #     product_weight = driver.find_element_by_id("product_weight").text
            # except:
            #     product_weight = ""

            # try:
            #     product_origin = driver.find_element_by_id("product_origin").text
            # except:
            #     product_origin = ""
            
            
            # try:
            #     product_color = driver.find_element_by_xpath("//td[text()='Colour']/following-sibling::td").text.strip()
            # except:
            #     product_color = ""
            
            # try:
            #     product_length = driver.find_element_by_xpath("//td[text()='Length']/following-sibling::td").text.strip()
            # except:
            #     product_length = ""


            # if product_sku not in products_dict: 
            #     product = {}
            #     product["name"] = product_name
            #     product["url"] = product_link[:-1]
            #     product["desc"] = product_desc
            #     product["price_trade"] = product_price_trade
            #     product["price_srp"] = product_price_srp
            #     product["price"] = product_price
            #     product["stock"] = product_stock
            #     product["img"] = product_img
            #     product["intrastat"] = product_intrastat
            #     product["barcode"] = product_barcode
            #     product["dimensions"] = product_dimensions
            #     product["weight"] = product_weight
            #     product["origin"] = product_origin
            #     product["category"] = product_category
            #     product["sku"] = product_sku
            #     product["color"] = product_color
            #     product["length"] = product_length

            #     print("\n == product == ", product, "\n")

            #     products_dict[product_sku] = product
            

        # # First Column
        # while True:
        #     try:
        #         category_links = driver.find_elements_by_xpath("//*[@id='pagewrapper']/table[2]/tbody/tr/td/table/tbody/tr/td[2]/div/table/tbody/tr[2]/td[1]//ul/li/a")
        #         self.status_publishing("Category links had got.")
        #         break
        #     except TimeoutException:
        #         self.status_publishing("Category links have not found")
        #         time.sleep(1)

        # for link in category_links:
        #     if not link.get_attribute("href") in category_link_list:
        #         category_link_list.append(link.get_attribute("href"))

        # # Second Column
        # while True:
        #     try:
        #         category_links = driver.find_elements_by_xpath("//*[@id='pagewrapper']/table[2]/tbody/tr/td/table/tbody/tr/td[2]/div/table/tbody/tr[2]/td[2]//ul/li/a")
        #         self.status_publishing("Category links had got.")
        #         break
        #     except TimeoutException:
        #         self.status_publishing("Category links have not found")
        #         time.sleep(1)

        # for link in category_links:
        #     if not link.get_attribute("href") in category_link_list:
        #         category_link_list.append(link.get_attribute("href"))

        # print(category_link_list)

        # # Get Sub Category link list **** begin ****
        # sub_category_link_list = []
        # sub_category_links = driver.find_elements_by_xpath("//*[@id='pagewrapper']/table[2]/tbody/tr/td/table/tbody/tr/td[2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr/td/ul/li/a")
        # for link in sub_category_links:
        #     if not link.get_attribute("href") in sub_category_link_list:
        #         sub_category_link_list.append(link.get_attribute("href"))

        # for link in category_link_list:
        #     self.status_publishing(link)
        #     driver.get(link)
        #     time.sleep(1)

        #     sub_category_links = driver.find_elements_by_xpath("//*[@id='pagewrapper']/table[2]/tbody/tr/td/table/tbody/tr/td[2]/div/table/tbody/tr[2]/td[3]/table/tbody/tr/td/ul/li/a")
        #     for link in sub_category_links:
        #         if not link.get_attribute("href") in sub_category_link_list:
        #             sub_category_link_list.append(link.get_attribute("href"))
        # # Get Sub Category link list **** end ****

        # # 
        # for link in sub_category_link_list:
        #     self.status_publishing("link = " + link)
        #     driver.get(link)
        #     time.sleep(1)
            
        #     while True:
        #         try:
        #             head_list_elem = driver.find_elements_by_xpath("html/body/div/table[2]/tbody/tr/td/table/tbody/tr[not(contains(@class, 'stocktd'))]/td")                    
        #             break
        #         except:
        #             pass
            
        #     head_list = []
        #     for head in head_list_elem:
        #         head_text = head.text
        #         if head_text == "Pattern Id": 
        #             head_text = "Pattern"
        #         head_list.append(head_text)
        #         if not head_text in global_head_list and head_text != " " : global_head_list.append(head_text)

        #     product_list = driver.find_elements_by_xpath("html/body/div/table[2]/tbody/tr/td/table/tbody/tr[contains(@class, 'stocktd')]")
        #     for product in product_list:
        #         product_detail = {}
        #         for field, item in zip(head_list, product.find_elements_by_xpath("./td")):
        #             if field == " ":
        #                 continue
        #             elif field == "Stock":
        #                 while True:
        #                     product_stock = item.find_element_by_xpath(".//td").text
        #                     if product_stock != "Loading..." : break
        #                 if product_stock.find("(") > -1:
        #                     product_stock = product_stock[:product_stock.find("(")].strip()
        #                 product_detail[field] = product_stock
        #             else:
        #                 product_detail[field] = item.text
                
        #         # print(product_detail)
                
        #         if product_detail["Item"] in products_dict: 
        #             print("duplicate")
        #             products_dict[product_detail["Item"]]["Range"] += " ; " + product_detail["Range"]
        #         else:
        #             products_dict[product_detail["Item"]] = product_detail

        #         product_count += 1

        # products_url_txt.close()
        # print("\n closed \n")

        # self.status_publishing("Saving data into a Excel file")
        # i = -1  
        # for head in fields:
        #     i += 1            
        #     worksheet.write(0, i, head)

        # i = 0
        # for sku in products_dict:
        #     i += 1
        #     print("name = ", products_dict[sku]['name'])
        #     worksheet.write(i, 0, sku)
        #     worksheet.write(i, 1, products_dict[sku]['name'])
        #     worksheet.write(i, 2, products_dict[sku]['desc'])
        #     worksheet.write(i, 3, products_dict[sku]['price_trade'])
        #     worksheet.write(i, 4, products_dict[sku]['price_srp'])
        #     worksheet.write(i, 5, products_dict[sku]['price'])
        #     worksheet.write(i, 6, products_dict[sku]['stock'])
        #     worksheet.write(i, 7, products_dict[sku]['url'])
        #     worksheet.write(i, 8, products_dict[sku]['img'])
        #     worksheet.write(i, 9, products_dict[sku]['category'])
        #     worksheet.write(i, 10, products_dict[sku]['intrastat'])
        #     worksheet.write(i, 11, products_dict[sku]['barcode'])
        #     worksheet.write(i, 12, products_dict[sku]['dimensions'])
        #     worksheet.write(i, 13, products_dict[sku]['weight'])
        #     worksheet.write(i, 14, products_dict[sku]['origin'])
        #     worksheet.write(i, 15, products_dict[sku]['color'])
        #     worksheet.write(i, 16, products_dict[sku]['length'])

        # workbook.close()

        # print("#" * 50)
        # print("count = " + str(product_count))

        # self.status_publishing("scraping is ended")
        
        
    def status_publishing(self,text) :
        global scrape_status

        scrape_status = text
        self.status = text
        print(text)
