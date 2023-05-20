import json
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import re

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/result', methods=['POST'])
def result():
    paper_urls = request.form.getlist('paper_url')
    papers = []
    for paper_url in paper_urls:
        # add "https://" if it's missing
        if not paper_url.startswith('http://') and not paper_url.startswith('https://'):
            paper_url = 'https://' + paper_url

        page = requests.get(paper_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        title = ''
        pdf_url = ''
        authors = []
        # check if the URL is an arxiv link
        if re.match(r'https?://arxiv\.org/abs/\d{4}\.\d{4,5}', paper_url):
            print('arxiv paper')
            title = soup.find(
                'meta', {'name': 'citation_title'}).get('content')
            pdf_url = soup.find(
                'meta', {'name': 'citation_pdf_url'}).get('content')
            authors = [meta.get('content') for meta in soup.find_all(
                'meta', {'name': 'citation_author'})]
        # check if the URL is an ACM link
        elif re.match(r'https?://dl\.acm\.org/doi/', paper_url):
            print('acm paper')
            title = soup.find('title').text.split('|')[0].strip()
            pdf_url = soup.find(
                'a', {'title': 'View or Download as a PDF file'}).get('href')
            pdf_url = 'https://dl.acm.org' + pdf_url
            authors = [author.get('title') for author in soup.find_all(
                'a', {'class': 'author-name'})]
        elif re.match(r'https?://ieeexplore\.ieee\.org/document/', paper_url):
            print('ieee paper')
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"
            }
            response = requests.get(paper_url, headers=headers)

            match = re.search(
                r'xplGlobal\.document\.metadata=({.*?});', response.text, re.DOTALL)
            if match is None:
                return {"error": "Could not extract paper info"}

            metadata_json = match.group(1)
            metadata = json.loads(metadata_json)

            title = metadata.get('title')
            authors = [author['name']
                       for author in metadata.get('authors', [])]

            pdf_url = 'https://ieeexplore.ieee.org' + \
                metadata.get('pdfUrl', '')
        else:
            print('unknown paper')
            continue

        papers.append({
            'title': title,
            'pdf_url': pdf_url,
            'authors': authors,
        })

    return render_template('result.html', papers=papers)


def parse_ieee(paper_html):
    metadata = re.search(r'xplGlobal\.document\.metadata=(.*?);', paper_html)
    if metadata:
        metadata_json = json.loads(metadata.group(1))

        title = metadata_json.get('title')
        authors = [author.get('name')
                   for author in metadata_json.get('authors', [])]
        pdf_link = "https://ieeexplore.ieee.org" + metadata_json.get('pdfPath')

        return {
            "title": title,
            "authors": authors,
            "pdf_link": pdf_link,
        }

    else:
        return None


if __name__ == "__main__":
    app.run(debug=True)
