import pandas as pd
import time
from parallelprocessing import StockNewsParallel, NewsletterParallel
import psycopg2
from dotenv import load_dotenv
import os
import json

def connect_to_db():
    conn = psycopg2.connect(f"{os.getenv('DATABASE_CONNECTION_URL')}")
    cur = conn.cursor()
    return cur

def get_customers_and_stocks():
    cur = connect_to_db()

    cur.execute("SELECT * FROM public.users;")
    data = cur.fetchall()
    #data = data[:3]
    email_addresses = [row[1] for row in data]
    company_names = [row[4] for row in data]
    return email_addresses,company_names

def get_stocknames(company_names):

    all_names = [name for sublist in company_names for name in sublist]

    unique_names = set(all_names)
    
    data = pd.DataFrame(unique_names, columns=['company_name'])

    data['news_articles'] = [[] for _ in range(len(data))]
    return data

def main():
    load_dotenv()

    email_addresses, company_names = get_customers_and_stocks()

    stocks = get_stocknames(company_names)
    paralell_processor = StockNewsParallel()
    paralell_processor.get_news_by_company_parallel(stocks)

    stocks = stocks.dropna(subset=['news_articles'])

    newsletter_processor = NewsletterParallel()
    newsletter_processor.send_newsletter_parallel(email_addresses,company_names,stocks)
    print(stocks)

start = time.time()
main()
end = time.time()
print(end-start)