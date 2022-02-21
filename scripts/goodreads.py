#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download goodreads info

"""
__author__ = "prakashsellathurai"
__copyright__ = "Copyright 2022"
__version__ = "1.0.1"
__email__ = "prakashsellathurai@gmail.com"

import feedparser
import yaml

USER_ID = "105903487"

READ_URL = "https://www.goodreads.com/review/list_rss/"+USER_ID+"?shelf=read"
CURRENTLY_READ_URL = "https://www.goodreads.com/review/list_rss/"+USER_ID+"?shelf=currently-reading"

DataToWrite = {}

for URL,shelf in zip([READ_URL,CURRENTLY_READ_URL],['read','currently-reading']):
    readsfeed = feedparser.parse(URL)
    if readsfeed.entries:
        contents = []
        for book in readsfeed.entries: # book_description  author_name
            contents.append({
                'title': book.title,
                'link': book.link,
                'desc': book.book_description,
                'author': book.author_name
            })
        DataToWrite[shelf] = contents



with open('../_data/goodreads.yml', 'w') as yaml_file:
    yaml.dump(DataToWrite, yaml_file, default_flow_style=False)

