import copy
from typing import List
import dateparser
from bs4 import BeautifulSoup, Tag
from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.extractors.utils import clean_string
import re
import json

class AfricacheckFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    """
    AfricacheckFactCheckingSiteExtractor class is responsible for extracting information from fact-checking articles on the Africacheck website.

    This class extends FactCheckingSiteExtractor, and it provides methods for extracting claim details, ratings, authors, tags, and more from fact-checking articles.

    Attributes:
        configuration (Configuration): The configuration object used for customizing the behavior of the extractor.

    Methods:
        __init__(configuration: Configuration): Initializes the AfricacheckFactCheckingSiteExtractor object with the given configuration.

        get_listing_page_formatters(): Returns a list of URL formats for listing pages to scrape multiple pages of fact-checking articles.

        extract_urls(parsed_listing_page: BeautifulSoup) -> List[str]: Extracts the URLs of individual fact-checking articles from a parsed listing page.

        extract_claim_and_review(parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]: Extracts claim and review details from a parsed claim review page.
            This method returns a list of Claim objects, as there might be multiple claims with different ratings or verdicts in a single page.

        extract_title(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the title of the claim review from the parsed claim review page.

        extract_claim_review_author(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the author of the claim review from the parsed claim review page.

        extract_claim_review_author_url(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the URL of the author of the claim review from the parsed claim review page.

        extract_date_claim_review_pub(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the publishing date of the claim review from the parsed claim review page.

        extract_claim(parsed_claim_review_page: BeautifulSoup) -> List[str]: Extracts the text of the claim from the parsed claim review page.
            This method returns a list of claim texts as there might be multiple claims in a single page.

        extract_rating(parsed_claim_review_page: BeautifulSoup) -> Tuple[List[str], List[str], List[str], List[str]]: Extracts the rating of the claim from the parsed claim review page.
            This method returns four lists: ratings, best_ratings, worst_ratings, and rating_values. Each list contains values for each claim in the page.

        extract_claim_review_body(parsed_claim_review_page: BeautifulSoup) -> List[str]: Extracts the body of the claim review from the parsed claim review page.
            This method returns a list of claim review bodies as there might be multiple claims in a single page.

        extract_tags(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the tags of the claim review from the parsed claim review page.

        extract_referred_links(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the referred links from the claim review page.

    """


    def __init__(self, configuration: Configuration):
        """
        Initializes the AfricacheckFactCheckingSiteExtractor object with the given configuration.

        Args:
            configuration (Configuration): The configuration object used for customizing the behavior of the extractor.
        """
        super().__init__(configuration)

    def get_listing_page_formatters(self):
        """
        Returns a list of URLs representing different pages of claim reviews on the website.

        Returns
        -------
        List[str]
            A list of URLs representing different pages of claim reviews.
        """
        return [lambda page_number: f"https://africacheck.org/search?rt_bef_combine=created_DESC&sort_by=created&sort_order=DESC&search_api_fulltext=&sort_bef_combine=created_DESC&page={page_number}"]

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        """
        Extracts the URLs of individual claim review pages from the parsed listing page.

        Parameters
        ----------
        parsed_listing_page : BeautifulSoup
            The parsed HTML content of the listing page containing multiple claim reviews.

        Returns
        -------
        List[str]
            A list of URLs representing individual claim review pages.
        """
        urls = list()

        links = parsed_listing_page.findAll("div", {"class": "node__content"})
        for anchor in links:
            anchor = anchor.find('a', href=True)
            url = str(anchor['href'])
            if "http" in url:
                if "africacheck.org" in url:
                    urls.append(url)
            else:
                urls.append("https://africacheck.org" + str(anchor['href']))

        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        """
        Extracts information related to a claim review, including the claim text, rating, author, publication date, tags, referred links, etc.
        Handles cases with multiple claims in one page.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.
        url : str
            The URL of the claim review page.

        Returns
        -------
        List[Claim]
            A list of Claim objects containing the extracted information for each claim found in the review.
        """
        claim = Claim()

       

        # url of factcheck
        claim.set_url(url)

        # source organization
        claim.set_source("africacheck")

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
        body_descriptions = self.extract_claim_review_body(parsed_claim_review_page)
        #claim.set_body(body_description)

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
        claim_texts = self.extract_claim(parsed_claim_review_page)

        # rating of claim
        ratings, best_ratings, worst_ratings, rating_values = self.extract_rating(parsed_claim_review_page)

        if len(claim_texts) == len(ratings) == len(best_ratings) == len(worst_ratings) == len(rating_values) == len(body_descriptions) == 1:
            claim.set_claim(claim_texts[0])
            claim.set_rating(ratings[0])
            claim.set_best_rating(best_ratings[0])
            claim.set_worst_rating(worst_ratings[0])
            claim.set_rating_value(rating_values[0])
            claim.set_body(body_descriptions[0])

            claims = [claim]

        else:  # Create multiple claims from the main one and add change then the claim text and verdict (rating):
            claims = []
            if len(claim_texts) != len(ratings):
                print(f"found different amounts of claims and ratings: {url}")
                print(len(claim_texts), len(ratings), len(best_ratings), len(worst_ratings), len(rating_values), len(body_descriptions))
                print()
                min_n = min(len(claim_texts), len(ratings), len(best_ratings), len(worst_ratings), len(rating_values), len(body_descriptions))
                claim_texts = claim_texts[:min_n]
                ratings = ratings[:min_n]
                best_ratings = best_ratings[:min_n]
                worst_ratings = worst_ratings[:min_n]
                rating_values = rating_values[:min_n]
                body_descriptions = body_descriptions[:min_n]

            for claim_text, rating, best_rating, worst_rating, rating_value, body_description in zip(claim_texts, ratings, best_ratings, worst_ratings, rating_values, body_descriptions):
                single_claim = copy.deepcopy(claim)

                single_claim.set_claim(claim_text)
                single_claim.set_rating(rating)
                single_claim.set_best_rating(best_rating)
                single_claim.set_worst_rating(worst_rating)
                single_claim.set_rating_value(rating_value)

                single_claim.set_body(body_description)

                claims.append(single_claim)

        return claims

    def extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the title of the claim review from the parsed claim review page.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        str
            The title of the claim review.
        """
        try:
            title_element = parsed_claim_review_page.find("meta", {"property": "og:title"})
            title = title_element['content']
            if "|" in title:
                title = title.split("|")[-1]

            title = clean_string(title)

            if title == "":
                title = "INFO: No claim review title found"

        except:
            title = "ERROR: Error when extracting claim review title"

        return title

    def extract_claim_review_author(self, parsed_claim_review_page: BeautifulSoup) -> str: # actually more found in html
        """
        Extracts the author's name of the claim review from the parsed claim review page.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        str
            The author's name of the claim review.
        """
        try:
            review_author = parsed_claim_review_page.find('div', {'class': 'author-details'})
            review_author = review_author.find('a', href=True).find("h4")
            review_author = review_author.text
            review_author = clean_string(review_author)

            if review_author == "":
                review_author = "INFO: No claim review author found"

        except:
            review_author = "ERROR: Error when extracting claim review author"

        return review_author

    def extract_claim_review_author_url(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the URL of the claim review author's page from the parsed claim review page.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        str
            The URL of the claim review author's page.
        """
        try:
            review_author = parsed_claim_review_page.find('div', {'class': 'author-details'})
            review_author_url = review_author.find('a', href=True)
            review_author_url = review_author_url['href']

            if review_author_url == "":
                review_author_url = "INFO: No claim review author url found"

        except:
            review_author_url = "ERROR: Error when extracting claim review author url"

        return review_author_url

    def extract_date_claim_review_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the publication date of the claim review from the parsed claim review page.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        str
            The publication date of the claim review (formatted as "YYYY-MM-DD").
        """
        try:
            date_claim_review_pub = ""

            for d in parsed_claim_review_page.find_all(string=re.compile("schema.org")):
                if '"@type": "NewsArticle"' in str(d):
                    data = json.loads(str(d))
                    break

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

    def extract_claim(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the claim text from the parsed claim review page.
        Handles different HTML structures for claim extraction.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        List[str]
            A list of claim texts extracted from the claim review.
        """
      
        def _extract_claim_v1(parsed_claim_review_page: BeautifulSoup) -> str:
            claim_texts = []

            for d in parsed_claim_review_page.find_all(string=re.compile("schema.org")):
                if '"@type": "ClaimReview"' in str(d):
                    data = json.loads(str(d))

                    node_zero = data['@graph'][0]

                    claim_text = ""

                    if "claimReviewed" in node_zero:
                        claim_text = node_zero['claimReviewed']
                        claim_text = clean_string(claim_text)

                    if claim_text != "":
                        claim_texts.append(claim_text)

            return claim_texts

        def _extract_claim_v2(parsed_claim_review_page: BeautifulSoup) -> str:
            claim_texts = []

            claim_elements = parsed_claim_review_page.find_all('p', {'class': 'claim-content'})

            for claim_element in claim_elements:
                claim_text = clean_string(claim_element.text)
                claim_texts.append(claim_text)

            return claim_texts

        def _extract_claim_v3(parsed_claim_review_page: BeautifulSoup) -> str:
            claim_texts = []

            claim_element = parsed_claim_review_page.find('div', {'class': 'field--name-field-claims'})

            if claim_element:
                claim_text = clean_string(claim_element.text)
                claim_texts.append(claim_text)

            return claim_texts

        def _extract_claim_v4(parsed_claim_review_page: BeautifulSoup) -> str:
            claim_texts = []

            title_element = parsed_claim_review_page.find("meta", {"property": "og:title"})
            claim_text = title_element['content']
            if "|" in claim_text:
                claim_text = claim_text.split("|")[-1]

            claim_text = clean_string(claim_text)
            claim_texts.append(claim_text)

            return claim_texts

        claim_texts = []

        for func in [_extract_claim_v1, _extract_claim_v2, _extract_claim_v3, _extract_claim_v4]:
            try:
                claim_texts = func(parsed_claim_review_page)
                if len(claim_texts) > 0:
                    break
                    #if len(set(claim_texts)) == len(claim_texts): # sanity check to not extract the same claim twice
                        #break
            except:
                continue

        if len(claim_texts) == 0:
            claim_texts = [f"INFO: no claim found"]

        return claim_texts

    def extract_rating(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the rating, best rating, worst rating, and rating value from the parsed claim review page.
        Handles different HTML structures for rating extraction.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        Tuple[List[str], List[str], List[str], List[str]]
            A tuple containing lists of ratings, best ratings, worst ratings, and rating values extracted from the claim review.
        """
        

        def _extract_rating_v1(parsed_claim_review_page: BeautifulSoup) -> str:
            ratings = []
            best_ratings = []
            worst_ratings = []
            rating_values = []

            for d in parsed_claim_review_page.find_all(string=re.compile("schema.org")):
                if '"@type": "ClaimReview"' in str(d) and "claimReviewed" in str(d):
                    data = json.loads(str(d))

                    node_zero = data['@graph'][0]

                    rating = ""
                    best_rating = ""
                    worst_rating = ""
                    rating_value = ""

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

                    if rating == "":
                        rating = "INFO: no rating found"
                    if best_rating == "":
                        best_rating = "INFO: no best rating found"
                    if worst_rating == "":
                        worst_rating = "INFO: no worst rating found"
                    if rating_value == "":
                        rating_value = "INFO: no rating value found"

                    ratings.append(rating)
                    best_ratings.append(best_rating)
                    worst_ratings.append(worst_rating)
                    rating_values.append(rating_value)

            return ratings, best_ratings, worst_ratings, rating_values

        def _extract_rating_v5(parsed_claim_review_page: BeautifulSoup) -> str:
            valid_ratings = ["Incorrect",
                             "Mostly Correct",
                             "Correct",
                             "Unproven",
                             "Misleading",
                             "Exaggerated",
                             "Understated",
                             "Checked",
                             "Partlyfalse",
                             "Partlytrue",
                             "True",
                             "False",
                             "Fake",
                             "Scam",
                             "Satire",
                             'Hoax']

            ratings = []

            image_meta = parsed_claim_review_page.find("meta", {'property': 'og:image'})
            image_path = image_meta['content']
            image_fn = image_path.split("/")[-1]

            for vr in valid_ratings:
                if vr.upper() in image_fn.upper():
                    ratings.append(vr)
                    break

            return ratings, [], [], []

        def _extract_rating_v6(parsed_claim_review_page: BeautifulSoup) -> str:
            valid_ratings = ["Incorrect",
                             "Mostly Correct",
                             "Correct",
                             "Unproven",
                             "Misleading",
                             "Exaggerated",
                             "Understated",
                             "Checked",
                             "Partlyfalse",
                             "Partlytrue",
                             "True",
                             "False",
                             "Fake",
                             "Scam",
                             "Satire",
                             'Hoax']

            ratings = []

            image_meta = parsed_claim_review_page.find("div", {'class': 'hero__image'})
            image_source = image_meta.find("img", recursive=True)
            image_fn = image_source.attrs['src']

            for vr in valid_ratings:
                if vr.upper() in image_fn.upper():
                    ratings.append(vr)
                    break

            return ratings, [], [], []

        def _extract_rating_v3(parsed_claim_review_page: BeautifulSoup) -> str:
            valid_ratings = ["Incorrect",
                             "Mostly Correct",
                             "Correct",
                             "Unproven",
                             "Misleading",
                             "Exaggerated",
                             "Understated",
                             "Checked",
                             "Partlyfalse",
                             "Partlytrue",
                             "True",
                             "False",
                             "Fake",
                             "Scam",
                             "Satire",
                             'Hoax']

            ratings = []

            tags = parsed_claim_review_page.findAll("meta", {'property': 'article:tag'})
            tags = [tag.attrs['content'] for tag in tags]

            for tag in tags:
                for vr in valid_ratings:
                    if vr.upper() in tag.upper():
                        ratings.append(vr)
                        break

                if len(ratings) == 1:
                    break


            return ratings, [], [], []

        def _extract_rating_v2(parsed_claim_review_page: BeautifulSoup) -> str:
            ratings = []

            rating_elements = parsed_claim_review_page.find_all('div', {'class': 'report-verdict indicator'})
            for rating_element in rating_elements:
                rating = clean_string(rating_element.span.text).title()
                ratings.append(rating)

            return ratings, [], [], []

        def _extract_rating_v4(parsed_claim_review_page: BeautifulSoup) -> str:
            ratings = []

            rating_element = parsed_claim_review_page.find('div', {'class': 'article-details__verdict'})
            rating_element = rating_element.find('div', {'class': 'rating'})
            rating = [r for r in rating_element.attrs['class'] if "--" in r][0]
            if rating:
                rating = rating.replace('rating--', '')
                rating = clean_string(rating)
                rating = rating.title()
                ratings.append(rating)

            return ratings, [], [], []

        ratings = []
        best_ratings = []
        worst_ratings = []
        rating_values = []

        for func in [_extract_rating_v1, _extract_rating_v2, _extract_rating_v3, _extract_rating_v4, _extract_rating_v5, _extract_rating_v6]:
            try:
                ratings, best_ratings, worst_ratings, rating_values = func(parsed_claim_review_page)
                if len(ratings) > 0:
                    break
            except Exception as e:
                continue

        if len(ratings) == 0:
            ratings = [f"INFO: no rating found"]

        if len(best_ratings) == 0:
            best_ratings = [f"INFO: no best rating found"] * len(ratings)
            worst_ratings = [f"INFO: no worst rating found"] * len(ratings)
            rating_values = [f"INFO: no rating values found"] * len(ratings)

        return ratings, best_ratings, worst_ratings, rating_values

    def extract_claim_review_body(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the body content of the claim review from the parsed claim review page.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        List[str]
            A list of body contents extracted from the claim review.
        """
        

        try:
            article_content = parsed_claim_review_page.find('div', {'class': 'node__content'})

            # remove all script tags from article content
            for script in article_content.find_all("script", recursive=True):
                script.decompose()

            text = article_content.get_text(strip=True, separator=' ')
            text = clean_string(text)

            # if text has multiple claims (we check for div class="inline-rating") we split the text to individual texts for each claim
            claim_rating_elements = parsed_claim_review_page.find_all('div', {'class': 'inline-rating'})
            if claim_rating_elements:
                #split text
                text_splits = []
                for claim_rating_element in claim_rating_elements:
                    claim_rating = clean_string(claim_rating_element.get_text(strip=True, separator=' '))
                    text_before, text_after = text.split(claim_rating)
                    text_splits.append(clean_string(text_before))
                    text = text_after

                text_splits.append(clean_string(text_after))

                general_text = text_splits.pop(0)
                claim_bodys = [general_text + " " + text for text in text_splits]

            else:
                if text != "":
                    claim_bodys = [text]

            if len(claim_bodys) == 0:
                claim_bodys = ["INFO: no body found"]

        except:
            claim_bodys = ["ERROR: Error when extracting body"]

        return claim_bodys

    def extract_tags(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts tags related to the claim review from the parsed claim review page.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        str
            A string containing tags related to the claim review, separated by ":-:".
        """
        try:
            tags = []

            tag_list = parsed_claim_review_page.findAll('meta', {"property": "article:tag"})
            for tag in tag_list:
                try:
                    tags.append(clean_string(tag["content"]))
                except:
                    continue

            tags = ":-:".join(tags)

            if tags == "":
                tags = "INFO: No tags found"

        except:
            tags = "ERROR: Error when extracting tags"

        return tags

    def extract_referred_links(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts referred links within the claim review page from the parsed claim review page.

        Parameters
        ----------
        parsed_claim_review_page : BeautifulSoup
            The parsed HTML content of the claim review page.

        Returns
        -------
        str
            A string containing referred links within the claim review, separated by ":-:".
        """
        try:
            referred_links = []

            article_content = parsed_claim_review_page.find('div', {'class': 'node__content'})

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
