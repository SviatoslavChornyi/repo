import telebot
import pandas as pd
import os
import shutil
import schedule
import time
import threading
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import logging


#Налаштування логування
logging.basicConfig(filename='bot.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Налаштування шляхів
download_folder = "C://Users//Святослав//Downloads"
target_folder = "C://Users//Святослав//Desktop//try_bot"
csv_file_sasha = os.path.join(target_folder, 'Sasha.csv')
csv_file_cyber = os.path.join(target_folder, 'Cyber.csv')


# Дані для авторизації та селектори
accounts = {
    'Sasha': {
        'url': "https://gamerange.site/admin/",
        'username': 'Sasha',
        'password': '4P9hM65Lsz!',
        'csv_file': csv_file_sasha,
        'reports_id': "reports",
        'metrics_button_selector': '[data-test-id="metrics-button"]',
        'success_button_selector': '[data-test-id="success-button"]',
        'offer_id': "Оффер",
        'sub_id_id': "Sub ID 18",
        'filters_compact_selector': '[data-test-id="filters-compact"]',
        'ip_id': 'IP',
        'group_id': 'Група кампанії'
    },
    'Cyber': {
        'url': "https://cybertraff.cfd/admin/",
        'username': 'Cyber',
        'password': 'P8e86FzG6r!',
        'csv_file': csv_file_cyber,
        'reports_id': "reports",
        'metrics_button_selector': '[data-test-id="metrics-button"]',
        'success_button_selector': '[data-test-id="success-button"]',
        'offer_id': "grid.offer",
        'sub_id_id': "grid.sub_id_18",
        'filters_compact_selector': '[data-test-id="filters-compact"]',
        'ip_id': 'grid.ip',
        'group_id': 'grid.campaign_group'
    }
}


bot = telebot.TeleBot("7744814439:AAF4BSeHodT8YODC6IE1J1NrNrGDmo-cSkk")


def load_data(csv_file):
    try:
        return pd.read_csv(csv_file, on_bad_lines='skip', header=0, delimiter=';', encoding='utf-8')
    except FileNotFoundError:
        return pd.DataFrame(columns=['Оффер', 'IP', 'Sub ID 18', 'Група кампанії'])


def find_sub_ids_by_ip(ip_address, data):
    matched_rows = data[data['IP'] == ip_address]
    return matched_rows['Sub ID 18'].unique()


def find_ips_by_sub_id(sub_ids, data):
    matched_rows = data[data['Sub ID 18'].isin(sub_ids)]
    return matched_rows[['Оффер', 'IP', 'Sub ID 18', 'Група кампанії']].drop_duplicates()


def split_message(message, chunk_size=4000):
    """Split a message into chunks."""
    return [message[i:i + chunk_size] for i in range(0, len(message), chunk_size)]


@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Скинь IP-адресу, будь ласка.')


@bot.message_handler(func=lambda message: True)
def message_handler(message):
    ip_address = message.text.strip()

    for account_name, details in accounts.items():
        # Обробка для набору даних
        sub_ids = find_sub_ids_by_ip(ip_address, load_data(details['csv_file']))
        if sub_ids.size > 0:
            related_ips = find_ips_by_sub_id(sub_ids, load_data(details['csv_file']))
            response = f"Результати для {account_name} CSV:\n"
            response += "---------------------------------------------\n"
            response += "| Оффер | IP | Sub ID | Група |\n"
            response += "---------------------------------------------\n"
            for index, row in related_ips.iterrows():
                response += f"| {row['Оффер']} | {row['IP']} | {row['Sub ID 18']} | {row['Група кампанії']} |\n"
                response += "---------------------------------------------\n"
        else:
            response = f"Немає результатів для IP {ip_address} у {account_name} CSV."

        # Split and send response in chunks
        for chunk in split_message(response):
            bot.send_message(message.chat.id, chunk)


def download_csv(account_data):
    try:
        options = webdriver.ChromeOptions()
        prefs = {'download.default_directory': download_folder}
        options.add_experimental_option('prefs', prefs)
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.get(account_data['url'])


        # Авторизація
        time.sleep(7)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'login'))).send_keys(account_data['username'])
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'password'))).send_keys(account_data['password'])
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="login-button"]'))).click()

        # Навігація та фільтрація
        time.sleep(5)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, account_data['reports_id']))).click()
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#!/clicks/log']"))).click()
        time.sleep(7)

        #Скинути фільтр
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, account_data['filters_compact_selector']))).click()
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Скинути фільтри']"))).click()
        time.sleep(2)
        #Фільтр
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, account_data['metrics_button_selector']))).click()
        time.sleep(3)
         
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.form-check-input'))).click()
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.form-check-input'))).click()
        time.sleep(2)

        #Вибрати поля
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, account_data['offer_id']))).click()
        time.sleep(2)
        
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, account_data['ip_id']))).click()
        time.sleep(2)
        search_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control-clearable__EAybb.form-control[placeholder='Знайти']")))
        search_input.clear() # Очищаємо поле, якщо в ньому щось є
        search_input.send_keys("група")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, account_data['group_id']))).click()
        time.sleep(2)
        search_input.clear()
        search_input.send_keys("Sub ID 18")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, account_data['sub_id_id']))).click()
        time.sleep(2)

        #Застосувати
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="success-button"]'))).click()
        
        # Експорт даних
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="grid-footer-export-button"]'))).click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//li[@ng-repeat='format in $ctrl.FORMATS']//a[contains(text(), 'CSV')]"))).click()
        time.sleep(60)

        # Переміщення завантаженого файлу
        for filename in os.listdir(download_folder):
            if filename.endswith(".csv"):
                filepath = os.path.join(download_folder, filename)
                filesize = os.path.getsize(filepath)
                if filesize > 0:
                    new_csv_path = os.path.join(target_folder, filename)
                    shutil.move(filepath, new_csv_path)
                    print(f"Файл {filename} успішно переміщено. Розмір: {filesize} байт.")
                    append_csv_data(account_data['csv_file'], new_csv_path)
                    os.remove(new_csv_path)
                else:
                    print(f"Порожній файл {filename} виявлено та пропущено.")
                    os.remove(filepath)
        driver.quit()
        load_data(filename)
    except Exception as e:
        logging.exception(f"Помилка під час завантаження CSV для {account_data['username']}: {e}")


def append_csv_data(main_file, new_file):
    try:
        main_df = pd.read_csv(main_file, sep=';', encoding='utf-8')
        new_df = pd.read_csv(new_file, sep=';', encoding='utf-8')
        new_df = new_df.drop_duplicates(subset=['Оффер', 'IP', 'Sub ID 18'])
        combined_df = pd.concat([main_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['Оффер', 'IP', 'Sub ID 18'])
        combined_df.to_csv(main_file, sep=';', encoding='utf-8', index=False)
    except pd.errors.EmptyDataError:
        logging.error("New CSV file is empty.")
    except Exception as e:
        logging.exception(f"Error appending CSV data: {e}")


def schedule_task():
    schedule.every(1).seconds.do(lambda: download_csv(accounts['Sasha']))
    schedule.every(1).seconds.do(lambda: download_csv(accounts['Cyber']))
    while True:
        schedule.run_pending()
        time.sleep(60)


load_data(csv_file_sasha)
load_data(csv_file_cyber)


scheduler_thread = threading.Thread(target=schedule_task)
scheduler_thread.start()


bot.polling(non_stop=True)


