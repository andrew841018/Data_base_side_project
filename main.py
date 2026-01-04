# task:web scraping from a website and save the data to a csv file
# step 1: import the necessary libraries
import requests
from bs4 import BeautifulSoup
import csv

# step 2: define the url of the website to scrape
url = "https://www.google.com"

# step 3: send a request to the website
response = requests.get(url)

# step 4: parse the html content of the website
soup = BeautifulSoup(response.text, "html.parser")

# step 5: find the data we want to scrape
data = soup.find("div", class_="data")

# step 6: save the data to a csv file
with open("data.csv", "w") as file:
    writer = csv.writer(file)
    writer.writerow(["data"])
    writer.writerow([data])

# step 7: print the data to the console
print(data)

# step 8: close the file
file.close()

# step 9: define the main function
def main():
    #print("Hello, World!")