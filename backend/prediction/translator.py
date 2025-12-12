import re
import requests
import json
import urllib.parse
from typing import Optional


class TextTranslator:
    def __init__(self, tr_url):
        self.url = tr_url

    @staticmethod
    def remove_urls(text: Optional[str]) -> str:
        """
        Removes URLs from the given text.

        :param text: The input text from which URLs need to be removed.
        :return: Text with URLs removed.
        """
        if text is None:
            return ""
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        return url_pattern.sub('', text)

    def translate_text(self, text: Optional[str], source_lang: str = 'auto', target_lang: str = 'en') -> str:
        """
        Translates the given text from source language to target language.

        :param text: The input text to be translated.
        :param source_lang: The source language of the text. Default is 'auto'.
        :param target_lang: The target language for the translation. Default is 'en'.
        :return: The translated text.
        """
        if text is None or text.strip() == "":
            return ""

        # Remove URLs from the text
        text_without_urls: str = TextTranslator.remove_urls(text)

        if text_without_urls.strip() == "":
            return ""

        # Encode the text to make it URL-safe
        encoded_text: str = urllib.parse.quote(text_without_urls, safe='')

        # Construct the URL for the translation API
        lingva_url: str = f"{self.url}/api/v1/{source_lang}/{target_lang}/{encoded_text}"

        try:
            # Send GET request to the translation API
            response: requests.Response = requests.get(lingva_url)
            response.raise_for_status()  # Raise an error if the request was unsuccessful
            translation: str = json.loads(response.text)['translation']
            return translation
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as err:
            print(f"An error occurred: {err}")
        except json.JSONDecodeError:
            print("Failed to decode JSON response")

        # Fallback to returning the original text if translation fails
        return text if text is not None else ""


if __name__ == '__main__':
    the_trans = TextTranslator('http://localhost:3000')
    text = 'ඇයි 2048 නේද සන්වර්ධිත රටක් කරනව කීවෙ.'
    tr_text = the_trans.translate_text(text)
    print(tr_text)
