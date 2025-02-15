from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import re
import psycopg2
import time
import logging
import sys
import getpass
import csv
from datetime import datetime

class Crawler:

    def __init__(self, login_id, login_pw):
        self.drvier = None
        self.connection = None
        self.cursor = None
        self.csv_file = None
        self.writer = None
        self.login_id = login_id
        self.login_pw = login_pw
        
    def open_csv_file(self):
        current_date = datetime.now().strftime("%Y%m%d_%H_%M")
        csv_file_path = f"dataset_{current_date}.csv"
        self.csv_file = open(csv_file_path, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        cols = [
            'product_id',
            'product_price',
            'product_color',
            'product_chip',
            'product_ram',
            'product_ssd',
            'product_keyboard'
        ]
        self.csv_writer.writerow(cols)
    
    def close_csv_file(self):
        self.csv_file.close()

    def start_driver(self):
        self.driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()))

    def quit_driver(self):
        self.driver.quit()

    def connect_db(self):
        db_config = {
        'dbname': 'your_database_name',
        'user': 'your_username',
        'password': 'your_password',
        'host': 'your_host',
        'port': 'your_port',
        }

        try:
            self.connection = psycopg2.connect(**db_config)
            logging.info("Connected to PostgreSQL.")
        except psycopg2.OperationalError:
            logging.info(f"Could not establish the database connection.")
        self.cursor = self.connection.cursor()

    def create_table(self):
        # univstore 테이블 생성
        create_univstore_table_query = '''
            CREATE TABLE IF NOT EXISTS univstore (
                id SERIAL PRIMARY KEY,
                product_id VARCHAR(255),
                price INTEGER,
                category VARCHAR(255),
                year INTEGER,
                cpu VARCHAR(255),
                ram VARCHAR(255),
                ssd VARCHAR(255),
                color VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                updated_at TIMESTAMP
            );
        '''
        self.cursor.excute(create_univstore_table_query)

        # coupang 테이블 생성
        create_coupang_table_query = '''
            CREATE TABLE IF NOT EXISTS coupang (
                id SERIAL PRIMARY KEY,
                product_id VARCHAR(255),
                price INTEGER,
                category VARCHAR(255),
                year INTEGER,
                cpu VARCHAR(255),
                ram VARCHAR(255),
                ssd VARCHAR(255),
                color VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                updated_at TIMESTAMP
            );
        '''
        self.cursor.excute(create_coupang_table_query)
        
        self.connection.commit()

    # 학생 복지 스토어에 로그인하는 함수
    def login_univstore(self):
        self.driver.get("https://www.univstore.com/user/login?redirect=%2F")
        self.driver.implicitly_wait(60)

        # 로그인
        try:
            id_element = self.driver.find_element(By.NAME, "userid")
            pw_element = self.driver.find_element(By.NAME, "password")
            submit_element = self.driver.find_element(By.NAME, "submit")
            ActionChains(self.driver).send_keys_to_element(id_element, self.login_id).send_keys_to_element(pw_element, self.login_pw).click(submit_element).perform()
        except:
            print("잘못된 id와 pw입니다.")
            exit()

    # 맥북 정보 리스트 페이지에서 정보를 갖고 오는 함수
    def get_macbook_info_in_univstore(self):
        self.open_csv_file()
        '''
        input : 맥북 페이지의 url
        output :
        1. 카테고리 (pro, air)
        2. 연도 (2020, 2021, 2022, ..)
        3. CPU (M1, M2, ..)
        4. RAM (8GB, 16GB, ..)
        5. SSD (256GB, 512GB, ..)
        6. 색상 (스페이스 그레이, 실버, 골드, ..)
        7. 가격
        '''
        macbook_url = "https://univstore.com/category/computer?ctg_sub_code=020100&ctg_third_code=020101"
        self.driver.get(macbook_url)
        self.driver.implicitly_wait(60)

        # 상품 더보기로 모든 상품 출력
        more_button_element = self.driver.find_element(By.CLASS_NAME, "usInputButtonRound")
        cnt = 1
        while cnt < 30:
            try:
                more_button_element.click()
                time.sleep(1)
                cnt += 1
            except:
                break
        self.driver.implicitly_wait(3)
        product_elements = self.driver.find_elements(By.CLASS_NAME, "usItemThumbnailLink")
        product_href_list = [product_element.get_attribute("href") for product_element in product_elements]
        for product_href in product_href_list:
            
            self.driver.get(product_href)
            self.driver.implicitly_wait(60)
            time.sleep(1)

            try:
                product_id = self.driver.find_element(By.CLASS_NAME, "usItemCardInfoCode").text
                product_price = int(self.driver.find_element(By.CLASS_NAME, "usItemCardInfoPrice2").text.replace(",", ""))
                product_info_element = self.driver.find_element(By.CLASS_NAME, "usInputSelectOptionPickerPlaceholder")
                product_infos = product_info_element.text.split(",")
                
                print(product_id, product_price, product_infos)
                self.csv_writer.writerow([product_id, product_price]+product_infos)
            except Exception as e:
                print(f"error 발생 : {e}")
        self.close_csv_file()

    def insert_data(self, table_name, dataset):
        '''
        input : 테이블 이름, (상품번호, 가격, 카테고리, 연도, CPU, RAM, SSD, 색상)
        데이터를 디비에 저장하는 함수.
        '''
        try :
            insert_query = f'''
                INSERT INTO {table_name} (product_id, price, category, year, cpu, ram, ssd, color) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            '''
            self.cursor.excute(insert_query, dataset)
            self.connection.commit()
            logging.info(f"Data successfully stored in the {table_name} table.")
        except psycopg2.Error as err:
            logging.error(f"error : {err}")
            self.connection.rollback()
            sys.exit(1)
