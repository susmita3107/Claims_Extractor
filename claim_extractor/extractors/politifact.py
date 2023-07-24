from typing import List
import dateparser
from bs4 import BeautifulSoup
from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.extractors.utils import clean_string


class PolitifactFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        """
        Constructor for the PolitifactFactCheckingSiteExtractor class.

        Parameters:
            configuration (Configuration): The configuration object containing settings for the extractor.
        """
        super().__init__(configuration)

    def get_listing_page_formatters(self):
        """
        Returns a list of lambda functions that format URLs for listing pages.

        Returns:
            List[Callable]: A list of lambda functions for formatting URLs.
        """
        return [lambda page_number: f"https://www.politifact.com/factchecks/?page={page_number}"]

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        """
        Extracts fact-check URLs from the parsed listing page.

        Parameters:
            parsed_listing_page (BeautifulSoup): The parsed HTML content of the listing page.

        Returns:
            List[str]: A list of fact-check URLs.
        """
        urls = list()
        links = parsed_listing_page.findAll("article", {"class": "m-statement"})
        for link in links:
            link_quote = link.find("div", {"class": "m-statement__quote"})
            link = link_quote.find('a', href=True)
            url = "https://www.politifact.com" + str(link['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)
        return urls

    def translate_rating_value(self, initial_rating_value: str) -> str:
        """
        Translates the initial rating value to its corresponding label.

        Parameters:
            initial_rating_value (str): The initial rating value to be translated.

        Returns:
            str: The translated rating label.
        """
        dictionary = {
            "true": "True",
            "mostly-true": "Mostly True",
            "half-true": "Half False",
            "barely-true": "Mostly False",
            "false": "False",
            "pants-fire": "Pants on Fire"
        }

        if initial_rating_value in dictionary:
            return dictionary[initial_rating_value]
        else:
            return ""

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        """
        Extracts claim and review details from the parsed claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.
            url (str): The URL of the claim review page.

        Returns:
            List[Claim]: A list containing the extracted claim and review details as Claim objects.
        """
        claim = Claim()

       
        claim_review_version = self.get_version(parsed_claim_review_page)

        # url of factcheck
        claim.set_url(url)

        # source organization
        claim.set_source("politifact")

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
        date_claim_review_pub = self.extract_date_claim_review_pub(parsed_claim_review_page, claim_review_version)
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
        date_claim_pub = self.extract_date_claim_pub(parsed_claim_review_page)
        claim.set_claim_date(date_claim_pub)

        # author of claim
        claim_author = self.extract_claim_author(parsed_claim_review_page)
        claim.set_claim_author(claim_author)

        return [claim]

    def get_version(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Determines the version of the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The version of the claim review page ("v1", "v2", or "could not determine version").
        """
        def _is_v1(page_html: str) -> bool:
            return all(['m-author__date' in page_html])

        def _is_v2(page_html: str) -> bool:
            return all(['m-author__date' not in page_html])

        version_checks = {
            "v1": _is_v1,
            "v2": _is_v2
        }

        page_html = str(parsed_claim_review_page)

        for version, check in version_checks.items():
            if check(page_html):
                return version

        return "could not determine version"

    def extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the title of the claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The title of the claim review.
        """
        try:
            title_element = parsed_claim_review_page.find("h2", {"class": "c-title"})
            title = title_element.text.strip()
            title = clean_string(title)

            if title == "":
                title = "INFO: No claim review title found"

        except:
            title = "ERROR: Error when extracting claim review title"

        return title

    def extract_claim_review_author(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the author of the claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The author of the claim review.
        """
        try:
            review_author_element = parsed_claim_review_page.find("div", {"class": "m-author__content copy-xs u-color--chateau"})
            review_author_element = review_author_element.find("a")
            review_author = review_author_element.text
            review_author = clean_string(review_author)
            if review_author == "":
                review_author = "INFO: No claim review author found"

        except:
            review_author = "ERROR: Error when extracting claim review author"

        return review_author

    def extract_claim_review_author_url(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the URL of the author of the claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The URL of the author of the claim review.
        """
        try:
            review_author_element = parsed_claim_review_page.find("div", {"class": "m-author__content copy-xs u-color--chateau"})
            review_author_element = review_author_element.find("a")
            review_author_url = "https://www.politifact.com" + review_author_element['href']
            if review_author_url == "":
                review_author_url = "INFO: No claim review author url found"

        except:
            review_author_url = "ERROR: Error when extracting claim review author url"

        return review_author_url

    def extract_date_claim_review_pub(self, parsed_claim_review_page: BeautifulSoup, version: str) -> str:
        """
        Extracts the publishing date of the claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.
            version (str): The version of the claim review page ("v1" or "v2").

        Returns:
            str: The publishing date of the claim review in the format "YYYY-MM-DD".
        """
        def _extract_date_claim_review_pub_v1(parsed_claim_review_page):
            date_claim_review_pub_element = parsed_claim_review_page.find("span", {"class": "m-author__date"})
            date_claim_review_pub = date_claim_review_pub_element.get_text(strip=True)
            date_claim_review_pub = dateparser.parse(date_claim_review_pub).strftime("%Y-%m-%d")
            return date_claim_review_pub

        def _extract_date_claim_review_pub_v2(parsed_claim_review_page):
            meta_element = parsed_claim_review_page.find("meta", {"property": "og:url"})
            url = meta_element['content']
            date_claim_review_pub = "-".join(url.removeprefix("https://www.politifact.com/factchecks/").split("/")[:3])
            date_claim_review_pub = dateparser.parse(date_claim_review_pub).strftime("%Y-%m-%d")
            return date_claim_review_pub

        try:
            if version == "v1":
                date_claim_review_pub = _extract_date_claim_review_pub_v1(parsed_claim_review_page)
            elif version == "v2":
                date_claim_review_pub = _extract_date_claim_review_pub_v2(parsed_claim_review_page)
            else:
                date_claim_review_pub = f"ERROR: Don't know how to extract claim review date"

            if date_claim_review_pub == "":
                date_claim_review_pub = f"INFO: no claim review date found with {version}"

        except:
            date_claim_review_pub = f"ERROR: Error when extracting claim review date with {version}"

        return date_claim_review_pub

    def extract_date_claim_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the date of the claim.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The date of the claim in the format "YYYY-MM-DD".
        """
        try:
            date_claim_pub_element = parsed_claim_review_page.find("div", {"class": "m-statement__meta"})
            date_claim_pub = " ".join(date_claim_pub_element.text.split()).strip()
            if "stated" in date_claim_pub:
                date_claim_pub = date_claim_pub.split("stated")[1]
            if "on" in date_claim_pub:
                date_claim_pub = date_claim_pub.split(" on ")[1]
            if "in" in date_claim_pub:
                date_claim_pub = date_claim_pub.split(" in ")[0]
            date_claim_pub = dateparser.parse(date_claim_pub).strftime("%Y-%m-%d")

            if date_claim_pub == "":
                date_claim_pub = "INFO: No claim date found"

        except:
            date_claim_pub = "ERROR: Error when extracting claim date"

        return date_claim_pub

    def extract_claim_author(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the author of the claim.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The author of the claim.
        """
        try:
            claim_author = parsed_claim_review_page.find("a", {"class": "m-statement__name"})
            claim_author = claim_author.get_text(strip=True)
            claim_author = clean_string(claim_author)
            if claim_author == "":
                claim_author = "INFO: No claim author found"

        except:
            claim_author = "ERROR: Error when extracting claim author"

        return claim_author

    def extract_claim(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the claim text from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The claim text.
        """
        try:
            claim_text_div = parsed_claim_review_page.find("div", {"class": "m-statement__quote"})
            claim_text = clean_string(claim_text_div.text)
            if claim_text == "":
                claim_text = "INFO: no claim found"

        except:
            claim_text = "ERROR: Error when extracting claim"

        return claim_text

    def extract_rating(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the rating of the claim from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The rating of the claim.
        """
        try:
            statement_body = parsed_claim_review_page.find("div", {"class", "m-statement__body"})
            statement_detail = statement_body.find("div", {"class", "c-image"})
            statement_detail_image = statement_detail.find("picture")
            statement_detail_image_alt = statement_detail_image.find("img", {"class", "c-image__original"})
            if self.translate_rating_value(statement_detail_image_alt['alt']) != "":
                rating = self.translate_rating_value(statement_detail_image_alt['alt'])
            else:
                rating = statement_detail_image_alt['alt']
                rating = clean_string(rating)
            if rating == "":
                rating = "INFO: no rating found"

        except:
            rating = "ERROR: Error when extracting rating"

        return rating

    def extract_claim_review_body(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the body/description of the claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The body/description of the claim review.
        """
        try:
            article_content = parsed_claim_review_page.find('article', {"class": 'm-textblock'})

            # remove all script tags from article content
            for script in article_content.find_all("script", recursive=True):
                script.decompose()

            # remove all style tags from article content
            for style in article_content.find_all("style", recursive=True):
                style.decompose()

            # remove all div .factbox tags from article content
            for div in article_content.find_all("div", {'class': 'factbox'}, recursive=True):
                div.decompose()

            # remove all section .o-pick tags from article content
            for section in article_content.find_all("section", {'class': 'o-pick'}, recursive=True):
                section.decompose()

            body_description = article_content.get_text(separator=' ')
            body_description = clean_string(body_description)

            if body_description == "":
                body_description = "INFO: no body found"

        except:
            body_description = "ERROR: Error when extracting body"

        return body_description

    def extract_tags(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the tags and categories associated with the claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: A string containing tags and categories separated by ":-:".
        """
        try:
            tag_list = parsed_claim_review_page.find("ul", {"class", "m-list"})
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
        Extracts the referred links from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: A string containing referred links separated by ":-:".
        """
        try:
            referred_links = []

            article = parsed_claim_review_page.find("article", {"class": "m-textblock"})

            for link in article.find_all('a', href=True):
                try:
                    if "http" in link['href']:
                        referred_links.append(link['href'])
                    else:
                        referred_links.append("https://www.politifact.com" + link['href'])
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
