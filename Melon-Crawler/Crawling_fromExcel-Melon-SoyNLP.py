# # Crawling_fromExcel-Melon-SoyNLP

# 형용사 태그 중 감정 단어는 기존 방법처럼 Konlpy 의 Okt 를 사용하고, 
# 
# 명사는 새로운 라이브러리인 **SoyNLP** 를 사용해 추출한다.

# In[1]:


# 필요한 라이브러리 불러오기
import os
import warnings
warnings.filterwarnings(action='ignore')
from selenium import webdriver as wd
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import random
import re
import pandas as pd
from konlpy.tag import Okt
from collections import Counter
from soynlp.utils import DoublespaceLineCorpus
from soynlp.noun import LRNounExtractor_v2
okt = Okt()


# In[2]:


# 불용어 사전 불러오기
with open('Melon/stop_words.txt', 'r') as file:
    stop_word = file.readline()
    stop_word = str(stop_word)
    
stop_word = stop_word.replace("\ufeff", '').replace("'", '').replace(",", '').replace('\n', '').replace("’", '').replace("‘", '')
stop_words = stop_word.split()


# In[3]:


# 불용어 사전 불러오기
with open('Melon/stop_words-nouns.txt', 'r') as file:
    stop_words_nouns = file.readline()
    stop_words_nouns = str(stop_words_nouns)
    
stop_words_nouns = stop_words_nouns.replace("\ufeff", '').replace("'", '').replace(",", '').replace('\n', '').replace("’", '').replace("‘", '')
stop_words_nouns = stop_words_nouns.split()


# In[4]:


# 곡 제목, 유튜브 링크가 있는 데이터 프레임(엑셀 파일)을 불러옴
data = pd.read_excel('Melon/melon_music_list.xlsx')
data
print(data)


# In[8]:


data_lst = data['Site Link'].tolist() # Series to List
data_lst



# In[12]:


for k in range(len(data)):
    
    # 댓글 페이지 개수 구하기
    driver = wd.Chrome(executable_path='/Users/lifeofpy/Desktop/chromedriver')
    page_url = data_lst[k] # url 에 페이지 링크를 하나씩 담아준다
    driver.get(page_url)
    comments = []
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    pages = soup.find_all('span', {'class': 'd_cmtpgn_srch_cnt'})[0]

    # 일단 추출된 태그를 문자열로 바꾸기
    pages = str(pages)

    # 정규식을 통해 태그에서 숫자(=댓글 개수)만 추출하기
    cmt_num = re.findall('\d+', pages)
    page_num = "".join(cmt_num)
    page_num = int(page_num)
    page_num = page_num//10
        
    # 댓글 페이지마다 바뀔 url 생성
    url = page_url + '#cmtpgn=&pageNo={}&sortType=0&srchType=2&srchWord='
    
    
    for i in range(0, page_num+1):
        link = url.format(i) # {} 안에 들어갈 문자열 포매팅
        driver.get(link)
        driver.implicitly_wait(2)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        comment = soup.find_all('div', {'class': 'd_cmtpgn_cmt_full_contents'})

        for r in comment:
            comments.append(r.get_text().strip())
            
    
    # 가수 이름을 멜론으로부터 추출해서 나올 수 있는 불용어 추가하기
    singer = soup.find(attrs={'class':'artist_name'}).find('span').text
    singer = str(singer)
    singer = singer.split()
    print(singer)
    for i in range(len(singer)):
        if "'" in singer[i]:
            real_singer = str(singer[0:-1]).replace('[', '').replace(']', '').replace(',', '').replace("'", '')
        elif "(" in singer[i]:
            real_singer = singer[i-1]
            break
        else:
            # 리스트에 있는 원소를 공백 없이 하나로 합쳐야함
            real_singer = "".join(singer)
            
    print('쿼리에 들어가는 가수 이름:', real_singer)
    
    # 가수 이름을 네이버에 검색해서 영문 가수 이름을 한글로 바꿔 singer 에 저장하기 (예시: aespa >> 에스파)
    # 드라이버 url 멜론 >> 네이버로 바꿔주기
    naver_url = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%s'%(real_singer)
    driver.get(naver_url)
    driver.implicitly_wait(2)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    name_of_singer = soup.find(attrs={'class':'title _title_ellipsis'}).find('span').text
    if len(name_of_singer) != 0:
        real_singer = soup.find(attrs={'class':'title _title_ellipsis'}).find('span').text
    else:
        real_singer = singer[0]
    
    stop_words_nouns.append(real_singer) # 에스파
    stop_words_nouns.append(real_singer + '님') # 에스파님
    stop_words_nouns.append(real_singer + '님들') # 에스파님들
    stop_words_nouns.append('갓' + real_singer) # 갓에스파
    stop_words_nouns.append(real_singer + '짱') # 에스파짱
    stop_words_nouns.append(real_singer + '분들') # 에스파분들
    stop_words_nouns.append(real_singer + '멤버') # 에스파멤버
    stop_words_nouns.append(real_singer + '멤버들') #에스파멤버들
    stop_words_nouns.append(real_singer + '님들목소리') #에스파님들목소리
    stop_words_nouns.append(real_singer + '멤버들목소리') #에스파멤버들목소리
    
    
    # 가수가 2명 이상의 그룹이라면, 멤버 이름도 불용어에 추가하기 (예시: 카리나, 윈터, 지젤, 닝닝)
    member_lst = []

    is_member_more_than_2 = soup.find(attrs={'class':'info_group'}).find('dt').text
    if is_member_more_than_2 == '멤버':
        soup = soup.find(attrs={'class':'info_group'}).find('dd')
        soup.find_all('a')
        
    member_lst.append(soup.text)
        
    member_lst = str(member_lst).replace("'", "").replace("[", "").replace("]", "").replace('(', "").replace(')', "").replace('보컬', '').replace('리더', '').replace(" ", '').replace('메인', '').replace('랩', '')
    member_lst = member_lst.split(',')
    # print(member_lst)
    
    for i in range(len(member_lst)):
        stop_words_nouns.append(member_lst[i]) # 카리나
        stop_words_nouns.append(member_lst[i] + '님') # 카리나님
        stop_words_nouns.append('갓' + member_lst[i]) # 갓카리나
        stop_words_nouns.append(member_lst[i] + '짱') # 카리나짱
        stop_words_nouns.append(member_lst[i] + '목소리') # 카리나목소리
        stop_words_nouns.append(member_lst[i] + '님목소리') # 카리나님목소리
        stop_words_nouns.append(member_lst[i] + '부분') # 카리나부분
        stop_words_nouns.append(member_lst[i] + '파트') # 카리나파트

    # 멜론 댓글 모을 리스트 melon_comments 정의하기
    
    melon_comments = []
    melon_comments = comments
    
    # 댓글이 모인 comments 리스트에서 필요없는 문자 처리하기
    for j in range(len(melon_comments)):
        if '내용' in melon_comments[j]:
            melon_comments[j] = melon_comments[j].replace('내용', '')
    
    
    # 필요한 단어만 추출하기
    okts = []
    
    for i in range(len(melon_comments)):
        okts.append(okt.pos(melon_comments[i]))
    
    
    ### 명사 & 형용사 모을 리스트 정의
    real_top10_noun = []
    real_top20_adj = []
    
    
    # konlp okt --> 형용사
    adj = []
    
    # 품사 태그 중 형용사 태그만 추출하기
    for i in range(len(okts)):
        for j in range(len(okts[i])):
            if okts[i][j][1] == 'Adjective' and len(okts[i][j][0]) > 1:
                adj.append(okts[i][j][0])
                
    real_adj = []
    
    for w in adj:
        if w not in stop_words:
            real_adj.append(w)
            
            
    # 멜론 댓글을 txt 파일로 한번 저장하기
    with open('cmts.txt', 'w') as f:
        for line in melon_comments:
            f.write(line)
            
    
    # soynlp --> 명사
    noun = []
    real_noun = []
    
    corpus_path = 'cmts.txt'
    sents = DoublespaceLineCorpus(corpus_path, iter_sent=True)

    noun_extractor = LRNounExtractor_v2(verbose=True)
    nouns = noun_extractor.train_extract(sents)
    
    
    ### 명사, 형용사 중 조건에 해당하는 것만 추출해서 열에 넣기
    for key, value in nouns.items(): # v[0] = frequency, v[1] = score
        if value[0] >= 5 or value[1] >= 0.3:
            if len(key) > 1:
                noun.append(key)
                
    for w in noun:
        if w not in stop_words_nouns:
            real_noun.append(w)
    
        
    # 형용사
    count_adj = Counter(real_adj)

    top20_adj = count_adj.most_common(20)

    for i in range(len(top20_adj)):
        real_top20_adj.append(top20_adj[i][0])
        
        
    # 중복 제거
    real_top20_adj = set(real_top20_adj)
    real_noun = set(real_noun)
        
        
    data.loc[k, 'Emotional Words'] = str(real_top20_adj)
    data.loc[k, 'Noun Words'] = str(real_noun)
    
    # for loop 가 한번 돌아가면 txt 파일 클리어하고 새로 저장되게 하기
    file = open("cmts.txt", "w")
    file.write('')
    file.close()


# In[ ]:


# 데이터프레임 엑셀로 만들기
data.to_excel('Melon/Sample.xlsx', index=False)


# In[ ]:


data






