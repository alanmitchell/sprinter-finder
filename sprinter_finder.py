# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Webscrape Sprinter Camper Vans

# %%
from time import sleep
from datetime import datetime
import re
from random import randint #avoid throttling by not sending too many requests one after the other
from warnings import warn
from time import time
from IPython.core.display import clear_output
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from IPython.display import display, Markdown

# import get to call a get request on the site
from requests import get
from jinja2 import Template


# %%
#build out the loop
#find the total number of posts to find the limit of the pagination
#results_num = html_soup.find('div', class_= 'search-legend')
#results_total = int(results_num.find('span', class_='totalcount').text) #pulled the total count of posts as the upper bound of the pages array

#each page has 119 posts so each new page is defined as follows: s=120, s=240, s=360, and so on. So we need to step in size 120 in the np.arange function
#pages = np.arange(0, results_total+1, 120)

iterations = 0

days_ago = []
post_title_texts = []
post_links = []
post_prices = []
search_ixs = []
post_ixs = [] 

# Craiglist cities to search
cities = (
    'anchorage',
    'fairbanks',
    'portland',
    'seattle',
    'denver',
    'madison',
    'boulder',
    'bozeman',
    'boise',
    'sfbay',
    'phoenix',
    'saltlakecity',
    'albuquerque',
    'minneapolis',
    'wyoming',
    'losangeles',
)

# Search strings
searches = (
    #'query=Thule+easyfold',
    'query=Thule+Motion+XXL',
    #'min_price=40000&max_price=100000&query=sprinter+4x4+camper',
    #'min_price=40000&max_price=100000&query=sprinter+4x4+conversion',
    #'min_price=40000&max_price=100000&query=sprinter+4wd+camper',
    #'query=electric+bicycle&min_price=700&max_price=2000',
)
post_ix = 0    # counts the posts downloaded
for city in cities:
        
    for search_ix, search in enumerate(searches):

        #get request
        response = get(f"https://{city}.craigslist.org/search/sss?{search}&" 
                       + "s=0" #the parameter for defining the page number 
                      )
        sleep(randint(1,5))

        #throw warning for status codes that are not 200
        if response.status_code != 200:
            warn('Request: {}; Status code: {}'.format(requests, response.status_code))

        #define the html text
        page_html = BeautifulSoup(response.text, 'html.parser')

        #define the posts
        posts = page_html.find_all('li', class_= 'result-row')

        #extract data item-wise
        for post in posts:

            # posting date
            # grab the datetime element 0 for date and 1 for time
            post_datetime = post.find('time', class_= 'result-date')['datetime']
            dt = datetime.strptime(post_datetime, '%Y-%m-%d %H:%M')
            ago = (datetime.now() - dt).days

            # title text
            post_title = post.find('a', class_='result-title hdrlnk')
            post_title_text = post_title.text

            # Filter out some posts
            title_lower = post_title_text.lower()

            excl_words = (
                'promaster',
                'ford',
                'porsche',
                'dodge',
                'isuzu',
                'roadster',
                'toyota',
                'jeep',
            )
            done = False
            for wd in excl_words:
                if wd in title_lower:
                    done = True
            if done:
                continue

            # post link
            post_link = post_title['href']

            # removes the \n whitespace from each side, removes the currency symbol, and turns it into an int
            try:
                post_price = int(post.a.text.strip().replace("$", "")) 
            except:
                continue
                
            
            days_ago.append(ago)
            post_title_texts.append(post_title_text)
            post_links.append(post_link)
            post_prices.append(post_price)
            search_ixs.append(search_ix)
            post_ixs.append(post_ix)
            post_ix += 1

        iterations += 1
        print('.', end='', flush=True)

print("\nScrape complete!")

vans = pd.DataFrame({'days_ago': days_ago,
                       'title': post_title_texts,
                        'URL': post_links,
                       'price': post_prices,
                       'search_ix': search_ixs,
                       'post_ix': post_ixs,
                    })

# first things first, drop duplicate URLs because people are spammy on Craigslist. 
vans = vans.drop_duplicates(subset='URL')

# Download the detailed post page for the remaining items
print('Downloading Posts...')
local_urls = []
for row_ix, row in vans.iterrows():
    post_html = get(row.URL).text
    post_lines = post_html.splitlines()
    for ix, line in enumerate(post_lines):
        if 'class="tryapp"' in line:
            start_ix = ix
            break
    for ix, line in enumerate(post_lines):
        if 'class="postingtitle"' in line:
            end_ix = ix
            break
    post_lines = post_lines[:start_ix] + post_lines[end_ix:]
    local_url = f'posts/{row_ix}.html'
    open(local_url, 'w').write('\n'.join(post_lines))
    local_urls.append(local_url)
    print('.', end='', flush=True)
    sleep(randint(1,5))
vans['local_url'] = local_urls

result = ''
for ix, srch in enumerate(searches):
    result += f'\n### {srch}\n\n'
    for _, row in vans.sort_values(by=['days_ago']).query(f'search_ix == {ix}').iterrows():
        result += f'[${row.price:.0f}, {row.days_ago} days ago, {row.title}]({row.URL})\n\n'
Markdown(result)


# %%
results = []
for ix, srch in enumerate(searches):
    srch = srch.replace('&', '<br>').replace('+', ' ')
    items = []
    for _, row in vans.query(f'search_ix == {ix}').sort_values(by=['days_ago']).iterrows():
        items.append((f'${row.price:.0f}, {row.days_ago} days ago, {row.title}', row.URL, row.local_url))
    results.append((srch, items))
t = Template(open('results_tmpl.html',).read())
open('results.html', 'w').write(t.render(results=results))


# %%
len(vans)

