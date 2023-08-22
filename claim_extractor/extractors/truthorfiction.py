from typing import List
import dateparser
from bs4 import BeautifulSoup
from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.extractors.utils import clean_string
import re
import json
import requests

class TruthorfictionFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        """
        Initializes the TruthorfictionFactCheckingSiteExtractor class with the provided configuration.

        Parameters:
        configuration (Configuration): An instance of the Configuration class containing relevant settings.
        """
        super().__init__(configuration)

    def get_listing_page_formatters(self):
        """
        Returns a list of lambda functions that generate the URL format for listing pages based on page numbers.

        Returns:
        List[Callable]: A list of lambda functions to generate listing page URLs.
        """
        return [lambda page_number: f"https://www.truthorfiction.com/category/fact-checks/page/{page_number}"]

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        """
        Extracts fact-checking URLs from a parsed listing page.

        Parameters:
        parsed_listing_page (BeautifulSoup): A BeautifulSoup object representing the parsed listing page.

        Returns:
        List[str]: A list containing the extracted fact-checking URLs.
        """
        urls = list()

        listing_container = parsed_listing_page.find_all("article", {"class": "post"})
        for article in listing_container:
            anchor = article.find("a")
            url = str(anchor['href'])
            urls.append(url)

        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        """
        Extracts claim and review information from a parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.
        url (str): The URL of the claim review page.

        Returns:
        List[Claim]: A list containing the extracted Claim object(s).
        """
        claim = Claim()

        """
        import requests
        parsed_claim_review_page = BeautifulSoup(requests.get("https://www.truthorfiction.com/some-one-dreamed-the-other-night-that-he-was-living-in-the-year-2023-eggs-had-gone-up-to-10-a-dozen/").text, "lxml")
        parsed_claim_review_page = BeautifulSoup(requests.get("https://www.truthorfiction.com/13000-marines-apply-white-house-detail/").text, "lxml")
        parsed_claim_review_page = BeautifulSoup(requests.get("https://www.truthorfiction.com/muslim-brotherhood-in-white-house-050813/").text, "lxml")
        
        
        

        """

        # url of factcheck
        claim.set_url(url)

        # source organization
        claim.set_source("truthorfiction")

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

        # date of claim
        #date_claim_pub = self.extract_date_claim_pub(parsed_claim_review_page)
        #claim.set_claim_date(date_claim_pub)

        # author of claim
        #claim_author = self.extract_claim_author(parsed_claim_review_page)
        #claim.set_claim_author(claim_author)

        return [claim]

    def extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the title of the claim review from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted title of the claim review.
        """
        try:
            title_element = parsed_claim_review_page.find("meta", {"property": "og:title"})
            title = title_element['content']
            title = clean_string(title)

            if title == "":
                title = "INFO: No claim review title found"

        except:
            title = "ERROR: Error when extracting claim review title"

        return title

    def extract_claim_review_author(self, parsed_claim_review_page: BeautifulSoup) -> str: # actually more found in html
        """
        Extracts the author of the claim review from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted author of the claim review.
        """
        try:
            review_author_element = parsed_claim_review_page.find('meta', {"name": "author"})
            review_author = review_author_element['content']
            review_author = clean_string(review_author)

            if review_author == "":
                review_author = "INFO: No claim review author found"

        except:
            review_author = "ERROR: Error when extracting claim review author"

        return review_author

    def extract_claim_review_author_url(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the URL of the author of the claim review from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted URL of the author of the claim review.
        """
        try:
            review_author_url_element = parsed_claim_review_page.find('a', {"class": "url fn n"})
            review_author_url = review_author_url_element['href']

            if review_author_url == "":
                review_author_url = "INFO: No claim review author url found"

        except:
            review_author_url = "ERROR: Error when extracting claim review author url"

        return review_author_url

    def extract_date_claim_review_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the publishing date of the claim review from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted publishing date of the claim review in the format "YYYY-MM-DD".
        """
        try:
            date_claim_review_pub_element = parsed_claim_review_page.find("meta", {"property": "article:published_time"})
            date_claim_review_pub = date_claim_review_pub_element['content']
            date_claim_review_pub = date_claim_review_pub.split("T")[0]
            date_claim_review_pub = dateparser.parse(date_claim_review_pub).strftime("%Y-%m-%d")

            if date_claim_review_pub == "":
                date_claim_review_pub = "INFO: no claim review date found"

        except:
            date_claim_review_pub = "ERROR: Error when extracting claim review date"

        return date_claim_review_pub

    def extract_date_claim_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the publishing date of the claim from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted publishing date of the claim in the format "YYYY-MM-DD".
        """
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
        """
        Extracts the author of the claim from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted author of the claim.
        """
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
        """
        Extracts the claim text from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted claim text.
        """
        def _extract_claim_v1(parsed_claim_review_page: BeautifulSoup) -> str:
            claim_element = parsed_claim_review_page.find("div", {"class", "claim-description"})
            claim_text = claim_element.get_text(separator=' ')
            claim_text = clean_string(claim_text)
            return claim_text

        def _extract_claim_v2(parsed_claim_review_page: BeautifulSoup) -> str:
            article_content = parsed_claim_review_page.find("main", {"id": "main"})
            article_h1 = article_content.find("h1")
            article_headline = article_h1.get_text(separator=' ')
            article_headline = article_headline.replace("–", "-")
            if "-" in article_headline:
                claim_text = " ".join(article_headline.split("-")[:-1])
                claim_text = clean_string(claim_text)
            else:
                claim_text = ""
            return claim_text

        for func in [_extract_claim_v1, _extract_claim_v2]:
            try:
                claim_text = func(parsed_claim_review_page)
                if claim_text != "":
                    break
            except Exception as e:
                continue

        if claim_text == "":
            claim_text = "INFO: no claim found"

        return claim_text

    def extract_rating(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the rating of the claim from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted rating of the claim.
        """
        def _extract_rating_v1(parsed_claim_review_page: BeautifulSoup) -> str:
            rating_element = parsed_claim_review_page.find("div", {"class", "rating-description"})
            rating = rating_element.get_text(separator=' ')
            rating = clean_string(rating)
            return rating

        def _extract_rating_v2(parsed_claim_review_page: BeautifulSoup) -> str:
            article_content = parsed_claim_review_page.find("main", {"id": "main"})
            article_h1 = article_content.find("h1")
            article_headline = article_h1.get_text(separator=' ')
            article_headline = article_headline.replace("–", "-")
            if "-" in article_headline:
                rating = article_headline.split("-")[-1]
                rating = rating.replace('!', '')
                rating = clean_string(rating)

            else:
                rating = ""
            return rating

        for func in [_extract_rating_v1, _extract_rating_v2]:
            try:
                rating = func(parsed_claim_review_page)
                if rating != "":
                    break
            except Exception as e:
                continue

        if rating == "":
            rating = "INFO: no rating found"

        return rating

    def extract_claim_review_body(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the body description of the claim review from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted body description of the claim review.
        """
        try:
            article_content = parsed_claim_review_page.find("main", {"id": "main"})

            for comment_element in article_content.find_all('div', {'id': 'emote_com'}):
                comment_element.decompose()

            for ad_element in article_content.find_all('span', {'class': 'ezoic-ad'}):
                ad_element.decompose()

            for button_element in article_content.find_all('button'):
                button_element.decompose()

            for nav_element in article_content.find_all('nav'):
                nav_element.decompose()

            for entry_meta_element in article_content.find_all('div', {'class': 'entry-meta'}):
                entry_meta_element.decompose()

            body_description = article_content.get_text(separator=' ')
            body_description = clean_string(body_description)

            if body_description == "":
                body_description = "INFO: no body found"

        except:
            body_description = "ERROR: Error when extracting body"

        return body_description

    def extract_tags(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the tags of the claim review from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted tags of the claim review, separated by ":-:".
        """
        try:
            tag_list = parsed_claim_review_page.find("span", {"class", "tags-links"})
            tag_elements = tag_list.select('a')
            tags = [clean_string(tag_element.get_text(strip=True)) for tag_element in tag_elements]
            tags = ":-:".join(tags)

            cat_list = parsed_claim_review_page.find("span", {"class", "cat-links"})
            cat_elements = cat_list.select('a')
            cats = [clean_string(cat_element.get_text(strip=True)) for cat_element in cat_elements]
            cats = ":-:".join(cats)

            tags = tags + cats

            if tags == "":
                tags = "INFO: No tags found"

        except:
            tags = "ERROR: Error when extracting tags"

        return tags

    def extract_referred_links(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the referred links in the claim review from the parsed claim review page.

        Parameters:
        parsed_claim_review_page (BeautifulSoup): A BeautifulSoup object representing the parsed claim review page.

        Returns:
        str: The extracted referred links in the claim review, separated by ":-:".
        """
        try:
            referred_links = []

            article_content = parsed_claim_review_page.find("main", {"id": "main"})

            for comment_element in article_content.find_all('div', {'id': 'emote_com'}):
                comment_element.decompose()

            for ad_element in article_content.find_all('span', {'class': 'ezoic-ad'}):
                ad_element.decompose()

            for button_element in article_content.find_all('button'):
                button_element.decompose()

            for nav_element in article_content.find_all('nav'):
                nav_element.decompose()

            for link in article_content.find_all('a', href=True):
                try:
                    link = link['href']
                    if "http" in link:
                        referred_links.append(link)
                    else:
                        referred_links.append("https://africacheck.org/" + link['href'])
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
