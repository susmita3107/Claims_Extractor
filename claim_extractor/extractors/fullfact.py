import copy
from typing import List
import dateparser
import contractions
import nltk
from bs4 import BeautifulSoup
from nltk import sent_tokenize, word_tokenize, WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.sentiment.util import mark_negation

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.extractors.utils import clean_string


class FullfactFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    """
    A web scraper to extract fact-checking information from the "Fullfact" website.

    Parameters:
        configuration (Configuration, optional): Configuration options for the web scraper.
        ignore_urls (List[str], optional): List of URLs to ignore during scraping.
        headers (dict, optional): HTTP headers to be used in the web requests.
        language (str, optional): Language code for the content to be scraped (default: 'eng').

    Attributes:
        _conclusion_processor (FullfactConclusionProcessor): An instance of the conclusion processor used for claim rating extraction.

    Methods:
        get_listing_page_formatters(): Returns a list of lambda functions for formatting URLs of different listing pages.
        extract_urls(parsed_listing_page: BeautifulSoup) -> List[str]: Extracts URLs of fact-checking articles from a parsed listing page.
        extract_claim_and_review(parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]: Extracts claim and review details from a parsed fact-checking article page.
        extract_title(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the title of a fact-checking article.
        extract_claim_review_author(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the author of a fact-checking article.
        extract_date_claim_review_pub(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the publishing date of a fact-checking article.
        extract_claim(parsed_claim_review_page: BeautifulSoup) -> List[str]: Extracts the claim text from a fact-checking article.
        extract_rating(parsed_claim_review_page: BeautifulSoup) -> List[str]: Extracts the rating (verdict) from a fact-checking article.
        extract_claim_review_body(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the body content of a fact-checking article.
        extract_tags(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the tags/categories of a fact-checking article.
        extract_referred_links(parsed_claim_review_page: BeautifulSoup) -> str: Extracts the referred links in a fact-checking article.

    """

    def __init__(self, configuration: Configuration = Configuration(), ignore_urls: List[str] = None, headers=None, language="eng"):
        """
        Initialize the FullfactFactCheckingSiteExtractor.

        Parameters:
            configuration (Configuration, optional): Configuration options for the web scraper.
            ignore_urls (List[str], optional): List of URLs to ignore during scraping.
            headers (dict, optional): HTTP headers to be used in the web requests.
            language (str, optional): Language code for the content to be scraped (default: 'eng').
        """
        super().__init__(configuration, ignore_urls, headers, language)
        self._conclusion_processor = FullfactConclusionProcessor()

    def get_listing_page_formatters(self):
        """
        Returns a list of lambda functions used to format URLs of different listing pages.

        Returns:
            List[Callable]: List of lambda functions for formatting URLs of different listing pages.
        """
        base_urls = ["https://fullfact.org/latest/",
                     "https://fullfact.org/health/all/",
                     "https://fullfact.org/economy/all",
                     "https://fullfact.org/europe/all",
                     "https://fullfact.org/crime/all",
                     "https://fullfact.org/law/all",
                     "https://fullfact.org/education/all"]

        return [(lambda page_number, base_url=base_url: f"{base_url}?page={page_number}") for base_url in base_urls]

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        """
        Extracts URLs of fact-checking articles from a parsed listing page.

        Parameters:
            parsed_listing_page (BeautifulSoup): Parsed HTML of the listing page.

        Returns:
            List[str]: List of URLs of fact-checking articles.
        """
        urls = []
        links = parsed_listing_page.findAll("div", {"class": "card"})
        for anchor in links:
            anchor = anchor.find('a', href=True)
            if "http" in anchor['href']:
                url = str(anchor['href'])
            else:
                url = "https://fullfact.org" + str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)

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

        

        # url of factcheck
        claim.set_url(url)

        # source organization
        claim.set_source("fullfact")

        """
        Claim Review
        """
        # title of claim review
        title = self.extract_title(parsed_claim_review_page)
        claim.set_title(title)

        # author of claim review
        review_author = self.extract_claim_review_author(parsed_claim_review_page)
        claim.set_claim_review_author(review_author)

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
        claim_texts = self.extract_claim(parsed_claim_review_page)

        # rating of claim
        ratings = self.extract_rating(parsed_claim_review_page)

        if len(claim_texts) == 1 and len(ratings) == 1:
            claim.set_claim(claim_texts[0])
            claim.set_rating(ratings[0])
            claims = [claim]

        else:# Create multiple claims from the main one and add change then the claim text and verdict (rating):
            claims = []
            if len(claim_texts) != len(ratings):
                print(f"found different amounts of claims and ratings: {url}")
                min_n = min(len(claim_texts), len(ratings))
                claim_texts = claim_texts[:min_n]
                ratings = ratings[:min_n]

            for claim_text, rating in zip(claim_texts, ratings):
                single_claim = copy.deepcopy(claim)
                single_claim.claim = claim_text
                single_claim.rating = rating
                claims.append(single_claim)

        return claims

    def extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the title of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The title of the fact-checking article.
        """
        try:
            article_content = parsed_claim_review_page.find("article")
            title_element = article_content.find('h1')
            title = title_element.text
            title = clean_string(title)

            if title == "":
                title = "INFO: No claim review title found"

        except:
            title = "ERROR: Error when extracting claim review title"

        return title

    def extract_claim_review_author(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the author of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The author of the fact-checking article.
        """
        try:
            article_content = parsed_claim_review_page.find("article")
            author_cites = article_content.select('section.social-media > div > div > ul > li > span > cite')

            author_list = []
            for author_cite in author_cites:
                try:
                    author_list.append(clean_string(author_cite.text))
                except:
                    continue

            review_author = ", ".join(author_list)

            if review_author == "":  # try with other extractor
                publish_element = article_content.find('div', {"class": "published-at"})
                if "|" in publish_element.text:
                    review_author = publish_element.text.split('|')[1]
                    review_author = clean_string(review_author)
            if review_author == "":
                review_author = "INFO: No claim review author found"

        except:
            review_author = "ERROR: Error when extracting claim review author"

        return review_author

    def extract_date_claim_review_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the publishing date of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The publishing date of the fact-checking article in the format "YYYY-MM-DD".
        """
        try:
            article_content = parsed_claim_review_page.find("article")
            date_element = article_content.find('div', {"class": "published-at"})
            date_pub = date_element.text.strip()
            if "|" in date_pub:
                split_date_pub = date_pub.split("|")
                date_pub = split_date_pub[0].strip()

            date_claim_review_pub = dateparser.parse(date_pub).strftime("%Y-%m-%d")

            if date_claim_review_pub == "":
                date_claim_review_pub = "INFO: No claim review date found"

        except:
            date_claim_review_pub = "ERROR: Error when extracting claim review date"

        return date_claim_review_pub

    def extract_claim(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the claim text from a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            List[str]: List of claim texts extracted from the fact-checking article.
        """
        try:
            claim_texts = []

            article_content = parsed_claim_review_page.find("article")
            claim_rating_divs = article_content.find_all("div", {"class": "row no-gutters card-body-text"})
            for claim_rating_div in claim_rating_divs:
                claim_rating_ps = claim_rating_div.find_all("p", recursive=True)
                if len(claim_rating_ps) == 2:
                    claim_text = claim_rating_ps[0].text
                    claim_text = clean_string(claim_text)
                    claim_texts.append(claim_text)

            if len(claim_texts) == 0:
                claim_texts = ["INFO: no claim found"]

        except:
            claim_texts = ["ERROR: Error when extracting claim"]

        return claim_texts

    def extract_rating(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the rating (verdict) from a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            List[str]: List of ratings (verdicts) extracted from the fact-checking article.
        """
        try:
            ratings = []

            article_content = parsed_claim_review_page.find("article")
            claim_rating_divs = article_content.find_all("div", {"class": "row no-gutters card-body-text"})
            for claim_rating_div in claim_rating_divs:
                claim_rating_ps = claim_rating_div.find_all("p", recursive=True)
                if len(claim_rating_ps) == 2:
                    rating = claim_rating_ps[1].text
                    conclusion_text = self._conclusion_processor.extract_conclusion(rating)
                    rating = str(conclusion_text).replace('"', "").strip()
                    if "." in rating:
                        split_name = rating.split(".")
                        if len(split_name) > 0:
                            rating = split_name[0]
                    ratings.append(rating)

            if len(ratings) == 0:
                ratings = ["INFO: no rating found"]

        except:
            ratings = ["ERROR: Error when extracting rating"]

        return ratings

    def extract_claim_review_body(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the body content of a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The body content of the fact-checking article.
        """
        try:
            article_content = parsed_claim_review_page.find("article")

            # remove all script tags from article content
            for script in article_content.find_all("script", recursive=True):
                script.decompose()

            # remove all style tags from article content
            for style in article_content.find_all("style", recursive=True):
                style.decompose()

            body_ps = article_content.find_all('p', recursive=True)
            body_description = " ".join([body_p.text for body_p in body_ps])
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
            breadcrumbs = parsed_claim_review_page.find('nav', {'class':"breadcrumbs"})
            categories_text = clean_string(breadcrumbs.text)
            categories = [clean_string(cat) for cat in categories_text.split('/')]
            categories = ":-:".join(categories)

            if categories == "":
                categories = "INFO: No categories found"

        except:
            categories = "ERROR: Error when extracting categories"

        return categories

    def extract_referred_links(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the referred links in a fact-checking article.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): Parsed HTML of the fact-checking article page.

        Returns:
            str: The referred links in the fact-checking article, separated by ":-:".
        """
        try:
            article_content = parsed_claim_review_page.find("article")

            referred_links = []
            for link in article_content.find_all('a', href=True, recursive=True):
                try:
                    if "facebook.com/sharer" in link['href'] or "twitter.com/intent/tweet?text=" in link['href']:
                        continue

                    if "http" in link['href']:
                        referred_links.append(link['href'])
                    else:
                        referred_links.append("https://www.fullfact.org" + link['href'])
                except Exception:
                    continue

            related_fcs = parsed_claim_review_page.find("section", {"class": "related-factchecks"})

            for link in related_fcs.find_all('a', href=True, recursive=True):
                try:
                    if "http" in link['href']:
                        referred_links.append(link['href'])
                    else:
                        referred_links.append("https://www.fullfact.org" + link['href'])
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


class FullfactConclusionProcessor:
    """
    A class for processing conclusions (verdicts) from fact-checking articles.

    Methods:
        extract_conclusion(conclusion: str) -> str: Extracts the conclusion (verdict) from a fact-checking article.

    """
    def __init__(self):
        self._vocabulary = {"true": ["correct", "right", "true", "evidence", "accurate", "exact"],
                            "false": ["incorrect", "false", "fake", "wrong", "inaccurate", "untrue"],
                            "mixture": ["uncertain", "ambiguous", "unclear", "unsure", "undetermined"],
                            "opposition_words": ["but", "however"],
                            "negation": ["no", "not", "neither", "nor"],
                            "mix_with_neg": ["quite", "necessarily", "sure", "clear"]}

        stop_words = stopwords.words('english')
        self._stop_words = [
            w for w in stop_words if not w in self._vocabulary["negation"]]

        self._punctuation = [".", ",", "!", ";", "?", "'", "\""]

        self._verb_tags = ["MD", "VB", "VBP"]
        self._wordnet_lemmatizer = WordNetLemmatizer()

    # Fonction qui traite les contractions dans les phrases puis les découpe et met leurs termes en minuscule
    @staticmethod
    def _nettoyage(conclusion):
        phrase = sent_tokenize(conclusion)
        phrase[0] = contractions.fix(phrase[0])
        tokens = word_tokenize(phrase[0])
        tokens = [w.lower() for w in tokens]
        return tokens

    # Fonction qui réduit les mots à leurs racines (mett les verbes à l'infinitif, supprime le "s" du pluriel, etc)
    def _lemmatization(self, tempo):
        tempo = [self._wordnet_lemmatizer.lemmatize(
            word, pos='v') for word in tempo]
        return tempo

    def _remove_stopwords(self, tempo):
        tempo = [w for w in tempo if not w in self._stop_words]
        return tempo

    # Fonction qui détecte les cas tels que (it's correct...however)
    def _detect_opposition(self, indice, tempo, n=False):
        new_tempo = tempo[indice + 1:]
        if n:
            sentence = "".join([" " + i for i in new_tempo])
        else:
            sentence = "".join([" " + i[0] for i in new_tempo])

        for m in self._vocabulary["opposition_words"]:
            if m in sentence:
                return True
        return False

    def _direct_extraction(self, words):
        words = [t for t in words if not t in self._punctuation]

        tempo = nltk.pos_tag(words)
        tempoLematise = self._lemmatization(words)
        tempoL = nltk.pos_tag(tempoLematise)
        i = 0
        if tempoL[-1][0] == "not" and (tempoL[-2][1] in self._verb_tags):
            return "False"

        while i < len(tempo):

            if (tempo[i][0] in self._vocabulary["true"] or tempo[i][0] in self._vocabulary["false"]) and i + 1 != len(
                    tempo) and self._detect_opposition(i, tempo):
                return "Mixture"

            if tempo[i][0] in self._vocabulary["false"]:
                return "False"

            if tempo[i][0] in self._vocabulary["true"]:
                return "True"

            if tempo[i][0] in self._vocabulary["mixture"]:
                return "Mixture"

            i += 1
        return "Other"

    def _indirect_negation(self, tempo):
        words = mark_negation(tempo)
        neg = [w.replace("_NEG", "") for w in words if w.endswith("_NEG")]
        i = 0
        for n in neg:
            if (n in self._vocabulary["true"] or n in self._vocabulary["false"]) and i + 1 != len(
                    neg) and self._detect_opposition(i, neg,
                                                     n=True):
                return "Mixture"

            if n in self._vocabulary["mix_with_neg"]:
                return "Mixture"

            if n in self._vocabulary["true"]:
                return "False"

            if n in self._vocabulary["false"]:
                return "True"

            i += 1

        return "Other"

    def extract_conclusion(self, conclusion):
        """
        Extracts the conclusion (verdict) from a fact-checking article.

        Parameters:
            conclusion (str): The conclusion section of the fact-checking article.

        Returns:
            str: The extracted conclusion (verdict) from the fact-checking article.
        """
        words = FullfactConclusionProcessor._nettoyage(conclusion)
        result = self._indirect_negation(words)
        if result == "Other":
            result = self._direct_extraction(words)
        return result
