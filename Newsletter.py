import requests
import time
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import pandas as pd
class Newsletter:
    def __init__(self,customer,companies, news_articles_df):
        self.customer = customer
        self.companies = companies
        self.selected_companies_with_articles = news_articles_df[news_articles_df['company_name'].isin(self.companies)]
    
    def send_simple_message(self):
        try:
            message_data = {
                "from": "Stockbites <dailynewsletter@stockbites.pro>",
                "to": self.customer,
                "subject": f"Stockbites {datetime.today().strftime('%Y-%m-%d')}",
                "template": "stocknews_template_html2",
                "v:date":f"{datetime.today().strftime('%Y-%m-%d')}"
            }
            
            for i, company in enumerate(self.selected_companies_with_articles['company_name'].tolist()):
                message_data[f"v:company{i+1}"] = company

            for i, article in enumerate(self.selected_companies_with_articles['news_articles'].tolist()):
                article_prefix = f"v:c_{i + 1}"
                message_data[f"{article_prefix}content1"] = article['text']
                message_data[f"{article_prefix}link1"] = article['url']
                message_data[f"{article_prefix}title1"] = article['title']
            
            return requests.post(
                "https://api.eu.mailgun.net/v3/newsletter.stockbites.pro/messages",
                auth=("api", f"{os.getenv('MAILGUN_API_KEY')}"),
                data=message_data
            )
        except Exception as error:
            logging.error(error)

    def send_newsletter(self):
        try:
            if self.selected_companies_with_articles.empty == False:
                self.send_simple_message()
        except Exception as error:
            logging.error(error)
