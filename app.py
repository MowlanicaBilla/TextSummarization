# Streamlit
import streamlit as st

from bs4 import BeautifulSoup
import requests
import re
from collections import Counter 
from string import punctuation
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as stop_words
from youtube_transcript_api import YouTubeTranscriptApi as ytapi
import pandas as pd
import bs4 as bs  
import urllib.request  
from PIL import Image
from gensim.summarization import summarize as su_gs
from gensim.summarization import keywords
from gensim.summarization import mz_keywords
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize 
from sys import argv
import os
from nltk.tokenize import sent_tokenize, word_tokenize
from string import punctuation
from nltk.probability import FreqDist
from heapq import nlargest
from collections import defaultdict
from lxml import html
import requests
import pdftotext
from io import StringIO

# Abstractive
from transformers import pipeline

summarization = pipeline("summarization")


    
def tokenizer(s):
    tokens = []
    for word in s.split(' '):
        tokens.append(word.strip().lower())
        
    return tokens

def sent_tokenizer(s):
    sents = []
    for sent in s.split('.'):
        sents.append(sent.strip())
        
    return sents

def count_words(tokens):
    word_counts = {}
    for token in tokens:
        if token not in stop_words and token not in punctuation:
            if token not in word_counts.keys():
                word_counts[token] = 1
            else:
                word_counts[token] += 1
                
    return word_counts

def word_freq_distribution(word_counts):
    freq_dist = {}
    max_freq = max(word_counts.values())
    for word in word_counts.keys():  
        freq_dist[word] = (word_counts[word]/max_freq)
        
    return freq_dist

def score_sentences(sents, freq_dist, max_len=40):
    sent_scores = {}  
    for sent in sents:
        words = sent.split(' ')
        for word in words:
            if word.lower() in freq_dist.keys():
                if len(words) < max_len:
                    if sent not in sent_scores.keys():
                        sent_scores[sent] = freq_dist[word.lower()]
                    else:
                        sent_scores[sent] += freq_dist[word.lower()]
                        
    return sent_scores

def summarize(sent_scores, k):
    top_sents = Counter(sent_scores) 
    summary = ''
    scores = []
    
    top = top_sents.most_common(k)
    
    for t in top: 
        summary += t[0].strip() + '. '
        scores.append((t[1], t[0]))
        
    return summary[:-1], scores


st.title('Text Summarization')
#st.subheader('One stop for all types of summarizations')

st.set_option('deprecation.showfileUploaderEncoding', False)

image = Image.open('pic1.jpeg')
st.sidebar.image(image, use_column_width=True)
st.sidebar.markdown('<center> <h1>Summarizer</h1></center>',unsafe_allow_html=True)
st.sidebar.markdown('<center> Get summaries for your papers, articles, pdf etc.</center>',unsafe_allow_html=True)
st.sidebar.markdown('<center> <h3>Google helped me do it</h3></center>',unsafe_allow_html=True)
types_summ = st.sidebar.selectbox(
    "Types of Summarization",
    ("Abstractive","Extractive")
)


def textfunc():

    content = textfield123
    content = sanitize_input(content)

    sent_tokens, word_tokens = tokenize_content(content)
    sent_ranks = score_tokens(sent_tokens, word_tokens)
    st.write(summarize2(sent_ranks, sent_tokens, no_of_sentences))


def textfunc_torch():

    content = textfield123
    content = sanitize_input(content)

    content = content.strip().replace("\n","")
    summary = summarization(content)[0]['summary_text']
    st.write(summary)



def textforYT():

    a = ytapi.get_transcript(video_id)
    textstr = ""
    for i in a:
        textstr += i["text"]
    article = [textstr[i:i + 100] for i in range(0, len(textstr), 100)]
    res = '. '.join(textstr[i:i + 100] for i in range(0, len(textstr), 100))
    content = res


    sent_tokens, word_tokens = tokenize_content(content)
    sent_ranks = score_tokens(sent_tokens, word_tokens)
    st.write(summarize2(sent_ranks, sent_tokens, no_of_sentences))


def tokenize_content(content):
    stop_words = set(stopwords.words('english') + list(punctuation))
    words = word_tokenize(content.lower())
    return (sent_tokenize(content), [word for word in words if word not in stop_words])

def score_tokens(sent_tokens, word_tokens):
    word_freq = FreqDist(word_tokens)
    rank = defaultdict(int)
    for i, sent in enumerate(sent_tokens):
        for  word in word_tokenize(sent.lower()):
            if word in word_freq:
                rank[i] += word_freq[word]
    return rank

def sanitize_input(data):
    replace = {
        ord('\f') : ' ',
        ord('\t') : ' ',
        ord('\n') : ' ',
        ord('\r') : None
    }
    return data.translate(replace)

def summarize2(ranks, sentences, length):

    if int(length) > len(sentences):
        print('You requested more sentences in the summary than there are in the text.')
        return ''

    else:
        indices = nlargest(int(length), ranks, key=ranks.get)
        final_summary = [sentences[j] for j in indices]
        return ' '.join(final_summary)

def summarize(url_topull, num_of_words):
    # Obtain text
    scraped_data = urllib.request.urlopen(url_topull)  
    article = scraped_data.read()
    
    parsed_article = bs.BeautifulSoup(article,'lxml')
    paragraphs = parsed_article.find_all('p')
    article_text = ""
    for p in paragraphs:  
        article_text += p.text

    # Extract keywords
    stop_words = set(stopwords.words('english')) 
    keywords = mz_keywords(article_text,scores=True,threshold=0.003)
    keywords_names = []
    for tuples in keywords:
        if tuples[0] not in stop_words: 
            if len(tuples[0]) > 2:
                keywords_names.append(tuples[0])

    
    pre_summary = su_gs(article_text,word_count=num_of_words)
    
    summary = re.sub("[\(\[].*?[\)\]]", "", pre_summary)
    
    print_pretty (summary,keywords_names)

def print_pretty (summary, keywords_names):
    columns = os.get_terminal_size().columns
    
    printable = summary
    st.write(printable.center(columns))
    str_keywords_names = str(keywords_names).strip('[]')
    printable2 = str_keywords_names
    st.write(printable2.center(columns))



def extract_data(feed):
    with open(feed, "r") as f:
        pdf = pdftotext.PDF(f)
        pdf_text = "\n\n".join(pdf)
        return pdf_text


############################### ABSTRACTIVE ###################################

if types_summ == "Abstractive":

    url = st.text_input('\nEnter URL of news article from thehindu.com: ')

    #wikiurl = st.text_input('\nEnter URL of news article from Wikipedia.com: ')
    video_id = st.text_input("\nEnter the Youtube Video Id:")
    # video_id = "Na8vHaCLwKc" 
    toolbox = st.text_input('\nEnter URL of any article from Spiceworks.com')
    textfield123 = st.text_area('\nEnter article or paragraph you want to summarize ')
    pdf_file = st.file_uploader("Upload a Text file", type=["txt"])
    no_of_sentences = st.number_input('Choose the no. of sentences in the summary', min_value = 1)


    #st.write('You selected `%s`' % pdf_file)

    if pdf_file is not None:


        if no_of_sentences and st.button('Summarize the text file'):
            pdf_file = pdf_file.read()
            # To convert to a string based IO:
            stringio = StringIO(pdf_file)
            # To read file as string:
            text = stringio.read()
            text = re.sub(r'\[[0-9]*\]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            st.subheader('Original text: ')
            st.write(text)


            content = text.strip().replace("\n","")
            summary = summarization(content)[0]['summary_text']

            #st.write()
            
            st.subheader('Summarised text: ')
            st.write(summary)
            

            sentence = summary.count('.') + summary.count('!') + summary.count(';') + summary.count(':') + summary.count('?')
            words = len(summary.split())
            syllable = 0
            for word in summary.split():
                for vowel in ['a','e','i','o','u']:
                    syllable += word.count(vowel)
                for ending in ['es','ed','e']:
                    if word.endswith(ending):
                        syllable -= 1
                if word.endswith('le'):
                    syllable += 1
            G = round((0.39*words)/sentence+ (11.8*syllable)/words-15.59)
            if G >= 0 and G <= 30:
                st.write('The Readability level is College')
            elif G >= 50 and G <= 60:
                st.write('The Readability level is High School')
            elif G >= 90 and G <= 100:
                st.write('The Readability level is fourth grade')


    if url and no_of_sentences and st.button('Summarize Hindu Article'):
        text = ""
        
        r=requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser') 
        content = soup.find('div', attrs = {'id' : re.compile('content-body-14269002-*')})
        
        for p in content.findChildren("p", recursive = 'False'):
            text+=p.text+" "
                
        text = re.sub(r'\[[0-9]*\]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        st.subheader('Original text: ')
        st.write(text)
        
        content = text.strip().replace("\n","")
        summary = summarization(content)[0]['summary_text']
        
        st.subheader('Summarised text: ')
        st.write(summary)
        
        sentence = summary.count('.') + summary.count('!') + summary.count(';') + summary.count(':') + summary.count('?')
        words = len(summary.split())
        syllable = 0
        for word in summary.split():
            for vowel in ['a','e','i','o','u']:
                syllable += word.count(vowel)
            for ending in ['es','ed','e']:
                if word.endswith(ending):
                    syllable -= 1
            if word.endswith('le'):
                syllable += 1
        G = round((0.39*words)/sentence+ (11.8*syllable)/words-15.59)
        if G >= 0 and G <= 30:
            st.write('The Readability level is College')
        elif G >= 50 and G <= 60:
            st.write('The Readability level is High School')
        elif G >= 90 and G <= 100:
            st.write('The Readability level is fourth grade')



    if toolbox and no_of_sentences and st.button('Summarize Spiceworks Article'):
        text = ""
        page = requests.get(toolbox)
        tree = html.fromstring(page.content)
        # for p in content.findChildren("p", recursive = 'False'):
        #     text+=p.text+" "
        text = tree.xpath('//*[@id="root_post"]/p/text()')
        text = ' '.join(text).replace('Get-MailboxFolderPermission -Identity *** Email address is removed for privacy *** :\calendar','').replace('Thanks','').replace('BenHyland','').replace('Thank you','').replace('Regards','')
                
        text = re.sub(r'\[[0-9]*\]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        st.subheader('Original text: ')
        st.write(text)
        content = text.strip().replace("\n","")
        summary = summarization(content)[0]['summary_text']
        
        st.subheader('Summarised text: ')
        st.write(summary)

        sentence = summary.count('.') + summary.count('!') + summary.count(';') + summary.count(':') + summary.count('?')
        words = len(summary.split())
        syllable = 0
        for word in summary.split():
            for vowel in ['a','e','i','o','u']:
                syllable += word.count(vowel)
            for ending in ['es','ed','e']:
                if word.endswith(ending):
                    syllable -= 1
            if word.endswith('le'):
                syllable += 1
        G = round((0.39*words)/sentence+ (11.8*syllable)/words-15.59)
        if G >= 0 and G <= 30:
            st.write('The Readability level is College')
        elif G >= 50 and G <= 60:
            st.write('The Readability level is High School')
        elif G >= 90 and G <= 100:
            st.write('The Readability level is fourth grade')


    if textfield123 and no_of_sentences and st.button('Summarize Text'):
        if not str(no_of_sentences).isdigit():
            st.write("Use it again. Error occured summarizing article.")
        else:
            textfunc_torch()
    if video_id and no_of_sentences and st.button('Summarize Youtube video'):
        if not str(no_of_sentences).isdigit():
            st.write("Use it again. Error occured summarizing article.")
        else:
            textforYT()



############################### EXTRACTIVE ####################################

if types_summ=="Extractive":


    url = st.text_input('\nEnter URL of news article from thehindu.com: ')

    #wikiurl = st.text_input('\nEnter URL of news article from Wikipedia.com: ')
    video_id = st.text_input("\nEnter the Youtube Video Id:")
    # video_id = "Na8vHaCLwKc" 
    toolbox = st.text_input('\nEnter URL of any article from Spiceworks.com')
    textfield123 = st.text_area('\nEnter article or paragraph you want to summarize ')
    pdf_file = st.file_uploader("Upload a PDF or Text file", type=["txt", "pdf"])
    no_of_sentences = st.number_input('Choose the no. of sentences in the summary', min_value = 1)


    #pdf_file = file_selector()
    st.write('You selected `%s`' % pdf_file)

    if pdf_file is not None:

        if no_of_sentences and st.button('Summarize the file'):
            pdf_file = pdf_file.read()
            # To convert to a string based IO:
            stringio = StringIO(pdf_file)
            # To read file as string:
            text = stringio.read()
            text = re.sub(r'\[[0-9]*\]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            st.subheader('Original text: ')
            st.write(text)

            content = text
            content = sanitize_input(content)

            sent_tokens, word_tokens = tokenize_content(content)
            sent_ranks = score_tokens(sent_tokens, word_tokens)
            summary = summarize2(sent_ranks, sent_tokens, no_of_sentences)
            #st.write()
            
            st.subheader('Summarised text: ')
            st.write(summary)
            

            sentence = summary.count('.') + summary.count('!') + summary.count(';') + summary.count(':') + summary.count('?')
            words = len(summary.split())
            syllable = 0
            for word in summary.split():
                for vowel in ['a','e','i','o','u']:
                    syllable += word.count(vowel)
                for ending in ['es','ed','e']:
                    if word.endswith(ending):
                        syllable -= 1
                if word.endswith('le'):
                    syllable += 1
            G = round((0.39*words)/sentence+ (11.8*syllable)/words-15.59)
            if G >= 0 and G <= 30:
                st.write('The Readability level is College')
            elif G >= 50 and G <= 60:
                st.write('The Readability level is High School')
            elif G >= 90 and G <= 100:
                st.write('The Readability level is fourth grade')

    if url and no_of_sentences and st.button('Summarize Hindu Article'):
        text = ""
        
        r=requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser') 
        content = soup.find('div', attrs = {'id' : re.compile('content-body-14269002-*')})
        
        for p in content.findChildren("p", recursive = 'False'):
            text+=p.text+" "
                
        text = re.sub(r'\[[0-9]*\]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        st.subheader('Original text: ')
        st.write(text)
        
        tokens = tokenizer(text)
        sents = sent_tokenizer(text)
        word_counts = count_words(tokens)
        freq_dist = word_freq_distribution(word_counts)
        sent_scores = score_sentences(sents, freq_dist)
        summary, summary_sent_scores = summarize(sent_scores, no_of_sentences)
        
        st.subheader('Summarised text: ')
        st.write(summary)

        sentence = summary.count('.') + summary.count('!') + summary.count(';') + summary.count(':') + summary.count('?')
        words = len(summary.split())
        syllable = 0
        for word in summary.split():
            for vowel in ['a','e','i','o','u']:
                syllable += word.count(vowel)
            for ending in ['es','ed','e']:
                if word.endswith(ending):
                    syllable -= 1
            if word.endswith('le'):
                syllable += 1
        G = round((0.39*words)/sentence+ (11.8*syllable)/words-15.59)
        if G >= 0 and G <= 30:
            st.write('The Readability level is College')
        elif G >= 50 and G <= 60:
            st.write('The Readability level is High School')
        elif G >= 90 and G <= 100:
            st.write('The Readability level is fourth grade')
        
        subh = 'Summary sentence score for the top ' + str(no_of_sentences) + ' sentences: '

        st.subheader(subh)
        
        data = []

        for score in summary_sent_scores: 
            data.append([score[1], score[0]])
            
        df = pd.DataFrame(data, columns = ['Sentence', 'Score'])

        st.table(df)


    if toolbox and no_of_sentences and st.button('Summarize Spiceworks Article'):
        text = ""
        page = requests.get(toolbox)
        tree = html.fromstring(page.content)
        # for p in content.findChildren("p", recursive = 'False'):
        #     text+=p.text+" "
        text = tree.xpath('//*[@id="root_post"]/p/text()')
        text = ' '.join(text).replace('Get-MailboxFolderPermission -Identity *** Email address is removed for privacy *** :\calendar','').replace('Thanks','').replace('BenHyland','').replace('Thank you','').replace('Regards','')
                
        text = re.sub(r'\[[0-9]*\]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        st.subheader('Original text: ')
        st.write(text)
        
        tokens = tokenizer(text)
        sents = sent_tokenizer(text)
        word_counts = count_words(tokens)
        freq_dist = word_freq_distribution(word_counts)
        sent_scores = score_sentences(sents, freq_dist)
        summary, summary_sent_scores = summarize(sent_scores, no_of_sentences)
        
        st.subheader('Summarised text: ')
        st.write(summary)
        
        subh = 'Summary sentence score for the top ' + str(no_of_sentences) + ' sentences: '

        st.subheader(subh)
        
        data = []

        for score in summary_sent_scores: 
            data.append([score[1], score[0]])
            
        df = pd.DataFrame(data, columns = ['Sentence', 'Score'])

        st.table(df)

        sentence = summary.count('.') + summary.count('!') + summary.count(';') + summary.count(':') + summary.count('?')
        words = len(summary.split())
        syllable = 0
        for word in summary.split():
            for vowel in ['a','e','i','o','u']:
                syllable += word.count(vowel)
            for ending in ['es','ed','e']:
                if word.endswith(ending):
                    syllable -= 1
            if word.endswith('le'):
                syllable += 1
        G = round((0.39*words)/sentence+ (11.8*syllable)/words-15.59)
        if G >= 0 and G <= 30:
            st.write('The Readability level is College')
        elif G >= 50 and G <= 60:
            st.write('The Readability level is High School')
        elif G >= 90 and G <= 100:
            st.write('The Readability level is fourth grade')


    if textfield123 and no_of_sentences and st.button('Summarize Text'):
        if not str(no_of_sentences).isdigit():
            st.write("Use it again. Error occured summarizing article.")
        else:
            textfunc()
    if video_id and no_of_sentences and st.button('Summarize Youtube video'):
    	if not str(no_of_sentences).isdigit():
    		st.write("Use it again. Error occured summarizing article.")
    	else:
    		textforYT()
