import concurrent.futures
from Newsletter import Newsletter
from newsarticle import SearchQuery, StockNewsArticle
import logging
import threading
import requests
class StockNewsParallel():
    
    def __init__(self):
        self.local_data = threading.local()

    def process_row(self,row,df):
        try:
            search_query = SearchQuery(row['company_name'],'when:1d','en',['boerse.de','ft.com', 'marketscreener.com', 'handelsblatt.com','investing.com','bloomberg.com','hackernoon.com'])
            stock_news = StockNewsArticle(search_query)

            stock_news.set_stock_news()
            stock_news.add_news_article_to_df(df, row.name)
        except Exception as error:
             logging.error(error)

    def get_news_by_company_parallel(self,data):
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.process_row, row, data) for _, row in data.iterrows()]
                concurrent.futures.wait(futures)
        except Exception as error:
            logging.error(error)

class NewsletterParallel():
    def send_newsletter_parallel(self,customers,companies, articles_df):
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                newsletters = [Newsletter(customer, company, articles_df) for customer, company in zip(customers, companies)]
                futures = [executor.submit(newsletter.send_newsletter) for newsletter in newsletters]
                concurrent.futures.wait(futures)
        except Exception as error:
            logging.error(error)