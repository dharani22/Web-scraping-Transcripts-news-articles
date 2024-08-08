from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import requests
import threading

# Path to your chromedriver executable
PATH = "C:\\Windows\\chromedriver.exe"
service = Service(PATH)

# Initialize Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Configure Chrome to automatically download files to a specified directory
download_directory = "C:\\cases"  # replace with user directory
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_directory,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# Initialize WebDriver with Chrome options
driver = webdriver.Chrome(service=service, options=chrome_options)

# Flag to control the running status
stop_flag = threading.Event()

def wait_for_element(locator_type, locator_value, timeout=30):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((locator_type, locator_value)))

def click_element_js(element):
    driver.execute_script("arguments[0].click();", element)

def safe_action(action, error_message):
    try:
        return action()
    except Exception as e:
        print(f"{error_message}: {e}")
        driver.save_screenshot(f"{error_message.lower().replace(' ', '_')}.png")
        return None

def download_pdf(pdf_url, file_path):
    try:
        # Download the PDF file directly from the browser
        driver.get(pdf_url)
        time.sleep(2)  # Adjust if necessary
    except Exception as e:
        print(f"Error downloading PDF: {e}")

def process_cases():
    while not stop_flag.is_set():
        # Find all PDF download buttons on the page
        pdf_buttons = safe_action(lambda: driver.find_elements(By.XPATH, "//a[@class='icon la-Download']"),
                                  "Error finding PDF download buttons")
        if pdf_buttons:
            for idx, pdf_button in enumerate(pdf_buttons):
                if stop_flag.is_set():
                    return

                for _ in range(3):  # Retry up to 3 times
                    try:
                        click_element_js(pdf_button)
                        time.sleep(2)  # Wait for PDF to be available

                        # Assuming a download link can be obtained; you may need to adjust based on actual behavior
                        pdf_url = pdf_button.get_attribute('href')
                        if pdf_url:
                            file_path = os.path.join(download_directory, f"case_{idx + 1}.pdf")
                            download_pdf(pdf_url, file_path)
                        break
                    except Exception as e:
                        print(f"Error processing PDF button: {e}")
                        pdf_button = safe_action(lambda: driver.find_element(By.XPATH, "//a[@class='icon la-Download']"),
                                                "Error finding PDF download button")
                        if not pdf_button:
                            break
        else:
            print("No PDF download buttons found on the page.")

        # Check if there's a next page button
        next_page_button = safe_action(lambda: driver.find_element(By.XPATH, "//button/span[text()='Next']"),
                                       "Error finding Next button")
        if next_page_button:
            for _ in range(3):  # Retry up to 3 times
                try:
                    click_element_js(next_page_button)
                    time.sleep(5)  # Wait for the next page to load
                    break
                except Exception as e:
                    print(f"Error clicking Next button: {e}")
                    next_page_button = safe_action(lambda: driver.find_element(By.XPATH, "//button/span[text()='Next']"),
                                                  "Error finding Next button")
                    if not next_page_button:
                        break
        else:
            print("No more pages.")
            break

def graceful_exit():
    print("Graceful exit initiated.")
    stop_flag.set()
    driver.quit()

try:
    # Open the LexisNexis sign-in page
    driver.get(
        "https://signin.lexisnexis.com/lnaccess/app/signin?back=https%3A%2F%2Fplus.lexis.com%3A443%2Fuk%2F&aci=uk")

    # Login process
    safe_action(lambda: wait_for_element(By.XPATH, "//*[@id='normalloginsection']/ul/li[5]/a").click(),
                "Error clicking Academic Login button")
    safe_action(lambda: wait_for_element(By.ID, "filter-box").send_keys("University of Greenwich"),
                "Error entering university name")
    safe_action(lambda: wait_for_element(By.XPATH,
                                         "//*[@id='institution-list']/ul[1]/li/app-institution-item/span[1][contains(text(), 'University of Greenwich')]").click(),
                "Error selecting university")
    safe_action(lambda: wait_for_element(By.XPATH, "//*[@id='on-campus-button']/button/span[2]").click(),
                "Error clicking Continue button")

    # Switch to new window
    safe_action(lambda: WebDriverWait(driver, 60).until(EC.number_of_windows_to_be(2)), "Error waiting for new window")
    original_window = driver.current_window_handle
    new_window = [window for window in driver.window_handles if window != original_window][0]
    driver.switch_to.window(new_window)

    # Enter credentials
    safe_action(lambda: wait_for_element(By.ID, "userNameInput").send_keys("Username"),
                "Error entering username")  # replace with username
    safe_action(lambda: wait_for_element(By.ID, "nextButton").click(), "Error clicking Next button")
    safe_action(lambda: wait_for_element(By.ID, "passwordInput").send_keys("Password"), "Error entering password")  # replace with password
    safe_action(lambda: wait_for_element(By.ID, "submitButton").click(), "Error clicking Submit button")

    # Wait for successful login
    safe_action(lambda: WebDriverWait(driver, 60).until(lambda d: "plus.lexis.com/uk/xhome" in d.current_url),
                "Error waiting for successful login")

    # Search process
    search_box = safe_action(lambda: wait_for_element(By.ID, "searchTerms"), "Error finding search box")
    if search_box:
        search_box.clear()
        search_box.send_keys("BP company")
        time.sleep(2)

    search_button = safe_action(lambda: wait_for_element(By.XPATH, "//button[@aria-label='Search']"),
                                "Error finding search button")
    if search_button:
        click_element_js(search_button)

    # Wait for search results
    search_results_div = safe_action(lambda: WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'search-results')]"))),
                                     "Error waiting for search results")

    # Click on "Cases" button
    cases_button = safe_action(lambda: WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
                                                                                                   "//button[contains(@class, 'contentTypeRow') and .//div[contains(@class, 'contentTypeDisplay') and text()='Cases']]"))),
                               "Error finding Cases button")
    if cases_button:
        click_element_js(cases_button)

    # Wait for Case Overview filter to be visible and click it
    case_overview_button = safe_action(lambda: WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
        (By.XPATH, "//span[contains(@class, 'filterval-text') and text()='Case Overview']"))),
                                       "Error finding Case Overview button")
    if case_overview_button:
        click_element_js(case_overview_button)

    # Process cases and download PDFs
    process_cases()

except KeyboardInterrupt:
    # Handle a keyboard interrupt (Ctrl+C)
    graceful_exit()

except Exception as e:
    print(f"An unexpected error occurred: {e}")
    driver.save_screenshot("unexpected_error.png")
    graceful_exit()

finally:
    # Ensure the browser is closed
    if driver:
        driver.quit()