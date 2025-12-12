from transformers import BertTokenizerFast, BertForSequenceClassification
import torch
import torch.nn.functional as F
from typing import Dict


class CandidatePredictor:
    def __init__(self, model_dir: str, label_dict: Dict[int, str], max_len: int = 128):
        self.model_dir = model_dir
        self.label_dict = label_dict
        self.max_len = max_len

        self.tokenizer = BertTokenizerFast.from_pretrained(f'{self.model_dir}/tokenizer/')
        self.model = BertForSequenceClassification.from_pretrained(f'{self.model_dir}/model/')

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def predict(self, post_text: str) -> Dict[str, float]:
        self.model.eval()
        encoding = self.tokenizer.encode_plus(
            post_text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)

        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probabilities = F.softmax(logits, dim=1).cpu().numpy()[0]

        return {self.label_dict[i]: float(prob) for i, prob in enumerate(probabilities)}

    def top_candidate(self, arti_text: str) -> str:
        candi_score = self.predict(arti_text)
        return max(candi_score, key=candi_score.get)


if __name__ == '__main__':
    MODEL_DIR = '/home/d42kw01f/Documents/dev/s0m3m0/models/the_candi/v0.1'
    LABELS = {0: 'Anura', 1: 'Sajith', 2: 'Ranil', 3: 'Other', 4: 'No One'}

    predictor = CandidatePredictor(model_dir=MODEL_DIR, label_dict=LABELS)

    text = "Why did you say you would make a developed country by 2048"

    candidate_scores = predictor.predict(text)

    print("Candidate probabilities:")
    for candidate, score in candidate_scores.items():
        print(f"{candidate}: {score:.4f}")

    predicted_candidate = predictor.top_candidate(text)
    print(f"\nThe article is most likely about: {predicted_candidate}")
