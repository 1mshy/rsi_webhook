from selenium import webdriver
from time import sleep
import os

# Creates an image of the heatmap, returns the relative path of the file
def request_heatmap_nasdaq() -> str:
    relative_path = "downloaded_images/tradingview_heatmap.png"
    url = "https://www.tradingview.com/heatmap/stock/#%7B%22dataSource%22%3A%22NASDAQ100%22%2C%22blockColor%22%3A%22change%22%2C%22blockSize%22%3A%22market_cap_basic%22%2C%22grouping%22%3A%22sector%22%7D"
    return request_website(url, relative_path)

    """Requests website and takes picture and saved in the given path
    Returns the given path
    """
def request_website(url: str, path: str) -> str:
    
    if not os.path.exists("downloaded_images"):
        os.makedirs("downloaded_images/")
    
    # 1. create a web driver instance
    driver = webdriver.Chrome()

    # 2. navigate to the website
    driver.get(url)
    
    sleep(1)

    # 3. save a screenshot of the current page
    driver.save_screenshot(path)

    # 4. close the web driver
    driver.quit()
    
    return path