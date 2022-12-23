import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import local_config


def switch_to_virtual_position():
    try:  # executed depend on window size
        sidebar_button = driver.find_element(By.XPATH,
                                             "/html/body/app-root/et-layout-main/div/div[2]/div["
                                             "1]/et-layout-sidenav/aside/div[3]/div[2]/a")
        sidebar_button.click()
        time.sleep(2)
    except selenium.common.exceptions.ElementNotInteractableException:
        pass

    switch_to_virtual_button = driver.find_element(By.XPATH,
                                                   '//*[@id="cdk-overlay-0"]/et-dialog-container/et-portfolio-toggle'
                                                   '-account/div/div[3]/a')
    switch_to_virtual_button.click()
    time.sleep(2)

    # try:
    #     virtual_confirm_button = driver.find_element(By.LINK_TEXT, 'Switch to Virtual Portfolio')
    #     virtual_confirm_button.click()
    #     time.sleep(5)
    # except selenium.common.exceptions.ElementNotInteractableException:
    #     pass

    my_watchlist_button = driver.find_element(By.XPATH,
                                              "/html/body/app-root/et-layout-main/div/div[2]/div["
                                              "1]/et-layout-sidenav/aside/div[2]/nav/ul/li[2]/a/span[2]")
    my_watchlist_button.click()
    time.sleep(2)


def buy(a):  # a=order no. in list
    buy_button = driver.find_element(By.XPATH,
                                     '//*[@id="watchlist-instruments"]/div[2]/div[%s]/div/div[2]/div['
                                     '4]/div/et-buy-sell-button/div/div[1]' % a)
    buy_button.click()
    time.sleep(2)

    # add your price action here
    # ...

    close_button = driver.find_element(By.XPATH, '//*[@id="open-position-view"]/div[1]/div[2]')
    close_button.click()
    time.sleep(2)


class MyApp:

    def __init__(self, username, password, path):
        self.username = username
        self.password = password
        self.path = path

    def login(self):
        username = driver.find_element(By.XPATH, '//*[@id="username"]')
        username.click()
        username.send_keys("%s" % self.username)
        password = driver.find_element(By.XPATH, '//*[@id="password"]')
        password.click()
        password.send_keys("%s" % self.password)
        login_button = driver.find_element(By.XPATH,
                                           "/html/body/app-root/et-layout-main/div/div/div/div/div/ui-layout/ng-view"
                                           "/et-login/et-login-sts/div/div/div/form/button")
        login_button.click()
        time.sleep(5)


if __name__ == '__main__':
    myApp = MyApp(local_config.USERNAME, local_config.PASSWORD, local_config.PATH)
    URL = "https://www.etoro.com/zh-tw/login"

    customized_chrome_options = Options()
    customized_chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(myApp.path, options=customized_chrome_options)
    driver.get(URL)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/93.0.4577.82 Safari/537.36"})

    myApp.login()
    switch_to_virtual_position()
    buy(1)
    buy(2)
    buy(3)
    buy(4)
