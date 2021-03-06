import apsw
import feedparser
from webpreview import TwitterCard, web_preview
import datetime
import threading
from queue import Queue
import pprint


class GetAddNews(object):
    def __init__(self):
        self.articles_queue = Queue()
        self.full_article_queue = Queue()
        self.standard_agrix = "https://www.standardmedia.co.ke/rss/agriculture.php"
        self.standard_biz = "https://www.standardmedia.co.ke/rss/business.php"
        self.business_daily = "https://www.businessdailyafrica.com/539444-539444-view-asFeed-bfdflfz/index.xml"
        now = datetime.datetime.now()
        self.year = now.year
        self.month = now.month
        self.day = now.day
        conn = apsw.Connection("data.sqlite")
        self.cursor = conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS data (image VARCHAR(100), link VARCHAR(100), source VARCHAR(30), summary VARCHAR(300), title VARCHAR(100), year INTEGER, month INTEGER, day INTEGER)")
        self.cursor.execute("DELETE FROM data")


    def _write_to_db_from_queue(self, final_q):
        try:
            work = True
            
            while work:
                data = final_q.get(block = True)
                if(data is None):
                    work = False
                    # Notify Caesar Lambda
                    url = "https://c72b7oi5gk.execute-api.us-east-1.amazonaws.com/beta"
                    requests.post(url, {
                        data = {"success": True, "message": "Scrape complete"}
                    })
                    return
                else:
                    self.cursor.execute("INSERT INTO data (image, link, source, summary, title, year, month, day) VALUES(:a, :b, :c, :d, :e, :f, :g, :h)", {'a': data['image'], 'b': data['link'], 'c': data['source'],'d': data['summary'],'e': data['title'], 'f': data['time']['year'], 'g': data['time']['month'], 'h': data['time']['day']})
                    # Write to SQLLite db
        except Exception as e:
            url = "https://c72b7oi5gk.execute-api.us-east-1.amazonaws.com/beta"
            requests.post(url, {
                data = {"success": True, "message": f"An error occured -> {e}"}
            })
            raise RuntimeError(e)

    def _get_article_image(self, article_q, final_q):
        """ Gets article link and other info, then gets URL for that article image
        """
        try:
            work = True
            while work:
                data = article_q.get(block = True)
                if(data is None):
                    work = False
                    final_q.put(None)
                    return
                else:
                    source = data["source"]
                    article_title = data["title"]
                    article_summary = data["summary"]
                    article_link = data["link"]
                    t = data["time"]

                    tc = TwitterCard(article_link, ["twitter:image"])
                    if(tc.image is None):
                        _, _, image = web_preview(article_link, parser = "html.parser")
                        if(image is None):
                            if(source == "standard_agrix"):
                                img = "https://www.farmers.co.ke/assets/images/logo.png"
                            elif(source == "standard_biz"):
                                img = "https://www.standardmedia.co.ke/common/i/standard-digital-world-inner-page.png"
                            elif(source == "business_daily"):
                                img = "https://www.businessdailyafrica.com/image/view/-/3818190/medRes/1349497/-/3ijc6bz/-/logoNew.png"
                        else:
                            img = image

                    else:
                        img = tc.image

                    fin_dict = {"title": article_title, "summary": article_summary, "link": article_link, "source": source, "image": img, "time": t}

                    final_q.put(fin_dict)
        except Exception as e:
            raise RuntimeError(e) 

    def _get_article_info(self, article):
        """ Gets a feedparse entry object then extracts info
        """
        article_title = article["title"]
        article_summary = article["summary"]
        article_link = article["link"]

        return article_title, article_summary, article_link

    def get_articles(self):
        img_thread = threading.Thread(target = self._get_article_image, args = (self.articles_queue, self.full_article_queue, ))
        img_thread.start()

        writer_thread = threading.Thread(target = self._write_to_db_from_queue, args = (self.full_article_queue, ))
        writer_thread.start()

        agrix_content = feedparser.parse(self.standard_agrix)
        for entry in agrix_content["entries"]:
            title, summary, link = self._get_article_info(entry)
            article_dict = {"title": title, "summary": summary, "link": link, "source": "standard_agrix", "time": {"year": self.year, "month": self.month, "day": self.day}}
            self.articles_queue.put(article_dict)

        business_content = feedparser.parse(self.standard_biz)
        for entry in business_content["entries"]:
            title, summary, link = self._get_article_info(entry)
            article_dict = {"title": title, "summary": summary, "link": link, "source": "standard_biz", "time": {"year": self.year, "month": self.month, "day": self.day}}
            self.articles_queue.put(article_dict)

        business_daily = feedparser.parse(self.business_daily)
        for entry in business_daily["entries"]:
            title, summary, link = self._get_article_info(entry)
            article_dict = {"title": title, "summary": summary, "link": link, "source": "business_daily", "time": {"year": self.year, "month": self.month, "day": self.day}}
            self.articles_queue.put(article_dict)

        
        self.articles_queue.put(None)
        

if __name__ == "__main__":
    GetAddNews().get_articles()
