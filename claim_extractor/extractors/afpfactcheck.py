from typing import List
import dateparser
from bs4 import BeautifulSoup
from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.extractors.utils import clean_string
import re
import json

class AfpfactcheckFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    """
    A web scraper to extract fact-checking information from the "AFP Fact Check" website.

    Parameters:
        configuration (Configuration): Configuration options for the web scraper.

    Methods:
        get_listing_page_formatters(): Returns a list of lambda functions for formatting URLs of different listing pages.
        extract_urls(parsed_listing_page: BeautifulSoup) -> List[str]: Extracts URLs of fact-checking articles from a parsed listing page.
        extract_claim_and_review(parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]: Extracts claim and review details from a parsed fact-checking article page.
        extract_title(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the title of a fact-checking article.
        extract_claim_review_author(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the author(s) of a fact-checking article.
        extract_claim_review_author_url(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the URL(s) of the author(s) of a fact-checking article.
        extract_date_claim_review_pub(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the publishing date of a fact-checking article.
        extract_date_claim_pub(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the date of the claim in a fact-checking article.
        extract_claim_author(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the author of the claim in a fact-checking article.
        extract_claim(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the claim text from a fact-checking article.
        extract_rating(parsed_claim_review_page: BeautifulSoup) -> Tuple[str, str, str, str]: Extracts the rating (verdict) from a fact-checking article.
        extract_claim_review_body(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the body content of a fact-checking article.
        extract_tags(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the tags/categories of a fact-checking article.
        extract_referred_links(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the referred links in a fact-checking article.

    """

    def __init__(self, configuration: Configuration):
        """
        Initialize the FullfactFactCheckingSiteExtractor.

        Parameters:
            configuration (Configuration, optional): Configuration options for the web scraper.
            ignore_urls (List[str], optional): List of URLs to ignore during scraping.
            headers (dict, optional): HTTP headers to be used in the web requests.
            language (str, optional): Language code for the content to be scraped (default: 'eng').
        """
        super().__init__(configuration)

    def get_listing_page_formatters(self):
        """
        Returns a list of lambda functions used to format URLs of different listing pages.

        Returns:
            List[Callable]: List of lambda functions for formatting URLs of different listing pages.
        """
        return [lambda page_number: f"https://factcheck.afp.com/list?page={page_number}"]

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        """
        Extracts URLs of fact-checking articles from a parsed listing page.

        Parameters:
            parsed_listing_page (BeautifulSoup): Parsed HTML of the listing page.

        Returns:
            List[str]: List of URLs of fact-checking articles.
        """
        urls = list()

        cards = parsed_listing_page.findAll('div', attrs={'class': 'card'})
        for card in cards:
            url = card.find("a")['href']
            urls.append("https://factcheck.afp.com" + url)

        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        """
        Extracts claim and review details from a parsed fact-checking article page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.
            url (str): URL of the fact-checking article.

        Returns:
            List[Claim]: List of Claim objects containing extracted information.
        """
        claim = Claim()

        """
        import requests
        parsed_claim_review_page = BeautifulSoup(requests.get("https://factcheck.afp.com/no-ronaldo-did-not-donate-15-million-palestinians-gaza-ramadan").text, "lxml")
        parsed_claim_review_page = BeautifulSoup(requests.get("https://factcheck.afp.com/http%253A%252F%252Fdoc.afp.com%252F9UL98F-1").text, "lxml")
        
        """

        # url of factcheck
        claim.set_url(url)

        # source organization
        claim.set_source("factcheck_afp")

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
        rating, best_rating, worst_rating, rating_value = self.extract_rating(parsed_claim_review_page)
        claim.set_rating(rating)
        claim.set_best_rating(best_rating)
        claim.set_worst_rating(worst_rating)
        claim.set_rating_value(rating_value)

        # date of claim
        date_claim_pub = self.extract_date_claim_pub(parsed_claim_review_page)
        claim.set_claim_date(date_claim_pub)

        # author of claim
        claim_author = self.extract_claim_author(parsed_claim_review_page)
        claim.set_claim_author(claim_author)

        return [claim]

    def extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the title of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The title of the fact-checking article.
        """
        try:
            title = ""

            data = parsed_claim_review_page.find(string=re.compile("schema.org"))
            data = json.loads(str(data))
            node_zero = data['@graph'][0]

            if "name" in node_zero:
                title = node_zero['name']
                title = clean_string(title)

            if title == "":
                title = "INFO: No claim review title found"

        except:
            title = "ERROR: Error when extracting claim review title"

        return title

    def extract_claim_review_author(self, parsed_claim_review_page: BeautifulSoup) -> str: # actually more found in html
        """
        Extracts the author of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The author of the fact-checking article.
        """
        try:
            review_author_span = parsed_claim_review_page.find('span', {"class": "meta-author"})
            review_author = ":-:".join([clean_string(author) for author in review_author_span.text.split(",")])

            if review_author == "":
                review_author = "INFO: No claim review author found"

        except:
            review_author = "ERROR: Error when extracting claim review author"

        return review_author

    def extract_claim_review_author_url(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the URL(s) of the author(s) of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The URL(s) of the author(s) of the fact-checking article, separated by ":-:".
        """
        try:
            review_author_span = parsed_claim_review_page.find('span', {"class": "meta-author"})
            review_author_urls = []
            for review_author_url in review_author_span.find_all("a", href=True):
                review_author_urls.append("https://factcheck.afp.com" + review_author_url['href'])

            review_author_url = ":-:".join(review_author_urls)

            if review_author_url == "":
                review_author_url = "INFO: No claim review author url found"

        except:
            review_author_url = "ERROR: Error when extracting claim review author url"

        return review_author_url

    def extract_date_claim_review_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the publishing date of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The publishing date of the fact-checking article in the format "YYYY-MM-DD".
        """
        try:
            date_claim_review_pub = ""

            data = parsed_claim_review_page.find(string=re.compile("schema.org"))
            data = json.loads(str(data))
            node_zero = data['@graph'][0]

            if "datePublished" in node_zero:
                date_claim_review_pub = node_zero['datePublished']
                date_claim_review_pub = date_claim_review_pub.split(' ')[0]
                date_claim_review_pub = dateparser.parse(date_claim_review_pub).strftime("%Y-%m-%d")

            if date_claim_review_pub == "":
                date_claim_review_pub = "INFO: no claim review date found"

        except:
            date_claim_review_pub = "ERROR: Error when extracting claim review date"

        return date_claim_review_pub

    def extract_date_claim_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the date of the claim in a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The date of the claim in the fact-checking article in the format "YYYY-MM-DD".
        """
        try:
            date_claim_pub = ""

            data = parsed_claim_review_page.find(string=re.compile("schema.org"))
            data = json.loads(str(data))
            node_zero = data['@graph'][0]

            if "itemReviewed" in node_zero:
                itemReviewed = node_zero['itemReviewed']
                if "datePublished" in itemReviewed:
                    date_claim_pub_element = itemReviewed['datePublished']
                    if date_claim_pub_element != "":
                        date_claim_pub = dateparser.parse(date_claim_pub_element).strftime("%Y-%m-%d")

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
        """
        Extracts the claim text from a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            List[str]: List of claim texts extracted from the fact-checking article.
        """
        try:
            claim_text = ""
            data = parsed_claim_review_page.find(string=re.compile("schema.org"))
            data = json.loads(str(data))
            node_zero = data['@graph'][0]

            if "claimReviewed" in node_zero:
                claim_text = node_zero['claimReviewed']
                claim_text = clean_string(claim_text)

            if claim_text == "":
                claim_text = "INFO: no claim found"

        except:
            claim_text = "ERROR: Error when extracting claim"

        return claim_text

    def extract_rating(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the rating (verdict) from a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            List[str]: List of ratings (verdicts) extracted from the fact-checking article.
        """
        try:
            rating = ""
            best_rating = ""
            worst_rating = ""
            rating_value = ""
            data = parsed_claim_review_page.find(string=re.compile("schema.org"))
            data = json.loads(str(data))
            node_zero = data['@graph'][0]

            if "reviewRating" in node_zero:
                rating_node = node_zero['reviewRating']
                if "alternateName" in rating_node:
                    rating = rating_node['alternateName']
                    rating = rating.title()
                    rating = clean_string(rating)

                if "bestRating" in rating_node:
                    best_rating = rating_node['bestRating']
                if "worstRating" in rating_node:
                    worst_rating = rating_node['worstRating']
                if "ratingValue" in rating_node:
                    rating_value = rating_node['ratingValue']

                if rating == "" and rating_value != "":
                    rating_value2rating = {
                        "1": "False"
                    }
                    if rating_value in rating_value2rating:
                        rating = rating_value2rating[rating_value]

            if rating == "":
                rating = "INFO: no rating found"
            if best_rating == "":
                best_rating = "INFO: no best rating found"
            if worst_rating == "":
                worst_rating = "INFO: no worst rating found"
            if rating_value == "":
                rating_value = "INFO: no rating value found"

        except:
            rating = "ERROR: Error when extracting rating"
            best_rating = "ERROR: Error when extracting best rating"
            worst_rating = "ERROR: Error when extracting worst rating"
            rating_value = "ERROR: Error when extracting rating value"

        return rating, best_rating, worst_rating, rating_value

    def extract_claim_review_body(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the body content of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The body content of the fact-checking article.
        """
        try:
            article_content = parsed_claim_review_page.find('div', {'class': 'article-entry clearfix'})

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
        """
        Extracts the tags/categories of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The tags/categories of the fact-checking article, separated by ":-:".
        """
        try:
            tag_list = parsed_claim_review_page.find("div", {"class", "tags"})
            tag_elements = tag_list.select('a')
            tags = [clean_string(tag_element.get_text(strip=True)) for tag_element in tag_elements]
            tags = ":-:".join(tags)

            if tags == "":
                tags = "INFO: No tags found"

        except:
            tags = "ERROR: Error when extracting tags"

        return tags

    def extract_referred_links(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the referred links in a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The referred links in the fact-checking article, separated by ":-:".
        """
        try:
            referred_links = []

            article = parsed_claim_review_page.find('div', {'class': 'article-entry clearfix'})

            for link in article.find_all('a', href=True):
                try:
                    link = link['href']
                    if "http" in link:
                        referred_links.append(link)
                    else:
                        referred_links.append("https://factcheck.afp.com" + link['href'])
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
