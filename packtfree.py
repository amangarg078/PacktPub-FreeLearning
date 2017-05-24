import celery
import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import lxml
from lxml import html as hl
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from celery import Celery
from celery.schedules import crontab
from celery.task import periodic_task
import os

REDIS_URL =  os.environ['REDIS_URL']
app = Celery('packtfree', broker=REDIS_URL)

def parse_html(html_source):
    """
    Parse HTML of the page to get book details to be sent in email
    """
    tree=hl.fromstring(html_source)
    image=tree.xpath("//img[contains(@class,'imagecache-dotd_main_image')]/@src")
    today_html=tree.xpath("//div[@id='deal-of-the-day']")

    countdownbar = today_html[0].xpath("//div[@class='eighteen-days-countdown-bar']")
    countdownbar[0].getparent().remove(countdownbar[0])
    return "<img src='{}'></br>".format(image[0])+ hl.tostring(today_html[0])


def send_email_notification(email_data):
    """
    Send email notification
    """
    FROM_EMAIL = "amangarg.packt@gmail.com"
    TO_EMAIL = "amangarg078@gmail.com"

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Packt Pub Daily Free E-book "+str(datetime.now())
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    # Create the body of the message (a plain-text and an HTML version).
    text = "Hi!"+ u' '.join(hl.fromstring(email_data).text_content()).encode('utf-8').strip()
    html = "<html><head></head><body><h1>Hi! Your free book is available to download!!</h1>"+email_data+"</body></html>"
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP('smtp.gmail.com:587')
    login = "amangarg.packt@gmail.com"
    password = "packtfree"

    server.starttls()
    server.login(login,password)
    server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
    server.quit()


@periodic_task(run_every=(crontab(hour="7", minute="0")))
def claim_free_ebook():
    """
    Claim the daily free book
    """

    URL = "https://www.packtpub.com/packt/offers/free-learning"
    USERNAME = "amangarg078@gmail.com"
    PASSWORD = "cooldude123"

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(URL)

    #Login to packtpub account
    driver.find_element_by_class_name('twelve-days-claim').click()
    driver.execute_script("window.scrollTo(0, 0);")
    driver.find_element_by_xpath("//div[@id='account-bar-form']/div/div/form/div/div/div/div/input[@id='email']").send_keys(USERNAME)
    driver.find_element_by_xpath("//div[@id='account-bar-form']/div/div/form/div/div/div[2]/div/input[@id='password']").send_keys(PASSWORD)
    driver.find_element_by_xpath("//div[@id='account-bar-form']/div/div/form/div/div/div[3]/input").click()

    driver.implicitly_wait(2)

    #get book image, name, details
    html_source = driver.page_source
    email_data = parse_html(html_source)
    driver.find_element_by_class_name('twelve-days-claim').click()
    driver.close()

    #send email notification
    send_email_notification(email_data)