from typing import Dict


class Claim:
    """
    Class representing a fact-checking claim.

    Attributes:
        source (str): The name of the fact-checking site, should match the name of the extractor.
        claim (str): The text of the claim (almost always different from the title of the page!).
        body (str): Text of the claim review extracted from the fact-checking site.
        referred_links (str): Links that appear in the body of the claim review in support of various statements.
        title (str): Title of the claim review page, often different from the claim, e.g. a reformulation with more context.
        date (str): Date on which the claim review was written.
        url (str): URL of the claim review (mandatory).
        tags (str): List of tags/keywords extracted from the fact-checking site when available, strings separated by commas.
        author (str): Name of the author of the claim (the claimer).
        author_url (str): Webpage URL associated with the author of the claim review.
        date_published (str): Date on which the claim was made. Not always available in fact-checking sites.
                             Often extracted from free text. Optional, but please include it if the information is available in the fact-checking site.
        same_as (str): URL of claim reviews that are marked as identical. Only for fact-checking sites that have a list of associated claim reviews. Optional.
        rating_value (str): Numerical value for the truth rating, only for fact-checking sites that include this information in the meta tags following the schema.org specification. Optional.
        worst_rating (str): Numerical value for the worst rating on the scale, only for fact-checking sites that include this information in the meta tags following the schema.org specification. Optional.
        best_rating (str): Numerical value for the best rating on the scale, only for fact-checking sites that include this information in the meta tags following the schema.org specification. Optional.
        rating (str): Truth rating (text) for the claim extracted from the fact-checking site (mandatory).
        claim_entities (str): Named entities extracted from the text of the claim encoded in JSON. Optional and deprecated,
                              this will be done in the claimskg generator.
        body_entities (str): Named entities extracted from the body of the claim review encoded in JSON. Optional and deprecated,
                             this will be done in the claimskg generator.
        keyword_entities (str): Named entities extracted from the keywords associated with the claim review encoded in JSON. Optional and deprecated,
                                this will be done in the claimskg generator.
        author_entities (str): Named entities extracted from the name of the claimer (author of the claim) encoded in JSON. Optional and deprecated,
                               this will be done in the claimskg generator.
        review_author (str): Author of the review of the claim on the fact-checking site (not the claimer!).
        related_links (list): A list of related links associated with the claim.
    """

    def __init__(self):
        """
        Default constructor, see other constructor to build object from dictionary
        """
        self.source = ""
        """The name of the fack checking site, should match the name of the extractor"""

        self.claim = str("")
        """The text of the claim (almost always different from the title of the page!)"""

        self.body = str("")
        """Text of the claim review extracted from the fact checkin site"""

        self.referred_links = ""
        """Links that appear in the body of the claim review in support of various statements."""

        self.title = str("")
        """Titre of the claim review page, often different from the claim, e.g. a reformulation with more context."""

        self.date = ""
        """Date on which the claim review was written"""

        self.url = ""
        """URL of the claim review. Mandatory."""

        self.tags = ""
        """List of tags/keywords extracted from the fact checking site when available, strings separated by commas"""

        self.author = ""
        """Name of the author of the claim (the claimer)."""

        self.author_url = ""
        """Webpage URL associated with the author of the claim review."""

        self.date_published = ""
        """Date on which the claim was made. Not always available in fact checking sites. Often extracted from 
        free text. Optional, but please include it if the information is available in the fact checking site."""

        self.same_as = ""
        """URL of claim reviews that are marked as identical. Only for fact checkin sites that have a list of 
        associated claim reviews. Optional."""

        self.rating_value = ""
        """Numerical value for the truth rating, only for fact checking sites that include this information in the
        meta tags following the schema.org specification. Optional."""

        self.worst_rating = ""
        """Numerical value for worst rating on the scale, only for fact checking sites that include this information in the
        meta tags following the schema.org specification. Optional."""

        self.best_rating = ""
        """Numerical value for best rating on the scale, only for fact checking sites that include this information in the
        meta tags following the schema.org specification. Optional."""

        self.rating = ""
        """Truth rating (text) for the claim extracted from the fact checking site. Mandatory."""

        self.claim_entities = ""
        """Named entities extracted from the text of the claim encoded in JSON, optional and deprecated,
        this will be done in the claimskg generator"""

        self.body_entities = ""
        """Named entities extracted from the body of the claim review encoded in JSON, optional and deprecated,
        this will be done in the claimskg generator"""

        self.keyword_entities = ""
        """Named entities extracted from the keywords associated with the claim review encoded in JSON, optional and deprecated,
        this will be done in the claimskg generator"""

        self.author_entities = ""
        """Named entities extracted from the name of the claimer (author of the claim) encoded in JSON, optional and deprecated,
        this will be done in the claimskg generator"""

        self.review_author = ""
        """Author of the review of the claim on the fact checking site (not the claimer!)"""

        self.related_links = []

    def generate_dictionary(self):
        """
        Converts the attributes of the Claim class into a dictionary format.

        Returns:
        dict: A dictionary containing the attributes and their corresponding values from the Claim class.
        """
        if isinstance(self.referred_links, list):
            self.referred_links = ",".join(self.referred_links)
        dictionary = {'rating_ratingValue': self.rating_value, 'rating_worstRating': self.worst_rating,
                      'rating_bestRating': self.best_rating, 'rating_alternateName': self.rating,
                      'creativeWork_author_name': self.author, 'creativeWork_datePublished': self.date_published,
                      'creativeWork_author_sameAs': self.same_as, 'claimReview_author_name': self.source,
                      'claimReview_author_url': self.author_url, 'claimReview_url': self.url,
                      'claimReview_claimReviewed': self.claim, 'claimReview_datePublished': self.date,
                      'claimReview_source': self.source, 'claimReview_author': self.review_author,
                      'extra_body': self.body.replace("\n", ""), 'extra_refered_links': self.referred_links,
                      'extra_title': self.title, 'extra_tags': self.tags,
                      'extra_entities_claimReview_claimReviewed': self.claim_entities,
                      'extra_entities_body': self.body_entities, 'extra_entities_keywords': self.keyword_entities,
                      'extra_entities_author': self.author_entities, 'related_links': ",".join(self.related_links)}
        return dictionary

    @classmethod
    def from_dictionary(cls, dictionary: Dict[str, str]) -> 'Claim':
        """
        Build claim instance from dictionary generated by the generate_dictionary method, mainly used for round tripping
        from cache.
        :param dictionary: The dictionary generated by generate_dictionary
        """
        claim = Claim()
        if 'claimReview_author_name' in dictionary.keys():
            claim.source = dictionary['claimReview_author_name']
        else:
            claim.source = ""
        claim.claim = dictionary["claimReview_claimReviewed"]
        claim.body = dictionary['extra_body']
        claim.referred_links = dictionary['extra_refered_links']
        claim.title = dictionary['extra_title']
        claim.date = dictionary['claimReview_datePublished']
        claim.url = dictionary['claimReview_url']
        claim.tags = dictionary['extra_tags']
        claim.author = dictionary['creativeWork_author_name']
        claim.date_published = dictionary['creativeWork_datePublished']
        claim.same_as = dictionary['creativeWork_author_sameAs']
        claim.author_url = dictionary['claimReview_author_url']
        claim.rating_value = dictionary['rating_ratingValue']
        claim.worst_rating = dictionary['rating_worstRating']
        claim.best_rating = dictionary['rating_bestRating']
        claim.rating = dictionary['rating_alternateName']
        claim.related_links = dictionary['related_links']
        claim.review_author = dictionary['claimReview_author']
        claim.keyword_entities = dictionary['extra_entities_keywords']
        #print(claim.source)
        #print(claim.tags)
        #print(claim.review_author)

        return claim

    def set_rating_value(self, string_value):
        """
        Set the numerical value for the truth rating of the claim.

        Args:
        string_value (str): Numerical value for the truth rating.

        Returns:
        Claim: The current Claim object.

        """
        if string_value:
            string_value = str(string_value).replace('"', "")
            self.rating_value = string_value
        return self

    def set_worst_rating(self, str_):
        """
        Set the numerical value for the worst rating on the scale.

        Args:
        str_ (str): Numerical value for the worst rating.

        Returns:
        Claim: The current Claim object.

        """
        if str_:
            str_ = str(str_).replace('"', "")
            self.worst_rating = str_
        return self

    def set_best_rating(self, str_):
        """
        Set the numerical value for the best rating on the scale.

        Args:
        str_ (str): Numerical value for the best rating.

        Returns:
        Claim: The current Claim object.

        """
        if str_:
            str_ = str(str_).replace('"', "")
            self.best_rating = str_
        return self

    def set_rating(self, alternate_name):
        """
        Set the truth rating (text) for the claim.

        Args:
        alternate_name (str): Truth rating text.

        Returns:
        Claim: The current Claim object.

        """
        self.rating = str(alternate_name).replace('"', "").strip()
        # split sentence

        if "." in self.rating:
            split_name = self.rating.split(".")
            if len(split_name) > 0:
                self.rating = split_name[0]

        return self

    def set_source(self, str_):
        """
        Set the name of the fact-checking site (source) for the claim.

        Args:
        str_ (str): The name of the fact-checking site.

        Returns:
        Claim: The current Claim object.

        """
        self.source = str_
        return self

    def set_author(self, str_):
        """
        Set the name of the claimer (author of the claim).

        Args:
        str_ (str): The name of the claimer (author of the claim).

        Returns:
        Claim: The current Claim object.

        """
        self.author = str_
        return self

    def set_same_as(self, str_):
        """
        Set the URL of claim reviews that are marked as identical.

        Args:
        str_ (str): URL of claim reviews that are marked as identical.

        Returns:
        Claim: The current Claim object.

        """
        if str_ is not None:
            self.same_as = str_
        return self

    def set_date_published(self, str_):
        """
        Set the date on which the claim review was published.

        Args:
        str_ (str): Date on which the claim review was published.

        Returns:
        Claim: The current Claim object.

        """
        self.date_published = str_
        return self

    def set_claim(self, str_):
        """
        Set the text of the claim.

        Args:
        str_ (str): Text of the claim.

        Returns:
        Claim: The current Claim object.

        """
        self.claim = str(str_).strip()
        return self

    def set_body(self, str_):
        """
        Set the text of the claim review extracted from the fact-checking site.

        Args:
        str_ (str): Text of the claim review.

        Returns:
        Claim: The current Claim object.

        """
        self.body = str(str_).strip()
        return self
        
    def set_review_author(self, str_):
        """
        Set the author of the review of the claim on the fact-checking site (not the claimer).

        Args:
        str_ (str): Author of the review of the claim.

        Returns:
        Claim: The current Claim object.

        """
        self.review_author = str_
        return self

    def set_refered_links(self, str_):
        """
        Set the links that appear in the body of the claim review in support of various statements.

        Args:
        str_ (str): Links in the body of the claim review.

        Returns:
        Claim: The current Claim object.

        """
        self.referred_links = str_
        return self

    def set_title(self, str_):
        """
        Set the title of the claim review page, often different from the claim.

        Args:
        str_ (str): Title of the claim review page.

        Returns:
        Claim: The current Claim object.

        """
        self.title = str(str_).strip()
        return self

    def set_date(self, str_):
        """
        Set the date on which the claim was made.

        Args:
        str_ (str): Date on which the claim was made.

        Returns:
        Claim: The current Claim object.

        """
        self.date = str_
        return self

    def set_url(self, str_):
        """
        Set the URL of the claim review.

        Args:
        str_ (str): URL of the claim review.

        Returns:
        Claim: The current Claim object.

        """
        self.url = str(str_)
        return self

    def set_tags(self, str_):
        """
        Set the list of tags/keywords extracted from the fact-checking site when available.

        Args:
        str_ (str): List of tags/keywords separated by commas.

        Returns:
        Claim: The current Claim object.

        """
        self.tags = str_
        
    def set_keyword_entities(self, str_):
        """
        Set the named entities extracted from the keywords associated with the claim review.

        Args:
        str_ (str): Named entities extracted from keywords encoded in JSON.

        Returns:
        Claim: The current Claim object.

        """
        self.tags = str_

    def add_related_link(self, link):
        """
        Add a related link to the list of related links for the claim.

        Args:
        link (str): Related link to be added.

        Returns:
        None

        """
        self.related_links.append(link)

    def add_related_links(self, links):
        """
        Add multiple related links to the list of related links for the claim.

        Args:
        links (list): List of related links to be added.

        Returns:
        None

        """
        self.related_links.extend(links)


class Configuration:
    """
        Default constructor for Configuration class.

        Initializes the Configuration object with default values for various settings.

    """

    def __init__(self):
        self.maxClaims = 0
        """int: The maximum number of claims to extract. Default is 0 (extract all)."""

        self.within = "15mi"
         """str: The time window within which to extract claims. Default is "15mi" (15 minutes)."""

        self.output = "output.csv"
        """str: The output file path for storing extracted claims. Default is "output.csv"."""

        self.website = ""
        """str: The name of the fact-checking site to extract claims from. Default is an empty string."""

        self.until = None
        """str: The date until which to extract claims. Default is None (extract claims up to the present date)."""

        self.since = None
        """str: The date since which to extract claims. Default is None (extract claims from the beginning)."""

        self.html = False
        """bool: Whether to extract claims in HTML format. Default is False."""

        self.entity = False
        """bool: Whether to include named entity recognition in claim extraction. Default is False."""

        self.input = None
        """str: The input file path for claims extraction. Default is None."""

        self.rdf = None
        """str: The path to an RDF file. Default is None."""

        self.avoid_urls = []
        """list: List of URLs to avoid during claim extraction. Default is an empty list."""

        self.update_db = False
        """bool: Whether to update the database. Default is False."""

        self.entity_link = False
        """bool: Whether to include entity links in claim extraction. Default is False."""

        self.normalize_credibility = True
        """bool: Whether to normalize credibility scores. Default is True."""

        self.parser_engine = "lxml"
         """str: The parser engine to use for HTML parsing. Default is "lxml"."""

        self.annotator_uri = "http://localhost:8090/service/"
        """str: The URI for the annotator service. Default is "http://localhost:8090/service/"."""


    def setSince(self, since):
        """
        Set the date since which to extract claims.

        Args:
        since (str): Date since which to extract claims.

        Returns:
        Configuration: The current Configuration object.

        """
        self.since = since
        return self

    def setUntil(self, until):
        """
        Set the date until which to extract claims.

        Args:
        until (str): Date until which to extract claims.

        Returns:
        Configuration: The current Configuration object.

        """
        self.until = until
        return self

    def setMaxClaims(self, maxClaims):
        """
        Set the maximum number of claims to extract.

        Args:
        maxClaims (int): Maximum number of claims to extract.

        Returns:
        Configuration: The current Configuration object.

        """
        self.maxTweets = maxClaims
        return self

    def setOutput(self, output):
        """
        Set the output file path for the extracted claims.

        Args:
        output (str): Output file path for the extracted claims.

        Returns:
        Configuration: The current Configuration object.

        """
        self.output = output
        return self
    
    def setOutputDev(self, output):
        """
        Set the output file path for the development dataset (sampled from the extracted claims).

        Args:
        output (str): Output file path for the development dataset.

        Returns:
        Configuration: The current Configuration object.

        """
        self.output_dev = output
        return self

    def setOutputSample(self, output):
        """
        Set the output file path for the sampled claims dataset.

        Args:
        output (str): Output file path for the sampled claims dataset.

        Returns:
        Configuration: The current Configuration object.

        """
        self.output_sample = output
        return self

    def set_website(self, website):
        """
        Set the website name for which to extract claims.

        Args:
        website (str): Name of the website for claim extraction.

        Returns:
        Configuration: The current Configuration object.

        """
        self.website = website
        return self
