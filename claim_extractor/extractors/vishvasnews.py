# -*- coding: utf-8 -*-
import calendar  # convert month name to month number
import json
import re
from typing import *

import requests
from bs4 import BeautifulSoup

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.tagme import tagme


class VishvasnewsFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    """
    This class is a custom extractor for the Vishvasnews fact-checking website.
    It inherits from the FactCheckingSiteExtractor base class and implements
    methods to retrieve and extract claim reviews from Vishvasnews.

    Attributes:
        TAGME_API_KEY (str): The API key used for TagMe API to extract entities.

    Methods:
        __init__(self, configuration: Configuration): Initializes the extractor with a given configuration.
        get(self, url: str) -> BeautifulSoup: Sends an HTTP GET request to a URL and parses the response using BeautifulSoup.
        post(self, url: str, data: dict) -> BeautifulSoup: Sends an HTTP POST request to a URL with data and parses the response using BeautifulSoup.
        retrieve_listing_page_urls(self) -> List[str]: Retrieves the URLs of pages that allow access to a paginated list of claim reviews.
        find_page_count(self, parsed_listing_page: BeautifulSoup) -> int: Finds the page count for paginated claim reviews.
        retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> List[str]: Retrieves the URLs of all claim reviews from paginated listing pages.
        extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]: Extracts the claim and review details from a parsed claim review page.
        is_claim(self, parsed_claim_review_page: BeautifulSoup) -> bool: Checks if the page contains a claim review.
        extract_claim(self, parsed_claim_review_page: BeautifulSoup) -> str: Extracts the claim text from a parsed claim review page.
        extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str: Extracts the title of the claim review from a parsed claim review page.
        extract_review(self, parsed_claim_review_page: BeautifulSoup) -> str: Extracts the review text from a parsed claim review page.
        extract_claimed_by(self, parsed_claim_review_page: BeautifulSoup) -> str: Extracts the claimed by information from a parsed claim review page.
        extract_links(self, parsed_claim_review_page: BeautifulSoup) -> str: Extracts the links mentioned in the claim review from a parsed claim review page.
        extract_date(self, parsed_claim_review_page: BeautifulSoup) -> str: Extracts the date of the claim review publication from a parsed claim review page.
        extract_tags(self, parsed_claim_review_page: BeautifulSoup) -> str: Extracts the tags related to the claim review from a parsed claim review page.
        extract_author(self, parsed_claim_review_page: BeautifulSoup) -> str: Extracts the author(s) of the claim review from a parsed claim review page.
        extract_rating_value(self, parsed_claim_review_page: BeautifulSoup, url: str) -> str: Extracts the rating value of the claim review from a parsed claim review page.
        extract_entities(self, claim: str, review: str): Extracts entities from the claim and review text using TagMe API.
        translate_rating_value(self, initial_rating_value: str) -> str: Translates the initial rating value to "False," "Misleading," or "True."
        tagme(text) -> list: Calls the TagMe API to annotate the text and returns a list of claim entities.
        get_json_format(tagme_entity): Converts the TagMe entity annotation to JSON format.
        escape(self, str): Escapes special characters and formats the string in CSV format.
    """

    TAGME_API_KEY = 'b6fdda4a-48d6-422b-9956-2fce877d9119-843339462'

    def __init__(self, configuration: Configuration):
        """
        Initializes the VishvasnewsFactCheckingSiteExtractor with a given Configuration.

        Parameters:
            configuration (Configuration): The configuration object containing extraction settings.
        """
        super().__init__(configuration)

    def get(self, url):
        """
        Sends an HTTP GET request to the specified URL and parses the response content using BeautifulSoup.
        Removes certain tags like "script", "iframe", "head", "header", "footer", and "style" from the response content.

        Parameters:
            url (str): The URL of the webpage to fetch and parse.

        Returns:
            BeautifulSoup: The parsed content of the webpage in BeautifulSoup format.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        html = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html, 'lxml')
        # removing some useless tags
        for s in soup.select("script, iframe, head, header, footer, style"):
            s.decompose()
        return soup

    def post(self, url, data):
        """
        Sends an HTTP POST request to the specified URL with the provided data and parses the response content using BeautifulSoup.
        Removes certain tags like "script", "iframe", "head", "header", "footer", and "style" from the response content.

        Parameters:
            url (str): The URL to which the POST request is sent.
            data (dict): The data to be sent as part of the POST request.

        Returns:
            BeautifulSoup: The parsed content of the webpage in BeautifulSoup format.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        html = requests.post(url, data=data, headers=headers).text
        soup = BeautifulSoup(html, 'lxml')
        # removing some useless tags
        for s in soup.select("script, iframe, head, header, footer, style"):
            s.decompose()
        return soup

    def retrieve_listing_page_urls(self) -> List[str]:
        """
            Abstract method. Retrieve the URLs of pages that allow access to a paginated list of claim reviews. This
            concerns some sites where all the claims are not listed from a single point of access but first
            categorized by another criterion (e.g. on politifact there is a separate listing for each possible rating).
            :return: Return a list of listing page urls
            
            Returns:
            List[str]: A list of listing page urls
        """
        different_urls = []
        different_categories_value = [
            "politics", "society", "world", "viral", "health"]
        url_begins = [
            "https://www.vishvasnews.com/english/",
            "https://www.vishvasnews.com/urdu/",
            "https://www.vishvasnews.com/assamese/",
            "https://www.vishvasnews.com/tamil/",
            "https://www.vishvasnews.com/malayalam/",
            "https://www.vishvasnews.com/gujarati/",
            "https://www.vishvasnews.com/telugu/",
            "https://www.vishvasnews.com/marathi/",
            "https://www.vishvasnews.com/odia/"]
            
        
        for url in url_begins:
            for value in different_categories_value:
                different_urls.append(url + value + "/")

        return different_urls

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        """
        A listing page is paginated and will sometimes contain information pertaining to the maximum number of pages
        there are. For sites that do not have that information, please return a negative integer or None.

        Parameters:
            parsed_listing_page (BeautifulSoup): The parsed content of the listing page.

        Returns:
            int: The page count if relevant, otherwise None or a negative integer.
        """
        return -1

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> List[
        str]:
        """
        Retrieves the URLs of all claim reviews from paginated listing pages.

        Parameters:
            parsed_listing_page (BeautifulSoup): The parsed content of the listing page.
            listing_page_url (str): The URL of the listing page.
            number_of_pages (int): The number of pages to retrieve claim reviews from.

        Returns:
            List[str]: A list of URLs representing all the claim reviews.
        """
        tmp_counter = 0
        links = []
        select_links = 'ul.listing li div.imagecontent h3 a'
        # links in the static page
        claims = parsed_listing_page.select(
            "div.ajax-data-load " + select_links)

        if self.configuration.maxClaims >= 1:
            for link in claims:
                if link["href"] and tmp_counter < self.configuration.maxClaims:
                    tmp_counter += 1
                    links.append(link["href"])
        else:
            for link in claims:
                if link["href"]:
                    links.append(link["href"])


        # for links loaded by AJAX
        r = re.compile(
            "https://www.vishvasnews.com/(.*)/(.*)[/]").match(listing_page_url)

        lang = r.group(1)
        categorie = r.group(2)

        url_ajax = "https://www.vishvasnews.com/wp-admin/admin-ajax.php"
        data = {
            'action': 'ajax_pagination',
            'query_vars': '{"category_name" : "' + categorie + '", "lang" : "' + lang + '"}',
            'page': 1,
            'loadPage': 'file-archive-posts-part'
        }

        response = self.post(url_ajax, data)
        
        if self.configuration.maxClaims >= 1:
            while True and tmp_counter < self.configuration.maxClaims:
                claims = response.select(select_links)
                for link in claims:
                    if link['href'] and tmp_counter < self.configuration.maxClaims:
                        tmp_counter += 1
                        links.append(link['href'])

                if response.find("nav"):
                    data['page'] = data['page'] + 1
                    response = self.post(url_ajax, data)
                    continue
                else:
                    break
        else:
            while True:
                claims = response.select(select_links)
                for link in claims:
                    if link['href']:
                        links.append(link['href'])

                if response.find("nav"):
                    data['page'] = data['page'] + 1
                    response = self.post(url_ajax, data)
                    continue
                else:
                    break
        print(links)
        return links

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        """
        Extracts the claim and review details from a parsed claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.
            url (str): The URL of the claim review page.

        Returns:
            List[Claim]: A list of Claim objects containing the extracted details.
        """
        claim = Claim()
        claim_txt = self.extract_claim(parsed_claim_review_page)
   

        review = self.extract_review(parsed_claim_review_page)
    
        rating_value = self.extract_rating_value(parsed_claim_review_page, url)
        
        claim.set_rating(rating_value)
       
        claim.set_source("Vishvanews")  # auteur de la review
        claim.review_author = self.extract_author(parsed_claim_review_page)
        claim.set_author(self.extract_claimed_by(
            parsed_claim_review_page))  # ? auteur de la claim?
        # claim.setDatePublished(self.extract_date(parsed_claim_review_page)) #? publication de la claim
        claim.set_claim(claim_txt)
        claim.set_body(review)
        #claim.set_refered_links(self.extract_links(parsed_claim_review_page))
        claim.set_title(self.extract_title(parsed_claim_review_page))
        # date de la publication de la review
        claim.set_date(self.extract_date(parsed_claim_review_page))
        claim.set_url(url)
        claim.set_tags(self.extract_tags(parsed_claim_review_page))

        # extract_entities returns two variables
        json_claim, json_body = self.extract_entities(claim_txt, review)
        claim.claim_entities = json_claim
        claim.body_entities = json_body

        if claim.rating != "":
            return [claim]
        else:
            return []
        
    def is_claim(self, parsed_claim_review_page: BeautifulSoup) -> bool:
        """
        Checks if the page contains a claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            bool: True if a claim review is found, False otherwise.
        """
        rating_value = parsed_claim_review_page.select_one(
            "div.selected span")
        return bool(rating_value)

    def extract_claim(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the claim text from a parsed claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            str: The extracted claim text.
        """
        claim = parsed_claim_review_page.select_one("ul.claim-review li span")
        # check that the claim is in english
        if claim:
            return self.escape(claim.text)
        else:
            return ""

    def extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the title of the claim review from a parsed claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            str: The extracted title of the claim review.
        """
        title = parsed_claim_review_page.find("h1", class_="article-heading")
        if title:
            return self.escape(title.text)
        else:
            return ""

    def extract_review(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the review text from a parsed claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            str: The extracted review text.
        """
        review = ""
        paragraphs = parsed_claim_review_page.select("div.lhs-area > p")

        if paragraphs:
            for paragraph in paragraphs:
                review += paragraph.text + " "

        return self.escape(review)

    def extract_claimed_by(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the "claimed by" information from a parsed claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            str: The extracted "claimed by" information.
        """
        review = parsed_claim_review_page.select("ul.claim-review li span")

        if len(review) > 1:
            return self.escape(review[1].text)
        else:
            return ""

    def extract_links(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the links (URLs) present in the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            str: A CSV-formatted string containing the extracted links.
        """
        links = []

        # extracting the main article body
        #review_body = parsed_claim_review_page.select_one("div.lhs-area")
        
        #review_body = parsed_claim_review_page.find('p', {'class': 'summery'})
        review_body = parsed_claim_review_page.find('div', {'class': 'lhs-area'})
       

        # extracting links
        for paragraph_tag in review_body.find_all("p"):
            for link_tag in paragraph_tag.find_all("a"):
                if link_tag.has_attr('href'):
                    links.append(link_tag['href'])

        # Links to embedded tweets
        for figure_tag in review_body.find_all("figure"):
            iframe = figure_tag.find("iframe")
            if iframe is not None:
                if iframe.has_attr('src'):
                    links.append(iframe['src'])
                elif iframe.has_attr("data-src"):
                    links.append(iframe['data-src'])

        return self.escape(str(links))

    def extract_date(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the date from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            str: The extracted date in the format "YYYY-MM-DD", or an empty string if no date is found.
        """
        date = parsed_claim_review_page.select("ul.updated li")[1].text.strip()
        if not date:
            return ""

        r = re.compile(
            '^Updated: *([a-zA-Z]+) ([0-9]+), ([0-9]{4})$').match(date)

        month = str({v: k for k, v in enumerate(
            calendar.month_name)}[r.group(1)])
        day = r.group(2)
        year = r.group(3)

        date = year + '-' + month + '-' + day
        return date

    def extract_tags(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the tags related to the claim from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            str: A CSV-formatted string containing the extracted tags.
        """
        tags_link = parsed_claim_review_page.select(
            "ul.tags a")
        tags = []
        for tag_link in tags_link:
            if tag_link.text:
                tags.append((tag_link.text).replace("#", ""))

        return self.escape(str(tags))

    def extract_author(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the author(s) of the claim review from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.

        Returns:
            str: A CSV-formatted string containing the extracted author(s).
        """
        authors = []

        for author in parsed_claim_review_page.select("li.name a"):
            authors.append(author.text)

        return ",".join(authors)

    def extract_rating_value(self, parsed_claim_review_page: BeautifulSoup, url: str) -> str:
        """
        Extracts the rating value (e.g., False, Misleading, True) from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed content of the claim review page.
            url (str): The URL of the claim review page.

        Returns:
            str: The extracted rating value, or an empty string if not found.
        """
        r = "" 
        detect_lang = "english"

        if url.split("/")[3]: 
            self.language = url.split("/")[3]
            detect_lang = url.split("/")[3]
        else:
            self.language = "eng"

        btn = parsed_claim_review_page.select_one("div.selected span")
        if btn:
            if detect_lang != 'english':
                r = self.translate_rating_value(str(btn.text.replace("\u200e","").strip(" ")))
                #print("\r" + btn.text.replace("\u200e","").strip(" ") + " => " + r)
            #if r == "" and ("Misleading" not in btn.text and "False" not in btn.text and "True" not in btn.text):
            #    print(btn.text.strip(" "))
            if r != "":
                return r
            else:
                return btn.text.strip()
        else:
            return ""

    def extract_entities(self, claim: str, review: str):
        """
        Extracts entities (tags) from the claim and review text.

        You should call the extract_claim and extract_review methods and
        store the results in self.claim and self.review before calling this method.

        Parameters:
            claim (str): The extracted claim from the claim review page.
            review (str): The extracted review text from the claim review page.

        Returns:
            Tuple[str, str]: A tuple containing the CSV-formatted strings of claim_entities and review_entities.
        """
        return self.escape(self.get_json_format(self.tagme(claim))), self.escape(
            self.get_json_format(self.tagme(review)))

    # Translates to False, Misleading or True https://www.vishvasnews.com/methodology/ 
    def translate_rating_value(self, initial_rating_value: str) -> str:
        """
        Translates the initial rating value to English (False, Misleading, True) based on a predefined dictionary.

        Parameters:
            initial_rating_value (str): The initial rating value in the native language.

        Returns:
            str: The translated rating value in English, or an empty string if the translation is not found in the dictionary.
        """
        dictionary = {
            # Punjabi:
            # Misleading 
            "ਭ੍ਰਮਕ": "Misleading",

            # False
            "ਫਰਜ਼ੀ": "False",

            # True 
            "ਸੱਚ" : "True",

            # Uudu:
            # Misleading 
            "گمراہ کن": "Misleading",

            # False
            "جھوٹ": "False",

            # True 
            "سچ": "True"

            # Assamese, Tamil, malayalam, gujarati, telugu, marathi, odia and bangla same as english:
        }
    
        
        
        if initial_rating_value in dictionary:
                return dictionary[initial_rating_value]
        else:
            return ""

    #@staticmethod
    #def translate_rating_value(initial_rating_value: str) -> str:
    #    return initial_rating_value

    @staticmethod
    def tagme(text) -> list:
        """
        Extracts entities using the TagMe API.

        Parameters:
            text (str): The text in English after translation.

        Returns:
            list: A list of claim_entities.
        """
        #if text == "":
        #    return []
        #tagme.GCUBE_TOKEN = VishvasnewsFactCheckingSiteExtractor.TAGME_API_KEY
        #return tagme.annotate(text)
        return []


    # write this method (and tagme, translate) in an another file cause we can use it in other websites
    @staticmethod
    def get_json_format(tagme_entity):
        """
        Converts the TagMe annotation response into a JSON-formatted string.

        Parameters:
            tagme_entity: An object of the AnnotateResponse class returned by the tagme function.

        Returns:
            str: A JSON-formatted string containing the entity information.
        """
        data_set = []
        i = 0
        min_rho = 0.1

        # in case tagme() method return nothing
        if tagme_entity != []:
            for annotation in tagme_entity.get_annotations(min_rho):
                entity = {}
                entity["id"] = annotation.entity_id
                entity["begin"] = annotation.begin
                entity["end"] = annotation.end
                entity["entity"] = annotation.entity_title
                entity["text"] = annotation.mention
                entity["score"] = annotation.score
                entity["categories"] = []
                if tagme_entity.original_json["annotations"][i]["rho"] > min_rho and "dbpedia_categories" in \
                        tagme_entity.original_json["annotations"][i]:
                    for categorie in tagme_entity.original_json["annotations"][i]["dbpedia_categories"]:
                        entity["categories"].append(categorie)
                i = i + 1
                data_set.append(entity)

        return json.dumps(data_set)

    @staticmethod
    def escape(str):
        """
        Escapes special characters and formats the string in CSV format.

        Parameters:
            str (str): The string to be escaped.

        Returns:
            str: The escaped string in CSV format.
        """
        str = re.sub('[\n\t\r]', ' ', str)  # removing special char
        str = str.replace('"', '""')  # escaping '"' (CSV format)
        str = re.sub(' {2,}', ' ', str).strip()  # remoing extra spaces
        str = '"' + str + '"'
        return str
