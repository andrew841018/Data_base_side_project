## import libraries
import requests
from bs4 import BeautifulSoup
import csv,os,time
import logging
from datetime import datetime
logging.basicConfig(level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s")
## global variable
MAX_RETRY=5
article_index=1
index=1

# functions
def get_previous_page(soup):
    for item in soup:
        prev_soup=item.find("a",string=lambda t:t and "上頁" in t)
        if not prev_soup:
            continue
        else:
            prev_page=prev_soup.get("href")
            return prev_page
    return False
def scrape_web_page_title(headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    data = soup.find_all("div", class_="r-ent")
    global article_index
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
            skip_list=["公告","盤後閒聊","盤中閒聊","情報"]
            if any(keyword in title.text for keyword in skip_list):
                continue
            web_page_content=scrape_web_page_content(headers,article_url,article_index)
            if not web_page_content:
                continue
            json_dict={
                "Article_id":article_index,
                "Title":title.text.strip(),
                "Push_count":comment_txt,#推噓數
                "Author":author.text.strip(),
                "Url":article_url,
                "Date":date.text.strip(),
                "Content":web_page_content["Content"],
                "Scraped_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            article_index+=1
            #using two csv files-title and comment_info
            with open("ptt_stock_article_info.csv", "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([json_dict["Article_id"],json_dict["Title"],json_dict["Push_count"],json_dict["Author"],json_dict["Url"],json_dict["Date"],json_dict["Content"],json_dict["Scraped_time"]])
            with open("ptt_stock_comment_info.csv", "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                for item in web_page_content["Comment_info"]:
                    writer.writerow([item["Comment_id"],item["Article_id"],item["User_id"],item["Push_tag"],item["Message"]])
        return True
    else:
        return False
def scrape_web_page_content(headers,url,article_id):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    main_content=soup.find("div",id="main-content")
    article_content=[]
    comment_info=[]
    global index
    if main_content:
        #get comment_info
        for item in main_content.find_all("div",class_="push"):
            message=item.find("span",class_="push-content")
            user_id=item.find("span",class_="push-userid")
            pro_and_con=item.find("span",class_="push-tag")
            if not (message and id and pro_and_con):
                continue
            content_dict={
                "Comment_id":index,
                "Article_id":article_id,
                "User_id":user_id.text.strip(),
                "Push_tag":pro_and_con.text.strip(),
                "Message":message.text.strip(),
            }
            index+=1
            comment_info.append(content_dict)
        #get content of the article
        for item in main_content.find_all("div",class_="push"):#刪除推文
            item.decompose()
        for item in main_content.find_all("div",class_=lambda c:c and "article" in c):#標題相關資訊刪除
            item.decompose()
        for item in main_content.find_all("span",class_="f2"):#remove 發信站＋文章網址
            item.decompose()
        for line in main_content.text.strip().split("\n"):
            if("引述" in line):
                continue
            if(line.startswith(": ") or line.startswith("http")):
                continue
            if line.strip():
                article_content.append(line.strip())
        article_content="\n".join(article_content)
        time.sleep(0.3) 
        return {"Content":article_content,"Comment_info":comment_info}
    else:
        return False

#init    
url = "https://www.ptt.cc/bbs/stock/index.html" #初始url
with open("ptt_stock_article_info.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Article_id","Title","Push_count","Author","Url","Date","Content","Scraped_time"]) 
with open("ptt_stock_comment_info.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Comment_id","Article_id","User_id","Push_tag","Message"]) 
for i in range(50):#爬蟲頁數
    retry = 0
    while retry < MAX_RETRY:
        try:
            headers = {"cookie": "over18=1"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            logging.info(f"第{i+1}頁")
            if not scrape_web_page_title(headers):
                print("Error: scrape_web_page_title")
                break
            time.sleep(0.5)#delay for 0.5 seconds
            page_soup=soup.find_all("div",class_="btn-group btn-group-paging")
            prev_url=get_previous_page(page_soup)
            if prev_url:
                url="https://www.ptt.cc"+prev_url
            else:
                logging.info("沒有上一頁")
                break
            break;#成功後跳出retry
        except requests.exceptions.Timeout:
            logging.error("請求超時，請稍後再試")
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error: {e}")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection Error: {e}")
        except Exception as e:
            logging.error(f"Error: {e}")
        retry += 1
logging.info("爬蟲完成")