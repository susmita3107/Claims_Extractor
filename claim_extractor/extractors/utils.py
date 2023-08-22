import unicodedata
import re

def clean_string(_str):
    """
    Cleans a given input string by performing various operations like normalizing Unicode characters,
    removing extra spaces, and unwanted characters.

    Parameters:
        _str (str): The input string to be cleaned.

    Returns:
        str: The cleaned string after applying the cleaning operations.

    Example:
        >>> clean_string(' Last winter, tens of thousands of sick patients waited on A&E trolleys.')
        'Last winter, tens of thousands of sick patients waited on A&E trolleys.'
    """
    cleaned_str = unicodedata.normalize("NFKC", _str).strip()

    cleaned_str = re.sub(r"\n[\s]*[\n]+", "\n", cleaned_str)
    cleaned_str = re.sub(r"\t[\s]*[\t]+", " ", cleaned_str)
    cleaned_str = cleaned_str.replace('\n ', '\n')
    cleaned_str = cleaned_str.replace('\t ', ' ')
    cleaned_str = cleaned_str.replace('\'', "'")
    cleaned_str = cleaned_str.replace('"', '')
    cleaned_str = cleaned_str.replace("'", '')
    cleaned_str = cleaned_str.replace("“", '')
    cleaned_str = cleaned_str.replace("”", '')
    cleaned_str = cleaned_str.replace("‘", '')
    cleaned_str = cleaned_str.replace("’", '')
    cleaned_str = re.sub(' +', ' ', cleaned_str)
    cleaned_str = cleaned_str.strip()

    return cleaned_str



clean_string(' Last winter, tens of thousands of sick patients waited on A&E trolleys.')