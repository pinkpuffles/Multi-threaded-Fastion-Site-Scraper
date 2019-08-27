import requests
from bs4 import BeautifulSoup
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

import csv
import os
import datetime
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from multiprocessing import Pool

import scrapy
from scrapy.selector import HtmlXPathSelector
from scrapy_splash import SplashRequest
from scrapy.selector import HtmlXPathSelector
from scrapy_splash import SplashRequest
from selenium import webdriver
from bs4 import BeautifulSoup as soup, BeautifulSoup
import urllib.request


import time

from selenium.common.exceptions import TimeoutException
class MultiThreadScraper:

    def __init__(self, base_url):

        self.base_url = base_url

        self.root_url = '{}://{}'.format(urlparse(self.base_url).scheme, urlparse(self.base_url).netloc)
        self.pool = ThreadPoolExecutor(max_workers=5)
        self.scraped_pages = []
        self.to_crawl = Queue()
        self.to_crawl.put(self.base_url)

    def createFolder(self, directory):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError:
            print('Error: Creating directory. ' + directory)

    def saveImage(self, foldername, product_name,start):
        product_name=product_name.replace("\n","")
        product_name=product_name.replace(" ","")
        product_name=product_name.replace("-", "")
        product_name = ''.join(i for i in product_name if not i.isdigit())
        product_images = []
        foldername = foldername + str(product_name)
        foldername = foldername.replace(" ", "")
        self.createFolder(foldername)
        c = 0

        for i in start.find_all('div', class_='slick-track'):

            for img in i.select('img'):

                product_images.append(img['src'])
                urllib.request.urlretrieve("https:"+img['src'], foldername + "/" + product_name + str(c) + ".jpg")
                c = c + 1

        return product_images

    def getColor(self,start):
        color= ""
        fcolor =[]
        color= start.find_all('span',{'class': 'product-swatch__background'})

        for c in color:
            fcolor.append(c["data-swatch"])
        return fcolor

    def getRecommendations(self,start,d):

        last_height = d.execute_script("return document.body.scrollHeight")
        while True:
            d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            new_height = d.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        recommendations = start.find_all('p', {'class': 'dy-recommendation-product__detail dy-recommendation-product__detail--name'})
        recommended = []
        for i in recommendations:
            recommended.append(i.text)


        for data in start.find_all('div', class_='product-look__link'):
            for a in data.find_all('a'):
                print(a.get('href'))  # for getting link
                print(a.text)  # for getting text between the link
                recommended.append("https://www.jny.com"+str(a.get('href')))



        return recommended
    def getPrice(self,start):
        fprice=[]
        discount = ""

        try:

            price1 = start.find('span', {'class': 'product-price--compare'}).find_next(text=True)

            discount = start.find('span',{'class': 'product-price--regular product-price--sale text-bold'}).find_next(text=True)
            fprice.append(price1)
            fprice.append(discount)
        except:
            price = start.find('span', {'class': 'product-price--regular'}).find_next(text=True)

            fprice.append(price)
            fprice.append(discount)
        return fprice

    def getDesc(self,start):
        desc = []
        d=start.find('div',{'class': 'accordion__text'})

        tdTags = d.find_all("li")
        for tag in tdTags:
               desc.append(tag.text)
        return desc
    def getURL(self,start):
       d = start.find('meta', {'property': 'og:url'})

       return d["content"]

    def parse_links(self, html):
        print("parsing links")
        soup = BeautifulSoup(html, 'html.parser')
        timestamp = datetime.datetime.now()
        url1 = soup.find('link', {'rel': 'canonical', 'href': True})
        url = url1['href']
        print(url)
        if "products" in url:
            print("inside")
            d = webdriver.Chrome('/Users/fatima.arshad/Downloads/chromedriver')
            d.get(url)
            start = BeautifulSoup(d.page_source, 'html.parser')
            product_url = d.current_url
            print (product_url)
            product_name = start.find('h1',{'class': 'product-title'}).find_next(text=True)
            print(product_name)
            desc = self.getDesc(start)
            while "\n" in desc: desc.remove("\n")
            print(desc)
            price = self.getPrice(start)
            print(price)
            Image_URL = self.saveImage("./products/", product_name, start)

            color =self.getColor(start)
            print(color)

            recommendations = self.getRecommendations(start, d)
            print(recommendations)

            self.saveCSV("output.csv", [product_url,timestamp,product_name,Image_URL,recommendations,price,color,desc])
            d.close()
        links = soup.find_all('a', href=True)
        for link in links:
            url = link['href']
            if url.startswith('/') or url.startswith(self.root_url):
                url = urljoin(self.root_url, url)
                if url not in self.scraped_pages:
                    self.to_crawl.put(url)

    def scrape_info(self, html):
        soup = BeautifulSoup(html, 'html.parser')

        return

    def post_scrape_callback(self, res):
        result = res.result()
        if result and result.status_code == 200:

            self.parse_links(result.text)
            self.scrape_info(result.text)

    def saveCSV(self, file_name, parameters):
        with open(file_name, mode='a', newline='') as employee_file:
                employee_writer = csv.writer(employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                print("csv file === ")
                print (parameters)
                employee_writer.writerow(parameters)
        employee_file.close()

    def scrape_page(self, url):

        try:
            print("in here")
            res = requests.get(url, timeout=(3, 30), verify = False)
            print(res)
            print("out here")
            return res
        except requests.RequestException:
            res = requests.get(url, timeout=(3, 30))
            return res

    def run_scraper(self):
        while True:
            try:
                target_url = self.to_crawl.get(timeout=60)

                if target_url not in self.scraped_pages:

                    print("Scraping URL: {}".format(target_url))
                    self.scraped_pages.append(target_url)
                    job = self.pool.submit(self.scrape_page,target_url)
                    job.add_done_callback(self.post_scrape_callback)
            except Empty:
                return
            except Exception as e:
                print(e)
                continue
if __name__ == '__main__':
    s = MultiThreadScraper("https://www.jny.com/")
    s.run_scraper()