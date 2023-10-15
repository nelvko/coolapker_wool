#!/usr/bin/python3
import re
import sys
import requests
import time
import yaml

with open("./config.yml", 'r', encoding='utf-8') as f:
    config = f.read()
    c = yaml.load(config, Loader=yaml.FullLoader)  # 用load方法转字典

interval_minute = c.get("filter").get("interval_minute") * 60
diy_replynum = c.get("filter").get("diy_replynum")
bark = c.get('bark')
bark_key = bark.get("key")
url_scheme = bark.get("url")

none_num = 0
now = time.time()
history_set = set()

raw_url = "https://api.coolapk.com/v6/page/dataList?url=%23/feed/multiTagFeedList?listType=lastupdate_desc&isIncludeTop=1&hiddenTagRelation=1&ignoreEntityById=1&tag=%E8%96%85%E7%BE%8A%E6%AF%9B%E5%B0%8F%E5%88%86%E9%98%9F&page=1&title=%E6%9C%80%E8%BF%91%E5%9B%9E%E5%A4%8D"
de_url = '''
https://api.coolapk.com/v6/page/dataList?url=#/feed/multiTagFeedList
?listType=lastupdate_desc
&isIncludeTop=1
&hiddenTagRelation=1
&ignoreEntityById=1
&tag=薅羊毛小分队
&page=1
&title=最近回复
'''
req_headers = f'''
Host: api.coolapk.com
Accept: */*
X-Requested-With: XMLHttpRequest
X-App-Token: {c.get('req_headers').get('X-App-Token')}
Accept-Encoding: br;q=1.0, gzip;q=0.9, deflate;q=0.8
X-Sdk-Locale: zh-CN
X-Api-Version: 13
X-App-Code: 2309071
X-App-Device: {c.get('req_headers').get('X-App-Device')}
User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 (#Build; Apple; iPhone 14 Pro Max; iOS17.0.3; 17.0.3) +iCoolMarket/5.2.3-2309071
X-Sdk-Int: 17.0.3
X-App-Version: 5.2.3
Accept-Language: zh-Hans-CN;q=1.0
Connection: keep-alive
Cookie: {c.get('req_headers').get('Cookie')}
X-App-Id: com.coolapk.app
'''


def get_headers(header_raw):
    return dict(line.split(": ", 1) for line in header_raw.split("\n") if line != '')


def is_popular(create_time, lastupdate, replynum) -> bool:
    if replynum >= diy_replynum:
        if lastupdate - create_time >= interval_minute:
            return True


def push_bark(message: str, url):
    message = re.sub(r'<a.*>.*</a>', '', message)
    message = re.sub(r'\n', '', message)
    message = re.sub(r'\[.*?]', '', message)  # [受虐滑稽]
    message = message.strip()
    bark_body = {
        "title": bark.get("title"),
        "body": message,
        # "group": "分组1",
        "icon": bark.get("icon"),
        "url": url_scheme,
        "copy": url
    }
    bark_url = f"https://api.day.app/{bark_key}"
    bark_headers = {"Content-Type": "application/json", "charset": "utf-8"}
    res = requests.post(url=bark_url, headers=bark_headers, json=bark_body)


def extract_and_bark(data_arr):
    global none_num
    for i in data_arr:
        message = i.get("message")
        create_time = i.get("create_time")
        lastupdate = i.get("lastupdate")
        replynum = i.get("replynum")
        likenum = i.get("likenum")
        shareUrl = i.get("shareUrl")
        id = i.get("id")
        if message is None or create_time is None or lastupdate is None or replynum is None or likenum is None or shareUrl is None:
            none_num += 1
            continue
        if is_popular(create_time, lastupdate, replynum):
            if id not in history_set:
                push_bark(message, shareUrl)
                history_set.add(id)
    print(f"log_info->空内容数量：{none_num}")


if __name__ == '__main__':
    res = requests.get(url=raw_url, headers=get_headers(req_headers))
    if res.status_code != 200:
        print(f"log_error->本次响应状态码{res.status_code}")
        sys.exit(1)
    data_arr = res.json().get("data")
    if data_arr is None:
        print(f"log_error->返回空data")
        sys.exit(1)
    extract_and_bark(data_arr)
