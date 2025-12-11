from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Configure Chrome options (headless mode optional)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Remove for visual debugging
driver = webdriver.Chrome(options=chrome_options)

try:
    # Replace with the actual Coursera assessment URL
    driver.get("https://www.coursera.org/learn/agentic-ai-chatgpt-zapier/home/module/4")
    time.sleep(5)  # Wait for page to load

    # Extract text from all visible elements (divs, p, li, etc.)
    elements = driver.find_elements(By.XPATH, "//div | //p | //li | //span | //h2 | //h3")
    raw_text = "\n".join([element.text for element in elements])

    # Print or save the extracted text
    print(raw_text)

    # Optional: Save to a file
    with open("coursera_text.txt", "w", encoding="utf-8") as f:
        f.write(raw_text)

finally:
    driver.quit()
