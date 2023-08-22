from typing import List
import dateparser
from bs4 import BeautifulSoup, Tag, NavigableString
import ast
import re
from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.extractors.utils import clean_string




class SnopesFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    

    def __init__(self, configuration: Configuration):
        """
        Constructor for the SnopesFactCheckingSiteExtractor class.

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
        return [lambda page_number: f"https://www.snopes.com/fact-check/?pagenum={page_number}"]

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        """
        Extracts fact-check URLs from the parsed listing page.

        Parameters:
            parsed_listing_page (BeautifulSoup): The parsed HTML content of the listing page.

        Returns:
            List[str]: A list of fact-check URLs.
        """
        urls = []
        anchors = parsed_listing_page.findAll("a", {"class": "outer_article_link_wrapper"}, href=True)

        for anchor in anchors:
            url = str(anchor['href'])

            if url not in self.configuration.avoid_urls:
                urls.append(url)

            if self.configuration.maxClaims == len(urls):
                break

        return urls

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
        claim.set_source("snopes")

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
        body_description = self.extract_claim_review_body(parsed_claim_review_page, claim_review_version)
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
        claim_text = self.extract_claim(parsed_claim_review_page, claim_review_version)
        claim.set_claim(claim_text)

        # rating of claim
        rating = self.extract_rating(parsed_claim_review_page, claim_review_version)
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
            str: The version of the claim review page ("v1", "v2", "v3", "v4", "v5", or "could not determine version").
        """
        def _is_v1(page_html: str) -> bool:
            return all(['div class="rating_title_wrap"' in page_html,
                        'div class="claim_cont"' in page_html,
                        'section id="fact_check_rating_container"' in page_html])

        def _is_v2(page_html: str) -> bool:
            return all(["Claim:" in page_html,
                        "Status:" in page_html,
                        "Origins:" in page_html])

        def _is_v3(page_html: str) -> bool:
            return all(["Claim:" in page_html,
                        "Status:" not in page_html,
                        "Origins:" in page_html,
                        '<td valign="CENTER"><img' in page_html])

        def _is_v4(page_html: str) -> bool:
            return all(["Claim:" in page_html,
                        "Status:" not in page_html,
                        "Origins:" in page_html,
                        "[green-label]" in page_html])

        def _is_v5(page_html: str) -> bool:
            return all([">FACT CHECK<" in page_html or ">FACT CHECK:<" in page_html,
                        ">Claim" in page_html,
                        ">Origins" in page_html,
                        "[green-label]" not in page_html])

        version_checks = {
            "v1": _is_v1,
            "v2": _is_v2,
            "v3": _is_v3,
            "v4": _is_v4,
            "v5": _is_v5,
        }

        page_html = str(parsed_claim_review_page)

        for version, check in version_checks.items():
            if check(page_html):
                print(version)
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
            title_element = parsed_claim_review_page.find("section", {"class": "title-container"})
            title_h1 = title_element.find("h1")
            title = title_h1.text
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
            review_author_element = parsed_claim_review_page.find("h3", {"class": "author_name"})
            review_author = review_author_element.text
            review_author = clean_string(review_author)

            if review_author == "":
                review_author = "INFO: No claim review author found"

        except:
            review_author = "ERROR: Error when extracting claim review author"

        return review_author

    def extract_date_claim_review_pub(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
        Extracts the publishing date of the claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.

        Returns:
            str: The publishing date of the claim review in the format "YYYY-MM-DD".
        """
        try:
            date_claim_review_pub_element = parsed_claim_review_page.find("h3", {"class": "publish_date"})
            date_claim_review_pub = date_claim_review_pub_element.text
            date_claim_review_pub = date_claim_review_pub.removeprefix("Published ")
            date_claim_review_pub = dateparser.parse(date_claim_review_pub).strftime("%Y-%m-%d")

            if date_claim_review_pub == "":
                date_claim_review_pub = "INFO: No claim review date found"

        except:
            date_claim_review_pub = "ERROR: Error when extracting claim review date"

        return date_claim_review_pub

    def extract_claim(self, parsed_claim_review_page: BeautifulSoup, version: str) -> str:
        """
        Extracts the claim text from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.
            version (str): The version of the claim review page ("v1", "v2", "v3", "v4", or "v5").

        Returns:
            str: The claim text.
        """
        
        def _extract_claim_v1(parsed_claim_review_page: BeautifulSoup) -> str:
            claim_text_div = parsed_claim_review_page.find("div", {"class": "claim_cont"})
            claim_text = claim_text_div.text
            claim_text = clean_string(claim_text)

            return claim_text

        def _extract_claim_v2345(parsed_claim_review_page: BeautifulSoup) -> str:
            claim_text = ""
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})
            for child_element in article_content.children:
                if ">Claim<" in str(child_element) or ">Claim:<" in str(child_element) or "]Claim" in str(child_element):
                    if isinstance(child_element, Tag):
                        claim_text = child_element.text
                    elif isinstance(child_element, NavigableString):
                        claim_text = str(child_element)

                    claim_text = re.sub("\[\/*(\w|-)+\]", "", claim_text)
                    claim_text = [text for text in claim_text.split('\n') if any(["Claim:" in text, "Claim" in text])][0]
                    claim_text = claim_text.split('\xa0')[-1]
                    claim_text = clean_string(claim_text)

            return claim_text

        try:
            if version == "v1":
                claim_text = _extract_claim_v1(parsed_claim_review_page)
            elif version in ["v2", "v3", "v4", "v5"]:
                claim_text = _extract_claim_v2345(parsed_claim_review_page)
            else:
                claim_text = f"ERROR: Don't know how to extract claim"

            if claim_text == "":
                claim_text = f"INFO: no claim found with {version}"

        except:
            claim_text = f"ERROR: Error when extracting claim with {version}"

        return claim_text

    def extract_rating(self, parsed_claim_review_page: BeautifulSoup, version: str) -> str:
        """
        Extracts the rating of the claim from the claim review page.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.
            version (str): The version of the claim review page ("v1", "v2", "v3", "v4", or "v5").

        Returns:
            str: The rating of the claim.
        """
        

        def _extract_rating_v1(parsed_claim_review_page: BeautifulSoup) -> str:
            rating_element = parsed_claim_review_page.find('div', {"class": "rating_title_wrap"})
            rating = rating_element.text.replace('About this rating', '').strip()
            return rating

        def _extract_rating_v2(parsed_claim_review_page: BeautifulSoup) -> str:
            rating = ""
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})
            paragraphs = article_content.select("p")
            for p in paragraphs:
                if "Status:" in p.text:
                    rating = p.text.strip()
                    rating = rating.split('\xa0')[-1].replace(".", "")
                    break

            return rating

        def _extract_rating_v3(parsed_claim_review_page: BeautifulSoup) -> str:
            rating = ""
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})
            rating_table = article_content.find('table')
            rating_table_cells = rating_table.select('td')
            if len(rating_table_cells) == 2:
                rating = rating_table_cells[1].text.title()

            return rating

        def _extract_rating_v4(parsed_claim_review_page: BeautifulSoup) -> str:
            rating = ""
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})
            paragraphs = article_content.select("p")
            for p in paragraphs:
                if "dot-" in p.text:
                    rating = p.text.strip()
                    rating = rating.split(']')[1].split('[')[0]
                    rating = rating.title()
                    break

            return rating

        def _extract_rating_v5(parsed_claim_review_page: BeautifulSoup) -> str:
            rating = ""
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})
            spans = article_content.select("span")
            for s in spans:
                if any([e.name == "img" for e in s.children]):
                    rating_span = s.find("span")
                    rating = rating_span.text
                    rating = rating.title()
                    break

            return rating

        try:
            if version == "v1":
                rating = _extract_rating_v1(parsed_claim_review_page)
            elif version == "v2":
                rating = _extract_rating_v2(parsed_claim_review_page)
            elif version == "v3":
                rating = _extract_rating_v3(parsed_claim_review_page)
            elif version == "v4":
                rating = _extract_rating_v4(parsed_claim_review_page)
            elif version == "v5":
                rating = _extract_rating_v5(parsed_claim_review_page)
            else:
                rating = f"ERROR: Don't know how to extract rating"

            if rating == "":
                rating = f"INFO: no rating found with {version}"

        except:
            rating = f"ERROR: Error when extracting rating with {version}"

        return rating

    def extract_claim_review_body(self, parsed_claim_review_page: BeautifulSoup, version: str) -> str:
        """
        Extracts the body/description of the claim review.

        Parameters:
            parsed_claim_review_page (BeautifulSoup): The parsed HTML content of the claim review page.
            version (str): The version of the claim review page ("v1", "v2", "v3", "v4", or "v5").

        Returns:
            str: The body/description of the claim review.
        """
        

        def _extract_claim_body_v1(parsed_claim_review_page: BeautifulSoup) -> str:
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})
            body_ps = article_content.find_all('p', recursive=False)
            body_description = " ".join([body_p.text for body_p in body_ps])
            body_description = clean_string(body_description)
            return body_description

        def _extract_claim_body_v23(parsed_claim_review_page: BeautifulSoup) -> str:
            body_description = ""
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})

            after_example_or_origin = False
            after_ad = False
            for child_element in article_content.children:
                if isinstance(child_element, Tag):  # ignore NavigableStrings
                    child_element_text = child_element.text

                    if "Advertisment:" in child_element_text or "Advertisement:" in child_element_text:  # exclude advertisements
                        # print(f"Excluded {child_element_text}")
                        after_ad = True
                        continue

                    if after_ad:  # exclude advertisements
                        # print(f"Excluded {child_element_text}")
                        after_ad = False
                        continue

                    if "Example:" in child_element_text or "Examples:" in child_element_text or "Origins:" in child_element_text:  # only collect text after "Example:"
                        after_example_or_origin = True

                    if after_example_or_origin:  # only collect text after "Example:"
                        if "Last updated:" in child_element_text:  # only collect text until "Last updated:"
                            break

                        body_description = body_description + " " + child_element_text

            body_description = clean_string(body_description)
            return body_description

        def _extract_claim_body_v4(parsed_claim_review_page: BeautifulSoup) -> str:
            body_description = ""
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})

            has_seen_example = False
            after_ad = False
            for child_element in article_content.find_all("p", recursive=True):
                if isinstance(child_element, Tag):  # ignore NavigableStrings
                    child_element_text = child_element.text

                    #remove tags
                    child_element_text = re.sub("\[\/*(\w|-)+\]", "", child_element_text)

                    if "Advertisment:" in child_element_text or "Advertisement:" in child_element_text:  # exclude advertisements
                        # print(f"Excluded {child_element_text}")
                        after_ad = True
                        continue

                    if after_ad:  # exclude advertisements
                        # print(f"Excluded {child_element_text}")
                        after_ad = False
                        continue

                    if "Example:" in child_element_text or "Examples:" in child_element_text:  # only collect text after "Example:"
                        has_seen_example = True

                    if has_seen_example:  # only collect text after "Example:"
                        if "Last updated:" in child_element_text:  # only collect text until "Last updated:"
                            break

                        body_description = body_description + " " + child_element_text

            body_description = clean_string(body_description)
            return body_description

        def _extract_claim_body_v5(parsed_claim_review_page: BeautifulSoup) -> str:
            body_description = ""
            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})

            after_example_or_origin = False
            for child_element in article_content.find_all('p', recursive=True):
                if isinstance(child_element, Tag):  # ignore NavigableStrings
                    child_element_text = child_element.text

                    if "Advertisment:" in child_element_text or "Advertisement:" in child_element_text:  # exclude advertisements
                        # print(f"Excluded {child_element_text}")
                        continue

                    if "Example:" in child_element_text or "Examples:" in child_element_text or "Origins:" in child_element_text:  # only collect text after "Example:"
                        after_example_or_origin = True

                    if after_example_or_origin:  # only collect text after "Example:" or "Origins:"
                        if "Last updated:" in child_element_text:  # only collect text until "Last updated:"
                            break

                        body_description = body_description + " " + child_element_text

            body_description = clean_string(body_description)
            return body_description

        try:
            # remove all script tags from article content
            for script in parsed_claim_review_page.find_all("script", recursive=True):
                script.decompose()

            # remove all style tags from article content
            for style in parsed_claim_review_page.find_all("style", recursive=True):
                style.decompose()

            if version == "v1":
                body_description = _extract_claim_body_v1(parsed_claim_review_page)
            elif version == "v2" or version == "v3":
                body_description = _extract_claim_body_v23(parsed_claim_review_page)
            elif version == "v4":
                body_description = _extract_claim_body_v4(parsed_claim_review_page)
            elif version == "v5":
                body_description = _extract_claim_body_v5(parsed_claim_review_page)
            else:
                body_description = f"ERROR: Don't know how to extract body"

            if body_description == "":
                body_description = f"INFO: no body found with {version}"

        except:
            body_description = f"ERROR: Error when extracting body with {version}"

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
            script_infos = parsed_claim_review_page.select('script')
            categories = []
            tags = []

            for script_info in script_infos:
                if "window.snopes_config" in script_info.text:
                    if 'categories' in script_info.text:
                        categories_str = script_info.text.split('categories')[1].split('],')[0].strip().replace(": ", "") + "]"
                        categories = ast.literal_eval(categories_str)
                        categories = [clean_string(cat) for cat in categories if cat != ""]

                    if 'tags' in script_info.text:
                        tags_str = script_info.text.split('tags')[1].split('],')[0].strip().replace(": ", "") + "]"
                        tags = ast.literal_eval(tags_str)
                        tags = [clean_string(tag) for tag in tags if tag != ""]
                    break

            combined_tags = ":-:".join(categories + tags)

            if combined_tags == "":
                combined_tags = "INFO: No categories or tags found"

        except:
            combined_tags = "ERROR: Error when extracting categories and tags"

        return combined_tags

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

            article_content = parsed_claim_review_page.find("article", {"id": "article-content"})
            for link in article_content.find_all('a', href=True, recursive=True):
                try:
                    if "href" in link.attrs:
                        if "http" in link['href']:
                            referred_links.append(link['href'])
                        else:
                            referred_links.append("https://snopes.com" + link['href'])
                except:
                    continue

            referred_links = list(set(referred_links))
            referred_links = ":-:".join(referred_links)

            if referred_links == "":
                referred_links = "INFO: No referred links found"

        except:
            referred_links = "ERROR: Error when extracting referred links"

        return referred_links
