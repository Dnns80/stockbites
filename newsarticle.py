from bs4 import BeautifulSoup
import requests
from newspaper import Article
import pandas as pd
import logging
import time
import nltk
from openai import OpenAI
import os

class SearchQuery:
    def __init__(self, search_term, time_constraint, language, blocked_sites):
        self.search_term = search_term
        self.time_constraint = time_constraint
        self.language = language
        self.blocked_sites = '-'+ ' -'.join(blocked_sites)

class RssUrl:
    def __init__(self,SearchQuery):
        self.SearchQuery = SearchQuery
        self.urls = None
        self.timeout = 15
    
    def __str__(self):
        rss_url = f"https://news.google.com/rss/search?q={self.SearchQuery.search_term} AND (stock OR company) {self.SearchQuery.blocked_sites} {self.SearchQuery.time_constraint}&hl={self.SearchQuery.language}:de"
        return rss_url

    def get_urls(self):
        url = self.__str__()
        
        result = requests.get(url,timeout=self.timeout)
        content = result.content

        soup = BeautifulSoup(content, 'xml')
        
        links = [link.text.strip() for link in soup.select('item link')[:10]] 
        self.urls = links

class NewsArticle:
    def __init__(self, news_article_url,company_name):
            self.news_article_url = news_article_url
            self.title = None
            self.summary = None
            self.company_name = company_name

    def is_relevant(self,text):
        
        try:
            client = OpenAI(api_key =f"{os.getenv('OPENAI_API_KEY')}")
            
            chat_completion = client.chat.completions.create(
                                messages=[
                {"role": "system", "content": f"Assist in evaluating the relevance of news articles for stakeholders interested in '{self.company_name}'. Look for articles that provide insights into the company's operations, strategy, partnerships, or industry developments. Exclude information related to stock price targets, technical analysis, or speculative content. Affirm relevance with 'True' and negate with 'False'. If the text does not seem to be a a news article at all, return 'False'."},
                {"role": "user", "content": text},
                ],
                model="gpt-4",
                timeout = 30,
                            )
            
            return chat_completion.choices[0].message.content == 'True'
        except Exception as error:
            logging.error(error)

    def summarize_article(self,text):
        try:
            client = OpenAI(api_key =f"{os.getenv('OPENAI_API_KEY')}")
            
            chat_completion = client.chat.completions.create(
                                messages=[
                {"role": "system", "content": f"Efficiently distill the essence of news articles from any language into a succinct 2-3 sentence summary in English, capturing the core information and context which are relevant to the '{self.company_name}'company/stock .Return the summary."},
                {"role": "user", "content": text},
                ],
                model="gpt-3.5-turbo",
                timeout = 30,
                )
            self.summary = chat_completion.choices[0].message.content
        except Exception as error:
            logging.error(error)

    def make_nice_title(self,title):
        try:
            client = OpenAI(api_key =f"{os.getenv('OPENAI_API_KEY')}")
            
            chat_completion = client.chat.completions.create(
                                messages=[
                {"role": "system", "content": "Return a concise, captivating English headline from any given news article title in any language. If the original title is already optimal, simply return an accurate English translation."},
                {"role": "user", "content": title},
                ],
                model="gpt-4",
                timeout = 30,
                )
            self.title = chat_completion.choices[0].message.content.strip('"')
        except Exception as error:
            logging.error(error)


    def parse_news_website(self):
        try:
            article = Article(self.news_article_url)
            article.download()
            article.parse()
    
            is_parsed_correct = article.title is not None and article.title != "" and article.text is not None and article.text != ""
            if not is_parsed_correct:
                self.summary = None
                return
            
            if self.is_relevant(article.text):
                self.make_nice_title(article.title)
                self.summarize_article(article.text)
            else:
                self.summary = None
        except Exception as error:
            logging.error(error)
    
    def is_valid(self):
        if self.summary is not None and self.title is not None:
            return True
        return False

    def get_news_article(self):
            return {
                'url': self.news_article_url,
                'title': self.title,
                'text': self.summary
            }

class StockNewsArticle:
    def __init__(self, SearchQuery):
        self.SearchQuery = SearchQuery
        self.stock_news_article = None
        self.timeout = 15

    def detect_paywall_and_get_url(self,resp):
        if 'paywall' in resp.text:
            return None
        return resp.url 

    def get_realURL(self,url):
        cookies = {'CONSENT': 'YES+'}
        response = requests.get(url, cookies=cookies, allow_redirects=False,timeout=self.timeout)
        response_real_url = requests.get(response.headers['Location'],timeout=self.timeout)

        if('consent.google.com' not in response_real_url.url):
            return self.detect_paywall_and_get_url(response_real_url)
        return None

    def get_valid_news_article(self,rss_url):
        for url in rss_url.urls:
            try:
                real_url = self.get_realURL(url)

                article = NewsArticle(real_url,self.SearchQuery.search_term)
                article.parse_news_website()

                if article.is_valid():
                    return article
            except Exception as error:
                logging.error(error)
                continue
        return None
    
    def set_stock_news(self):
        try:
            rss_url = RssUrl(self.SearchQuery)
            rss_url.get_urls()

            news_article = self.get_valid_news_article(rss_url)

            if news_article:
                self.stock_news_article = news_article.get_news_article()
        except Exception as error:
            logging.error(error)
    
    def add_news_article_to_df(self,df, label):
        
        df.at[label, 'news_articles'] = self.stock_news_article


