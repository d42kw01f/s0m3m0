import os
import torch
import torch.nn as nn
from transformers import BertTokenizer, BertConfig, BertModel
from typing import Tuple
import ast
from typing import NoReturn, Any, Dict

CLASS_NAMES = ['non-political', 'political']
MAX_LEN = 512


class RadicalizedClassifier(nn.Module):
    def __init__(self, n_classes: int, bert_model: BertModel) -> None:
        super(RadicalizedClassifier, self).__init__()
        self.bert = bert_model
        self.drop = nn.Dropout(p=0.5)
        self.out = nn.Linear(self.bert.config.hidden_size, n_classes)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        output = self.drop(output.pooler_output)
        return self.out(output)


class politicalIncClassifier:
    def __init__(self, model: RadicalizedClassifier, tokenizer: BertTokenizer, device: torch.device,
                 max_len: int, class_names: list[str]) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.max_len = max_len
        self.class_names = class_names

    def predict(self, text: str) -> str:
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


def load_model(model_path: str, config_path: str) -> Tuple[RadicalizedClassifier, BertTokenizer, torch.device]:
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

    return model, tokenizer, device


if __name__ == '__main__':
    the_poli_model, the_poli_tokenizer, the_poli_device = load_model(
        '/home/d42kw01f/Documents/dev/s0m3m0/models/the_poli/v0.3/the_poli_v0.3.bin',
        '/home/d42kw01f/Documents/dev/s0m3m0/models/the_poli/v0.3/config.json'
    )
    the_poli_predictor = politicalIncClassifier(
        model=the_poli_model,
        tokenizer=the_poli_tokenizer,
        device=the_poli_device,
        max_len=MAX_LEN,
        class_names=CLASS_NAMES,
    )
    text = "President Ranil emphasizes the importance of AI in education."
    final_result = the_poli_predictor.predict(text)
    print(final_result)

