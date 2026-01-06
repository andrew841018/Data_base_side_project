# task:web scraping from a website and save the data to a csv file
# step 1: import the necessary libraries
import requests
from bs4 import BeautifulSoup
import csv,os,time
def get_previous_page(soup):
    for item in soup:
        prev_soup=item.find("a",string=lambda t:t and "上頁" in t)
        if not prev_soup:
            continue
        else:
            prev_page=prev_soup.get("href")
            return prev_page
    return False
url = "https://www.ptt.cc/bbs/stock/index.html" #初始url
file_exists = os.path.exists("ptt_stock_title.csv")
with open("ptt_stock_title.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Title","推噓數","Author","Url","Date"]) 
web_content_list=[]
for i in range(10000):
    try:
        headers = {"cookie": "over18=1"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        data = soup.find_all("div", class_="r-ent")
        if data:
            for item in data:
                comment=item.find("div",class_="nrec")
                title=item.find("div",class_="title")
                author=item.find("div",class_="author")
                date=item.find("div",class_="date")
                a_tag=title.find("a")
                if not a_tag:
                    continue
                article_url="https://www.ptt.cc"+a_tag.get("href")
                if comment and comment.text.strip():
                    comment_txt=comment.text.strip()
                else:#no div or no comment
                    comment_txt="0"
                if "公告" in title.text:
                    continue
                json_dict={
                    "title":title.text.strip(),
                    "comment":comment_txt,
                    "author":author.text.strip(),
                    "url":article_url,
                    "date":date.text.strip()
                }
                web_content_list.append(json_dict)
                # step 6: save the data to a csv file
                with open("ptt_stock_title.csv", "a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([json_dict["title"],json_dict["comment"],json_dict["author"],json_dict["url"],json_dict["date"]])
            ## web scraping from the previous page
            page_soup=soup.find_all("div",class_="btn-group btn-group-paging")
            prev_url=get_previous_page(page_soup)
            if prev_url:
                url="https://www.ptt.cc"+prev_url
                #print(prev_url)
            else:
                print("沒有上一頁")
            if i%100==0:
                print(f"已爬取{i}頁")
            time.sleep(0.5)
    except requests.exceptions.Timeout:
        print("請求超時，請稍後再試")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
