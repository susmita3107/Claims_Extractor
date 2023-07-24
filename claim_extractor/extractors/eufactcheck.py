# -*- coding: utf-8 -*-
import re
from typing import List

from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching, find_by_text


class EufactcheckFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    """
    A class that extracts fact-checking claims and related information from the Eufactcheck website.
    """

    def __init__(self, configuration: Configuration):
        """
        Initialize the EufactcheckFactCheckingSiteExtractor.

        :param configuration: The configuration object containing extractor settings.
        :type configuration: Configuration
        """
        super().__init__(configuration)

    def retrieve_listing_page_urls(self) -> List[str]:
        """
        Retrieves the URLs of listing pages for fact-checking articles.

        :return: A list of URLs of listing pages.
        :rtype: List[str]
        """
        return ["https://eufactcheck.eu/page/1/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        """
        Finds the total number of fact-checking pages available.

        :param parsed_listing_page: The parsed listing page containing pagination information.
        :type parsed_listing_page: BeautifulSoup
        :return: The total number of fact-checking pages available.
        :rtype: int
        """
        pages_list = parsed_listing_page.find("div", {"class":"paginator"}).findAll("a")
        max_page = int(pages_list[-2].contents[0])
        print(max_page)
        return max_page


    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        """
        Retrieves fact-checking article URLs from listing pages.

        :param parsed_listing_page: The parsed listing page containing fact-checking article links.
        :type parsed_listing_page: BeautifulSoup
        :param listing_page_url: The URL of the current listing page.
        :type listing_page_url: str
        :param number_of_pages: The total number of pages to retrieve URLs from.
        :type number_of_pages: int
        :return: A list of fact-checking article URLs.
        :rtype: List[str]
        """
        urls = self.extract_urls(parsed_listing_page)
        #parcours from 2 to end
        for page_number in tqdm(range(2, number_of_pages+1)):
            url = "https://eufactcheck.eu/page/" + str(page_number) + "/"
            #load from cache (download if not exists, sinon load )
            page = caching.get(url, headers=self.headers, timeout=20)
            if page is not None:
                #parser avec BeautifulSoup la page
                current_parsed_listing_page = BeautifulSoup(page, "lxml")
                #extriare les liens dans cette page et rajoute dans urls
                urls +=self.extract_urls(current_parsed_listing_page)
            else:
                break
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        """
        Extracts fact-checking article URLs from a parsed listing page.

        :param parsed_listing_page: The parsed listing page containing fact-checking article links.
        :type parsed_listing_page: BeautifulSoup
        :return: A list of fact-checking article URLs.
        :rtype: List[str]
        """
        urls = list()
        links = parsed_listing_page.findAll("a", {"class":"post-thumbnail-rollover"})
        for anchor in links:
            url = str(anchor['href'])
            if 'blogpost' in url : continue
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)
        return urls


    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        """
        Extracts fact-checking claim and review information from a parsed claim review page.

        :param parsed_claim_review_page: The parsed fact-checking claim review page.
        :type parsed_claim_review_page: BeautifulSoup
        :param url: The URL of the fact-checking claim review page.
        :type url: str
        :return: A list of Claim objects containing extracted claim and review information.
        :rtype: List[Claim]
        """
        claim = Claim()
        claim.set_url(url)
        claim.set_source("eufactcheck")

        #title
        #Since the title always starts with claim followed by the title of the article we split the string based on ":"
        full_title = parsed_claim_review_page.find("div", {"class":"page-title-head hgroup"}).find("h1").get_text()
        split_title = full_title.split(":")
        if len(split_title) == 1:
            split_title = full_title.split("–")
        claim.set_title(split_title[1].strip())

        #claim review published date
        full_date = parsed_claim_review_page.find("time", {"class":"entry-date updated"})['datetime'].split("T")
        claim.set_date(full_date[0])

        #body
        body = parsed_claim_review_page.find('div', {"class":"entry-content"})
        claim.set_body(body.get_text().replace("\n", " "))

        #related related_links
        related_links = []
        for link in body.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        claim.set_claim(claim.title)

        #rating
        rating = full_title[0].strip()
        claim.set_rating(rating)
        
        #author
      
        author= parsed_claim_review_page.find('span', {"class":"fn"})
        x = author.get_text().split(", ")
       
        claim.set_review_author(x[0])
        
        #tags
        tags = parsed_claim_review_page.find('div', {"class":"entry-tags"})
        claim.set_tags(tags.get_text())
        
        
        return [claim]