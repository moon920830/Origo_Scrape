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



cur_path = dirname(__file__)
dotenv_path = join(cur_path[:cur_path.rfind("\\")], '.env')
load_dotenv(dotenv_path)

class Origo_Thread(Thread):
 
    def __init__(self, scrape_type):
        Thread.__init__(self)
        self.scrape_type = scrape_type


    def login(self, mail, driver) :    
        driver.get('https://origo-online.origo.ie')
        mail_address = mail[0]
        mail_pass = mail[1]

        try:
            email_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@name='UserName' and @type='email']")))
            email_field.send_keys(mail_address)
            print("Email address inserted")
        except TimeoutException:
            print("Email field is not ready")

        try:
            password_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@type='password' and @name='Password']")))
            password_field.send_keys(mail_pass)
            print("Password inserted")
        except TimeoutException:
            print("Password is not ready")

        try:
            login_button = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//button[@type='submit']")))
            login_button.click()
            print("Login button clicked")
        except TimeoutException:
            print("login button is not ready")
 
    def run(self):
        now = datetime.now()
        mail_address = os.environ.get('MAIL_ADDRESS')
        mail_password = os.environ.get('MAIL_PASSWORD')
        mail = [mail_address, mail_password]

        ua = UserAgent()
        userAgent = ua.random
        userAgent = userAgent.split(" ")
        # userAgent[0] = "Mozilla/5.0"
        userAgent = " ".join(userAgent)
        print("userAgent = " + userAgent)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('user-agent={0}'.format(userAgent))
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("window-size=1280,800")
        chrome_options.add_argument('--log-level=0')
        path = join(dirname(__file__), 'webdriver', 'chromedriver.exe')
        driver = webdriver.Chrome (executable_path = path, options = chrome_options )
        # driver.maximize_window()

        #Remove navigator.webdriver Flag using JavaScript
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # driver.set_window_size(1200,900)
        try:
            self.login(mail, driver)
            time.sleep(5)
            if self.scrape_type == "stock":
                self.loop_main_category(driver, 1)
            else:
                self.loop_main_category(driver)
            print("#" * 50)
            print("time = " + str(datetime.now() - now))
        except Exception as e:
            # driver.save_screenshot(datetime.now().strftime("screenshot_%Y%m%d_%H%M%S_%f.png"))
            print(e)
        finally:
            pass


    def fail_with_error(self, message):
        def decorator(fx):
            def inner(*args, **kwargs):
                try:
                    return fx(*args, **kwargs)
                except Exception as e:
                    print(message)
                    raise e
            return inner
        return decorator


    def loop_main_category(self, driver, stock_scrape=0):
        category_href_dict = {}
        products_dict = {}
        product_count = 0
        fields = ['id', 'category', 'title', 'stock', 'list price', 'nett price', 'description', 'URL', 'image']
        if stock_scrape == 1: fields = ['id', 'stock']

        while True:
            try:
                shopping_cart_btn = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@class='basket' and @data-src='/basket/summary']")))
                break
            except TimeoutException:
                print("main window is not ready")

        main_categories = WebDriverWait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//ul[@class='nav-list nav-list-root']/li[@class='nav-item nav-item-root']")))
        for main_category in main_categories:        
            main_category_title_elem = main_category.find_element_by_xpath("./a/span")
            
            sub_category_href_arr = []
            sub_categories = main_category.find_elements_by_xpath("./div//a[@href!='#']")
            if main_category == main_categories[-1]: sub_categories = main_category.find_elements_by_xpath("./a[@href!='#']")
            for sub_category in sub_categories:
                sub_category_href = sub_category.get_attribute('href')            
                sub_category_href_arr.append(sub_category_href)
            category_href_dict[main_category_title_elem.text] = sub_category_href_arr

        timestamp = datetime.now().strftime("%Y-%m%d-%H%M%S")

    
    # generate .xlsx file name
    
        xlsfile_name = 'xls\\products-' + timestamp + '.xlsx'
        if stock_scrape == 1: xlsfile_name = 'stock-' + timestamp + '.xlsx'

        workbook = xlsxwriter.Workbook(xlsfile_name)
        worksheet = workbook.add_worksheet()
        
        while len(category_href_dict) > 0:
            category_href_dict_2 = category_href_dict.copy()
            category_href_dict = {}
            for main_category in category_href_dict_2:
                for category_href in category_href_dict_2[main_category]:
                    print(category_href)
                    
                # find if there are products.
                
                    no_product_found = True

                    try:
                        driver.get(category_href)
                        try:
                            elem = driver.find_element_by_xpath("//div[@id='productListPage']/div[@class='msg-block']")
                            print("find msg-block")
                        except:
                            try:
                                elem = driver.find_element_by_xpath("//div[@id='product-list-panel']")
                                print("find list panel")
                                no_product_found = False
                            except:
                                try:
                                    elems = driver.find_elements_by_xpath("//div[@id='flexiPage']/div[@class='flexi-row']//div[@class='column']/div/a")
                                    print("find flexi-row")
                                    sub_category_href_arr = []
                                    for sub_category in elems:
                                        sub_category_href = sub_category.get_attribute('href')            
                                        print(sub_category_href)
                                        sub_category_href_arr.append(sub_category_href)
                                    category_href_dict[main_category] = sub_category_href_arr
                                except:
                                    print("find nothing")
                    except:
                        while True:
                            try:
                                
                            # find "No products found"
                                
                                elem = driver.find_element_by_xpath("//div[@id='productListPage']/div[@class='msg-block']")
                                print("find msg-block")
                                break
                            except:
                                pass

                            try:
                                elem = driver.find_element_by_xpath("//div[@id='product-list-panel']")
                                print("find list panel")
                                no_product_found = False
                                break
                            except:
                                pass

                            try:
                                
                            # find "No products found"
                                
                                elems = driver.find_elements_by_xpath("//div[@id='flexiPage']/div[@class='flexi-row']//div[@class='column']/div/a[not(contains(@href, '/cuisinart-'))]")
                                print("find flexi-row")
                                sub_category_href_arr = []
                                for sub_category in elems:
                                    sub_category_href = sub_category.get_attribute('href')            
                                    print(sub_category_href)
                                    sub_category_href_arr.append(sub_category_href)
                                category_href_dict[main_category] = sub_category_href_arr
                                break
                            except:
                                print("find nothing")
                                continue

                    if no_product_found :continue
                    print("Escape while loop")

                # Search all products
                   
                    products = driver.find_elements_by_xpath("//ul[@id='list-of-products']/li//a[@class='hyp-thumbnail']")
                    products_count = len(products)
                    print(products_count)
                    if products_count >= 60:
                        products_pre_count = 0
                        while products_pre_count != products_count:
                            products_pre_count = products_count
                            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                            time.sleep(5)
                            products = driver.find_elements_by_xpath("//ul[@id='list-of-products']/li//a[@class='hyp-thumbnail']")
                            products_count = len(products)
                            print("pre_count = " + str(products_pre_count) + "  count = " + str(products_count))

                    if stock_scrape == 1: 
                    
                    # Stock Scrape
                    
                        products = driver.find_elements_by_xpath("//ul[@id='list-of-products']/li")
                        for product in products:
                            product_id = product.find_element_by_xpath(".//div[@class='product-id-stock']/span[@class='product-id']/span[@class='product-id-value']").text
                            product_indication = product.find_element_by_xpath(".//div[@class='product-id-stock']/span[@class='stock-indication']/span")
                            product_stock = "0"
                            try:
                                product_stock = product_indication.find_element_by_xpath(".//span[@class='stock-amount']").text
                            except:
                                pass
                            product_count += 1
                    
                    else:
                    
                    # Full Scrape
                    
                        href_list = []
                        for product in products:
                            href_list.append(product.get_attribute("href"))

                        for href in href_list:
                            print(href)
                            try:
                                driver.get(href)
                                try:
                                    product_title = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h1[@class='font-product-title']"))).text
                                    print("found product title")
                                except:
                                    print("Not found product title")
                                    pass
                            except:
                                while True:
                                    try:
                                        product_title = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h1[@class='font-product-title']"))).text
                                        print("found product title")
                                        break
                                    except:
                                        print("Not found product title")
                                        pass
                            product_id = driver.find_element_by_xpath("//span[@itemprop='productID']").text
                            product_stock = "0"

                            try:
                                product_in_stock = driver.find_element_by_xpath("//span[@class='stock-row']//span[@class='stock-amount']")
                                product_stock = product_in_stock.text
                            except:
                                pass

                            product_price_1 = driver.find_element_by_xpath("((//span[@class='prices']/div)[1]/span)[1]").text.replace(".", "").replace(",", ".")
                            product_list_1 = driver.find_element_by_xpath("((//span[@class='prices']/div)[1]/span)[2]").text
                            product_price_2 = driver.find_element_by_xpath("((//span[@class='prices']/div)[2]/span)[1]").text.replace(".", "").replace(",", ".")
                            product_list_2 = driver.find_element_by_xpath("((//span[@class='prices']/div)[2]/span)[2]").text

                            product_description = ""
                            try:
                                product_description = driver.find_element_by_xpath("//div[@id='description']/div[@class='description']").text
                            except:
                                pass

                            img_src = driver.find_element_by_xpath("//div[@class='carousel-image-m-wrapper']//img").get_attribute('src')

                            product_category_path_elems = driver.find_elements_by_xpath("//li[contains(@class, 'arrow-red')]/a")
                            product_category_paths = []
                            for product_category_path_elem in product_category_path_elems:
                                product_category_paths.append(product_category_path_elem.text)

                            product_category = " > ".join(product_category_paths)

                            product_count += 1
                            
                            product_price_list = 0
                            product_price_nett = 0
                            if product_list_2 == "nett":
                                product_price_list = product_price_1
                                product_price_nett = product_price_2
                            else:
                                product_price_list = product_price_2
                                product_price_nett = ""
                            
                            try:
                                if product_id in products_dict: 
                                    print("duplicate")
                                    products_dict[product_id][1] += " ; " + product_category
                                else:
                                    products_dict[product_id] = [str(product_id), product_category, product_title, product_stock, product_price_list, product_price_nett, product_description, href, img_src]
                            except:
                                pass
        
        i = -1                                              
        for val in fields:
            i += 1
            worksheet.write(0, i, val)

        i = 0
        for row in products_dict:
            i += 1
            j = -1
            for val in products_dict[row]:
                j += 1
                worksheet.write(i, j, val)
        workbook.close()
        
        print("#" * 50)
        print("count = " + str(product_count))





# def origo_thread():
#     try:
#         login(mail, driver)
#         time.sleep(5)
#         loop_main_category(driver)
#         print("#" * 50)
#         print("time = " + str(datetime.now() - now))
#     except Exception as e:
#         # driver.save_screenshot(datetime.now().strftime("screenshot_%Y%m%d_%H%M%S_%f.png"))
#         print(e)
#     finally:
#         pass