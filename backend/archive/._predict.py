from pymongo import MongoClient
from transformers import BertTokenizer, BertConfig, BertModel
from datetime import datetime, timezone
import torch
import os
import torch.nn as nn
import requests
import json
import re
import urllib.parse


class MongoDBClient:
    def __init__(self, uri, db_name, collection_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def find_unpredicted_docs(self):
        return self.collection.find({
            "$or": [{"pt_the_poli": {"$exists": False}}, {"pt_the_poli": None}]
        })

    def update_doc(self, doc_id, update_fields):
        self.collection.update_one({"_id": doc_id}, {"$set": update_fields})


class RadicalizedClassifier(nn.Module):
    def __init__(self, n_classes, bert_model):
        super(RadicalizedClassifier, self).__init__()
        self.bert = bert_model
        self.drop = nn.Dropout(p=0.5)
        self.out = nn.Linear(self.bert.config.hidden_size, n_classes)

    def forward(self, input_ids, attention_mask):
        output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        output = self.drop(output.pooler_output)
        return self.out(output)


class SentimentPredictor:
    def __init__(self, model, tokenizer, device, max_len, class_names):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.max_len = max_len
        self.class_names = class_names

    def predict(self, text):
        encoded_review = self.tokenizer.encode_plus(
            text,
            max_length=self.max_len,
            add_special_tokens=True,
            return_token_type_ids=False,
            pad_to_max_length=True,
            return_attention_mask=True,
            return_tensors='pt',
        )
        input_ids = encoded_review['input_ids'].to(self.device)
        attention_mask = encoded_review['attention_mask'].to(self.device)

        self.model.eval()
        with torch.no_grad():
            output = self.model(input_ids, attention_mask)
            _, prediction = torch.max(output, dim=1)

        return self.class_names[prediction.item()]


class TextTranslator:
    @staticmethod
    def remove_urls(text):
        if text is None:
            return ""
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        return url_pattern.sub('', text)

    @staticmethod
    def translate_text(text, source_lang='auto', target_lang='en'):
        if text is None or text.strip() == "":
            return ""  # Return empty string for None or empty text

        text_without_urls = TextTranslator.remove_urls(text)

        if text_without_urls.strip() == "":
            return ""

        encoded_text = urllib.parse.quote(text_without_urls)
        url = f"http://localhost:3000/api/v1/{source_lang}/{target_lang}/{encoded_text}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            translation = json.loads(response.text)['translation']
            return translation
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as err:
            print(f"An error occurred: {err}")
        except json.JSONDecodeError:
            print("Failed to decode JSON response")

        return text if text is not None else ""


class FacebookScraperProcessor:
    def __init__(self, db_client, sentiment_predictor, text_translator):
        self.db_client = db_client
        self.sentiment_predictor = sentiment_predictor
        self.text_translator = text_translator

    def process(self):
        unpredicted_docs = self.db_client.find_unpredicted_docs()

        for doc in unpredicted_docs:
            post_text = doc.get("post_text", "")
            translated_text = self.text_translator.translate_text(post_text)

            if translated_text:
                sentiment = self.sentiment_predictor.predict(translated_text)
                final_the_poli = 'political' if sentiment == 'political' else 'non-political'
            else:
                sentiment = "non-political"

            comment_data = []
            if sentiment == 'non-political':
                comments = doc.get("two_comments", [])
                for comment in comments:
                    translated_comment_text = self.text_translator.translate_text(comment)
                    if translated_comment_text:
                        comment_sentiment = self.sentiment_predictor.predict(translated_comment_text)
                        if comment_sentiment == 'political':
                            final_the_poli = 'political'
                    else:
                        comment_sentiment = "non-political"

                    comment_data.append({
                        "original_comment": comment,
                        "translated_comment": translated_comment_text,
                        "comment_sentiment": comment_sentiment
                    })

            update_fields = {
                "post_text_prediction_data": {
                    "prediction": sentiment,
                    "predictedAt": datetime.now(timezone.utc).isoformat(),
                    "tr_post_text": translated_text,
                },
                "comment_prediction_data": comment_data,
                "final_the_poli": final_the_poli
            }

            self.db_client.update_doc(doc["_id"], update_fields)
            print(f"Processed document {doc['_id']}")

        print("Translation, sentiment prediction, and update completed for unpredicted documents.")


# Initialize and load model and tokenizer
model_path = "../../models/the_poli/v0.21/the_poli_v0.21.bin"
config_path = "../../models/the_poli/v0.21/config.json"

# Define constants
MAX_LEN = 512
CLASS_NAMES = ['non-political', 'political']

if not os.path.isfile(model_path) or not os.path.isfile(config_path):
    raise FileNotFoundError("Model or configuration file not found. Please check the paths.")

config = BertConfig.from_json_file(config_path)
bert_model = BertModel(config)
model = RadicalizedClassifier(n_classes=len(CLASS_NAMES), bert_model=bert_model)
state_dict = torch.load(model_path, map_location=torch.device('cpu'))
model.load_state_dict(state_dict)
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

# Dependency Injection
db_client = MongoDBClient(uri="mongodb://localhost:27017/", db_name="fb_scraper", collection_name="page_posts")
sentiment_predictor = SentimentPredictor(model, tokenizer, device, MAX_LEN, CLASS_NAMES)
text_translator = TextTranslator()

# Processing
processor = FacebookScraperProcessor(db_client, sentiment_predictor, text_translator)
processor.process()
