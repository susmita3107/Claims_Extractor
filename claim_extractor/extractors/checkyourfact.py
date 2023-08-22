from typing import List
import dateparser
from bs4 import BeautifulSoup

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.extractors.utils import clean_string
import re
import json
import requests

class CheckyourfactFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def get_listing_page_formatters(self):
        return [lambda page_number: f"https://checkyourfact.com/page/{page_number}"]

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()

        links = parsed_listing_page.find('articles').findAll('a', href=True)
        for anchor in links:
            url = "https://checkyourfact.com" + str(anchor['href'])
            urls.append(url)

        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()

        """
        import requests
        parsed_claim_review_page = BeautifulSoup(requests.get("https://checkyourfact.com/2023/01/31/fact-check-german-military-tanks-ukraine/").text, "lxml")
        parsed_claim_review_page = BeautifulSoup(requests.get("https://checkyourfact.com/2017/10/23/fact-check-has-the-uranium-one-controversy-been-debunked/").text, "lxml")
        
        
        """

        # url of factcheck
        claim.set_url(url)

        # source organization
        claim.set_source("checkyourfact")

        """
        Claim Review
        """
        # title of claim review
        title = self.extract_title(parsed_claim_review_page)
        claim.set_title(title)

        # author of claim review
        review_author = self.extract_claim_review_author(parsed_claim_review_page)
        claim.set_claim_review_author(review_author)

        # url of author of claim review
        review_author_url = self.extract_claim_review_author_url(parsed_claim_review_page)
        claim.set_claim_review_author_url(review_author_url)

        # publishing date of claim review
        date_claim_review_pub = self.extract_date_claim_review_pub(parsed_claim_review_page)
        claim.set_claim_review_date(date_claim_review_pub)

        # body of claim review
        body_description = self.extract_claim_review_body(parsed_claim_review_page)
        claim.set_body(body_description)

        # tags of claim review
        tags = self.extract_tags(parsed_claim_review_page)
        claim.set_tags(tags)

        # referred links in claim review
        referred_links = self.extract_referred_links(parsed_claim_review_page)
        claim.set_referred_links(referred_links)

        """
        Claim
        """
        # text of claim
        claim_text = self.extract_claim(parsed_claim_review_page)
        claim.set_claim(claim_text)

        # rating of claim
        rating = self.extract_rating(parsed_claim_review_page)
        claim.set_rating(rating)

        return [claim]

    def extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            article_content = parsed_claim_review_page.find('article')
            article_h1 = article_content.find("h1")
            article_headline = article_h1.get_text(separator=' ')
            title = article_headline.replace("FACT CHECK: ", "")
            title = clean_string(title)

            if title == "":
                title = "INFO: No claim review title found"

        except:
            title = "ERROR: Error when extracting claim review title"

        return title

    def extract_claim_review_author(self, parsed_claim_review_page: BeautifulSoup) -> str: # actually more found in html

        def extract_claim_review_author_v1(parsed_claim_review_page: BeautifulSoup) -> str:
            review_author = ""
            for d in parsed_claim_review_page.find_all(string=re.compile("schema.org")):
                if '"@type": "NewsArticle"' in str(d):
                    data = json.loads(str(d))
                    break

            if "author" in data:
                review_author_dict = data['author']
                if "name" in review_author_dict:
                    review_author = review_author_dict['name']
                    review_author = clean_string(review_author)

            return review_author

        def extract_claim_review_author_v2(parsed_claim_review_page: BeautifulSoup) -> str:
            article_content = parsed_claim_review_page.find('article')
            review_author_element = article_content.find('author')
            review_author = review_author_element.text.split("|")[0]
            review_author = review_author.split("\n")[0]
            review_author = clean_string(review_author)

            return review_author

        for func in [extract_claim_review_author_v1, extract_claim_review_author_v2]:
            try:
                review_author = func(parsed_claim_review_page)
                if review_author != "":
                    break
            except Exception as e:
                continue

        if review_author == "":
            review_author = "INFO: No claim review author found"

        return review_author

    def extract_claim_review_author_url(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            article_content = parsed_claim_review_page.find('article')
            review_author_element = article_content.find('author')

            review_author_url = "https://checkyourfact.com/author/" + review_author_element['data-slug']

            if review_author_url == "":
                review_author_url = "INFO: No claim review author url found"

        except:
            review_author_url = "ERROR: Error when extracting claim review author url"

        return review_author_url

    def extract_date_claim_review_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            article_content = parsed_claim_review_page.find('article')
            time_element = article_content.find("time")
            date_claim_review_pub = time_element.text
            date_claim_review_pub = date_claim_review_pub.split(' ')[-1]
            date_claim_review_pub = dateparser.parse(date_claim_review_pub).strftime("%Y-%m-%d")

            if date_claim_review_pub == "":
                date_claim_review_pub = "INFO: no claim review date found"

        except:
            date_claim_review_pub = "ERROR: Error when extracting claim review date"

        return date_claim_review_pub

    def extract_date_claim_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            date_claim_pub = ""

            data = parsed_claim_review_page.find(string=re.compile("schema.org"))
            data = json.loads(str(data))
            node_zero = data['@graph'][0]

            if "itemReviewed" in node_zero:
                itemReviewed = node_zero['itemReviewed']
                if "datePublished" in itemReviewed:
                    date_claim_pub = itemReviewed['datePublished']
                    date_claim_pub = dateparser.parse(date_claim_pub).strftime("%Y-%m-%d")

            if date_claim_pub == "":
                date_claim_pub = "INFO: No claim date found"

        except:
            date_claim_pub = "ERROR: Error when extracting claim date"

        return date_claim_pub

    def extract_claim_author(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            claim_author = ""

            data = parsed_claim_review_page.find(string=re.compile("schema.org"))
            data = json.loads(str(data))
            node_zero = data['@graph'][0]

            if "itemReviewed" in node_zero:
                itemReviewed = node_zero['itemReviewed']
                if 'author' in itemReviewed:
                    author_dict = itemReviewed['author']
                    if 'name' in author_dict:
                        if type(author_dict['name']) is list:
                            claim_author = author_dict['name'][0]
                        else:
                            claim_author = author_dict['name']
                        claim_author = clean_string(claim_author)

            if claim_author == "":
                claim_author = "INFO: No claim author found"

        except:
            claim_author = "ERROR: Error when extracting claim author"

        return claim_author

    def extract_claim(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            article_content = parsed_claim_review_page.find("div", {"id": "ob-read-more-selector"})
            first_p = article_content.find('p')
            claim_text = first_p.get_text(separator=" ")
            claim_text = clean_string(claim_text)

            if claim_text == "":
                claim_text = "INFO: no claim found"

        except:
            claim_text = "ERROR: Error when extracting claim"

        return claim_text

    def extract_rating(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            for script_element in parsed_claim_review_page.find_all('script'):
                script_element.decompose()

            rating_element = parsed_claim_review_page.find(string=re.compile("Verdict:"))
            rating = str(rating_element).split(":")[-1].strip()
            rating = clean_string(rating)
            if rating == "":
                rating = "INFO: no rating found"

        except:
            rating = "ERROR: Error when extracting rating"

        return rating

    def extract_claim_review_body(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            article_content = parsed_claim_review_page.find("div", {"id": "ob-read-more-selector"})

            # remove all script tags from article content
            for script in article_content.find_all("script", recursive=True):
                script.decompose()

            # remove all style tags from article content
            for style in article_content.find_all("style", recursive=True):
                style.decompose()

            body_description = article_content.get_text(separator=' ')
            body_description = clean_string(body_description)

            if body_description == "":
                body_description = "INFO: no body found"

        except:
            body_description = "ERROR: Error when extracting body"

        return body_description

    def extract_tags(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            tags = ""
            data = parsed_claim_review_page.find(string=re.compile("schema.org"))
            data = json.loads(str(data))
            if 'keywords' in data:
                tag_list = data['keywords']
                tags = [clean_string(tag.replace("-", " ")) for tag in tag_list]
                tags = ":-:".join(tags)

            if tags == "":
                tags = "INFO: No tags found"

        except:
            tags = "ERROR: Error when extracting tags"

        return tags

    def extract_referred_links(self, parsed_claim_review_page: BeautifulSoup) -> str:
        try:
            referred_links = []

            article_content = parsed_claim_review_page.find('article')

            for link in article_content.find_all('a', href=True):
                try:
                    link = link['href']

                    if "http" in link:
                        referred_links.append(link)

                    else:
                        referred_links.append("https://checkyourfact.com" + link['href'])
                except Exception:
                    continue

            referred_links = list(set(referred_links))
            referred_links = sorted(referred_links)
            referred_links = ":-:".join(referred_links)

            if referred_links == "":
                referred_links = "INFO: No referred links found"

        except:
            referred_links = "ERROR: Error when extracting referred links"

        return referred_links
