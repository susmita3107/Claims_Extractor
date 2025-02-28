# -*- coding: utf-8 -*-
import json
import re
from typing import List

from bs4 import BeautifulSoup
from tqdm import trange

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


# factutel.afp.com can be changed by the english version factcheck.afp.com which contains much more claims

class AfpfactuelFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    """
    A class for extracting fact-checking claims from the AFP Factuel fact-checking website.
    Inherits from FactCheckingSiteExtractor class.
    """

    def __init__(self, configuration: Configuration = Configuration(), ignore_urls: List[str] = None, headers=None,
                 language="fra"):
        """
        Constructor for AfpfactuelFactCheckingSiteExtractor class.

        Args:
        configuration (Configuration): An instance of the Configuration class to customize extraction settings.
        ignore_urls (List[str]): A list of URLs to ignore during claim extraction.
        headers: The headers to use for HTTP requests.
        language (str): The language of the website. Default is "fra" (French).
        
        """
        super().__init__(configuration, ignore_urls, headers, language)
        self.base_url = "https://factuel.afp.com/"

    def retrieve_listing_page_urls(self) -> List[str]:
        """
        Retrieves the URLs of listing pages from the AFP Factuel website.

        Returns:
        List[str]: A list of URLs of listing pages.

        """
        return ["https://factuel.afp.com/list/all/37881/all/all/87",
                "https://factuel.afp.com/list/all/37075/all/all/88",
                "https://factuel.afp.com/list/all/37783/all/all/89",
                "https://factuel.afp.com/list/all/37074/all/all/90",
                "https://factuel.afp.com/list/all/37202/all/all/135",
                "https://factuel.afp.com/list/all/37412/all/all/1201",
                "https://factuel.afp.com/list/all/all/39405/all/2535",
                "https://factuel.afp.com/list/all/all/39297/all/1814",
                "https://factuel.afp.com/list/all/all/35799/all/130",
                "https://factuel.afp.com/list/38329/all/all/all/11",
                "https://factuel.afp.com/list/all/all/all/38562/10",
                "https://factuel.afp.com/list/all/all/all/38558/12",
                "https://factuel.afp.com/list/all/all/all/38560/13",
                "https://factuel.afp.com/list/all/all/all/38559/14",
                "https://factuel.afp.com/list/all/all/all/38561/15",
                "https://factuel.afp.com/list/all/all/all/38563/16"
                
                #"https://factuel.afp.com/covid-19-60-des-contaminations-en-france-au-travail-ou-dans-les-etablissements-scolaires-impossible"
                ]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        """
        Finds the total number of pages in a listing page.

        Args:
        parsed_listing_page (BeautifulSoup): The BeautifulSoup object representing the parsed listing page.

        Returns:
        int: The total number of pages in the listing.

        """
        paginaltion_nav = parsed_listing_page.find("nav", attrs={'id': 'pagination'})

        last_li_href = list(paginaltion_nav.select(".page-link-desktop"))[-1]['href']
        page_matcher = re.match("^.*page=([0-9]+)$", last_li_href)
        last_page_number = page_matcher.group(1)
        return int(last_page_number)

    def extract_urls(self, parsed_listing_page):
        """
        Extracts claim URLs from the parsed listing page.

        Args:
        parsed_listing_page: The BeautifulSoup object representing the parsed listing page.

        Returns:
        List[str]: A list of URLs of claims.

        """
        urls = list()
        featured_post = parsed_listing_page.find('div', attrs={'class': 'featured-post'})
        if featured_post is None:
            featured_post = parsed_listing_page.find('main')
        cards = featured_post.select(".card")
        for card in cards:
            url = card.find("a")['href']
            urls.append(self.base_url + url)

        return urls

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> List[
        str]:
        """
        Retrieves URLs of claims from multiple listing pages.

        Args:
        parsed_listing_page (BeautifulSoup): The BeautifulSoup object representing the parsed listing page.
        listing_page_url (str): The URL of the listing page.
        number_of_pages (int): The total number of listing pages.

        Returns:
        List[str]: A list of URLs of claims from all listing pages.

        """
        urls = self.extract_urls(parsed_listing_page)
        for page_number in trange(1, number_of_pages):
            #if ((page_number*15) + 14 >= self.configuration.maxClaims):
                #break
            url = listing_page_url + "?page=" + str(int(page_number))
            page = caching.get(url, headers=self.headers, timeout=20)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls += self.extract_urls(current_parsed_listing_page)

        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        """
        Extracts fact-checking claims and their reviews from the parsed claim review page.

        Args:
        parsed_claim_review_page (BeautifulSoup): The BeautifulSoup object representing the parsed claim review page.
        url (str): The URL of the claim review page.

        Returns:
        List[Claim]: A list of Claim objects containing the extracted fact-checking claims and reviews.

        """
        claim = Claim()

        data = parsed_claim_review_page.find(string=re.compile("schema.org"))
        data = json.loads(str(data))

        node_zero = data['@graph'][0]

        if node_zero and 'claimReviewed' in node_zero.keys():
            claim_str = node_zero['claimReviewed']
            if claim_str and len(claim_str) > 0:
                claim.set_claim(claim_str)
                #print("test")
            else:
                return []
        #claim review rating
        rating = data['@graph'][0]['reviewRating']
        print(rating)
    
        if rating and 'alternateName' in rating.keys():
            claim.set_rating(rating['alternateName'])
            try:
                claim.set_best_rating(rating['bestRating'])
                claim.set_worst_rating(rating['worstRating'])
                if type(rating['ratingValue']) is list: #changes
                    claim.set_rating_value(rating['ratingValue'][0])
                        
                else:
                    claim.set_rating_value(rating['ratingValue'])
                
                
                
            except Exception:
                pass
        else:
            return []

        if 'author' in data['@graph'][0]['itemReviewed'].keys():
            author = data['@graph'][0]['itemReviewed']['author']
            if author and 'name' in author.keys():
                if len(str(author['name'])) > 0:
                     #creative work author
                   
                    if type(author['name']) is list:
                        claim.set_author(author['name'][0])
                        
                    else:
                        claim.set_author(author['name'])
                       
                    

        claim.set_url(url)
        claim.set_source("factual_afp")

        try:
            title = data['@graph'][0]['name']
            claim.set_title(title)
        except Exception:
            pass

        try: #creative work date
            claim.set_date_published(data['@graph'][0]['itemReviewed']['datePublished'])
        except Exception:
            pass
        except KeyError:
            pass

        try: #claim review date
            date = data['@graph'][0]['datePublished']
            claim.set_date(date.split(' ')[0])
        except Exception:
            pass
        try:        
            body = parsed_claim_review_page.find('div', {'class': 'article-entry clearfix'})
            claim.set_body(body.text)
        except Exception:
            pass
      
        
        #claim review author
                
        review_author = parsed_claim_review_page.find('span', {"class": "meta-author"})
        for text in review_author:
            #print(text.get_text())
            claim.set_review_author(review_author.text.split(",")[0])
            print(claim.review_author)
        
        
        links = []
        children = parsed_claim_review_page.find('div', {'class': 'article-entry clearfix'}).children
        for child in children:
            try:
                if child.name == 'aside':
                    continue
                if (child != "\n" and not " " ):
                    elems = child.findAll('a')
                    for elem in elems:
                        links.append(elem['href'])
            except Exception as e:
                continue
        claim.set_refered_links(links)
        
        return [claim]
