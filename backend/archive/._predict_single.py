from transformers import BertTokenizer, BertConfig, BertModel
import torch
import torch.nn as nn
import re
import urllib.parse
import requests
import json


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
            padding='max_length',
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
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        return url_pattern.sub('', text)

    @staticmethod
    def translate_text(text, source_lang='auto', target_lang='en'):
        text_without_urls = TextTranslator.remove_urls(text)
        encoded_text = urllib.parse.quote(text_without_urls)
        url = f"http://localhost:3000/api/v1/{source_lang}/{target_lang}/{encoded_text}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return json.loads(response.text)['translation']
        except requests.exceptions.RequestException as err:
            print(f"An error occurred: {err}")
        return text


# Initialize model and tokenizer
model_path = "../../models/the_poli/v0.21/the_poli_v0.21.bin"
config_path = "../../models/the_poli/v0.21/config.json"
MAX_LEN = 512
CLASS_NAMES = ['non-political', 'political']

config = BertConfig.from_json_file(config_path)
bert_model = BertModel(config)
model = RadicalizedClassifier(n_classes=len(CLASS_NAMES), bert_model=bert_model)
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

# Predict on a single text
sentiment_predictor = SentimentPredictor(model, tokenizer, device, MAX_LEN, CLASS_NAMES)
text_translator = TextTranslator()

input_text = "SL vs NZ 1st TEST: ශ්‍රී ලංකා පළමු ඉනිම ලකුණු 305 කට සීමාවෙයි"
translated_text = text_translator.translate_text(input_text)
sentiment = sentiment_predictor.predict(translated_text)
print(f"Predicted sentiment: {sentiment}")
