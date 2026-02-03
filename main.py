## import libraries
import requests
from bs4 import BeautifulSoup
import csv,os,time
import logging
logging.basicConfig(level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s")
## global variable
web_content_list=[]
message_list=[]
MAX_RETRY=5

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
            json_dict={
                "title":title.text.strip(),
                "comment":comment_txt,#推噓數
                "author":author.text.strip(),
                "url":article_url,
                "date":date.text.strip()
            }
            web_page_content=scrape_web_page_content(headers,article_url)
            if web_page_content:
                json_dict["comment_and_content"]=web_page_content
            else:
                print(f"Error: {article_url}")
                continue
            web_content_list.append(json_dict)
            #using two csv files-title and comment_info
            with open("ptt_stock_title.csv", "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([json_dict["title"],json_dict["comment"],json_dict["author"],json_dict["url"],json_dict["date"],json_dict["comment_and_content"]["content"]])
            with open("ptt_stock_comment_info.csv", "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                for item in json_dict["comment_and_content"]["comment_info"]:
                    writer.writerow([json_dict["url"],json_dict["title"],item["id"],item["message"],item["pro_and_con"]])
        return True
    else:
        return False
def scrape_web_page_content(headers,url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    main_content=soup.find("div",id="main-content")
    article_content=[]
    comment_info=[]
    if main_content:
        #get comment_info
        for item in main_content.find_all("div",class_="push"):
            message=item.find("span",class_="push-content")
            id=item.find("span",class_="push-userid")
            pro_and_con=item.find("span",class_="push-tag")
            if not (message and id and pro_and_con):
                continue
            content_dict={
                "id":id.text.strip(),
                "message":message.text.strip(),
                "pro_and_con":pro_and_con.text.strip(),
            }
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
        return {"content":article_content,"comment_info":comment_info}
    else:
        return False

#init    
url = "https://www.ptt.cc/bbs/stock/index.html" #初始url
file_exists = os.path.exists("ptt_stock_title.csv")
with open("ptt_stock_title.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Title","推噓數","Author","Url","Date"]) 
with open("ptt_stock_comment_info.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Url","Title","Id","Message","Pro_and_Con"]) 
for i in range(2):#爬蟲頁數
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