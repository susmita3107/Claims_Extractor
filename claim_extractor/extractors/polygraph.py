# -*- coding: utf-8 -*-
from typing import List

from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class PolygraphFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    """
    A class that extracts fact-checking claims and related information from the Polygraph website.
    """

    def __init__(self, configuration: Configuration):
        """
        Initialize the PolygraphFactCheckingSiteExtractor.

        :param configuration: The configuration object containing extractor settings.
        :type configuration: Configuration
        """
        super().__init__(configuration, language="rus")

    def retrieve_listing_page_urls(self) -> List[str]:
        """
        Retrieves the URLs of listing pages for fact-checking articles.

        :return: A list of URLs of listing pages.
        :rtype: List[str]
        """
        return ["https://www.polygraph.info/z/7205?p=0"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        """
        Finds the total number of fact-checking pages available.

        :param parsed_listing_page: The parsed listing page containing pagination information.
        :type parsed_listing_page: BeautifulSoup
        :return: The total number of fact-checking pages available.
        :rtype: int
        """
        count = 0
        url = "https://www.polygraph.info/z/7205?p=" + str(count + 1)
        result = caching.get(url, headers=self.headers, timeout=10)
        if result:
            while result:
                count += 1
                url = "https://www.polygraph.info/z/7205?p=" + str(count)
                result = caching.get(url, headers=self.headers, timeout=10)
                if result:
                    parsed = BeautifulSoup(result, self.configuration.parser_engine)
                    articles = parsed.findAll("li", {"class": "fc__item"})
                    if not articles or len(articles) == 0:
                        break
        else:
            count -= 1
        print(count - 1)
        return count - 1

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
        # lien de la premiere page -> liste de textes
        urls = self.extract_urls(parsed_listing_page)
        # parcours from 2 to end
        for page_number in tqdm(range(0, number_of_pages + 1)):
            url = "https://www.polygraph.info/z/7205?p=" + str(page_number) 
            print(url)
            # load from cache (download if not exists, sinon load )
            page = caching.get(url, headers=self.headers, timeout=5)
            if page:
                # parser avec BeautifulSoup la page
                current_parsed_listing_page = BeautifulSoup(page, "lxml")
                # extriare les liens dans cette page et rajoute dans urls
                urls += self.extract_urls(current_parsed_listing_page)
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
        # when simply findAll(a, class=title), same href exists two times (title and title red)
        links = parsed_listing_page.findAll(lambda tag: tag.name == 'a' and
                                                        tag.get('class') == ['title'])
        for anchor in links:
            url = "https://www.polygraph.info" + str(anchor['href'])
            print(url)
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
        claim.set_source("polygraph")
        
        

        # title
        title = parsed_claim_review_page.find("h1", {"class": "title pg-title"})
        claim.set_title(title.text.replace(";", ","))
        print("title")
        print(claim.set_title)
        
        

        # review date
        full_date = parsed_claim_review_page.find("time")['datetime'].split("T")
        claim.set_date(full_date[0])
        print("date")
        print(claim.set_date)
        
        
        
        
        body = parsed_claim_review_page.find("div", {"id": "article-content"})
        claim.set_body(body.get_text())
        print("body")
        print(claim.set_body)
        

        # related related_links
        related_links = []
        for link in body.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        claim.set_claim(claim.title)

        # creative work author
        author = parsed_claim_review_page.find('h4', {"class": "author"})
        claim.set_author(author.text)
        print("author")
        print(claim.set_author)
        
        #claim review author
        try:        
            review_author = parsed_claim_review_page.find('a', {"class": "links__item-link"})
            print("review_author")
            print(review_author.text)
            claim.set_review_author(review_author.text)
        except AttributeError:
            pass
            

        # rating
        rating = parsed_claim_review_page.find('div', {"class": "verdict"}).find_all('span')[1]
        claim.set_rating(rating.text)
        print("rating")
        print(claim.set_rating)

        return [claim]
