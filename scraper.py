# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import scraperwiki
import datetime

import sys

reload(sys)
sys.setdefaultencoding('utf8')

#a quick and dirty script to scrape/harvest resource-level metadata records from data.gov.sg
#the original purpose of this work is to support the ongoing international city open data index project led by SASS

#shanghai portal is needed to be parsed at html level

#this is for api list, for the data list, please refer to the morph version


#NOTE that we parse dataproduct and dataapi seperately and the dirty solution is manually replace the url and set index accordingly
#to crawl both product and api, so do not forget to set file writer method to 'a' when you work on api list
base_url = 'http://www.data.sh.gov.cn/query!queryInterface.action?currentPage='
index = int(os.environ['MORPH_START'])
#manually check on the website and set the max_index accordingly
max_index = int(os.environ['MORPH_MAX'])

#we need random ua to bypass website security check
ua = UserAgent()
headers = {'User-Agent':ua.random}


#we create a metadata dict as it might be possible that for some dataset some metadata may be missing or in wrong order
meta_dict = {
            '摘要：':'desc',
            '应用场景：':'',
            '数据标签：':'',
            '关键字：':'tags',
            '数据领域：':'topics',
            '国家主题分类：':'',
            '部门主题分类：':'',
            '公开属性：':'openness',
            '更新频度：':'frequency',
            '首次发布日期：':'created',
            '更新日期：':'updated',
            '访问/下载次数：':'count',
            '接口提供方：':'org',
            }
today_date = datetime.date.today().strftime("%m/%d/%Y")
package_count = 1

for i in range(index,max_index+1):
    url = base_url + str(i)
    print(url)
    result = requests.get(url,headers=headers)
    soup = BeautifulSoup(result.content,features='lxml')
    #fetch all dt blocks and get rid of the first 5 as they are irrelevant
    package_blocks = soup.find_all('dt')[5:]
    for p in package_blocks:
        #we create a package_dict to store
        package_dict = {
                        'today':'',
                        'id':'',
                        'index_url':'',
                        'url':'',
                        'name':'',
                        'desc':'',
                        'org':'',
                        'topics':'',
                        'tags':'',
                        'created':'',
                        'updated':'',
                        'frequency':'',
                        'count':
                            {
                            'view':'0',
                            'download':'0'
                            },
                        'openness':'',

        }
        #for each package block on the list page, we parse the url to detail page, and package title
        package_dict['today']=today_date
        package_dict['id'] = package_count
        package_dict['index_url']=url
        package_dict['url'] = "http://www.datashanghai.gov.cn/"+p.a['href']
        package_dict['name'] = p.a['title']
        package_dict['topics'] = p.strong.text
        print(package_dict['url'])
        print(package_dict['name'])
        result = requests.get(package_dict['url'],headers=headers)
        #now for each package block, we fetch back its detail page and parse its metadata
        soup = BeautifulSoup(result.content,features='lxml')
        #there are 4 tables on detail page
        tables = soup.find_all('table')
        #the first one contains metadata
        metadata_table = tables[0]
        trs =  metadata_table.find_all('tr')
        for tr in trs:
            key = re.sub('[\r\t\n ]+', '', tr.th.text)
            value = re.sub('[\r\t\n ]+', '', tr.td.text)
            print(key,value)

            if key == '访问/下载次数：':
                view,download = value.split('/')
                print(view,download)
                package_dict['count']['view'] = view
                package_dict['count']['download'] = download
            else:
                # for meta_dict elements that not mapped into package_dict it will create a '' key in package_dict
                package_dict[meta_dict[key]] = value
            print(package_dict)
        del package_dict['']

        #output the result
        #note for tags, it might be splited by , or chinese , or chinese 、
        row = package_dict['name']+','+'"'+package_dict['desc']+'"'+','+package_dict['org']+','+package_dict['topics'] \
                +','+"|".join(re.split(r'[,，、]\s*', package_dict['tags']))+','+package_dict['created']+','+package_dict['frequency']\
                +','+package_dict['updated']+','+package_dict['openness']+','+package_dict['count']['view']+','+package_dict['count']['download']+'\n'
        print(row)
        scraperwiki.sqlite.save(unique_keys=['today','id'],data=package_dict)
        print('****************end---'+package_dict['name']+'---end****************')
        package_count = package_count + 1

