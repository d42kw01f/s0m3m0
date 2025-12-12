import os
import ast
from typing import NoReturn, Dict

from dotenv import load_dotenv

from prediction.the_poli import (
    load_model,
    politicalIncClassifier,
    CLASS_NAMES,
    MAX_LEN,
)
from prediction.hela_processor import HelakuruScraperProcessor
from database import get_db_client

# Load environment variables
load_dotenv(dotenv_path='.env')

# Model paths and labels from environment variables
THE_POLI_MODEL_PATH: str = os.getenv("THE_POLI_MODEL_PATH", "")
THE_POLI_CONFIG_PATH: str = os.getenv("THE_POLI_CONFIG_PATH", "")
THE_CANDI_MODEL_PATH: str = os.getenv("THE_CANDI_MODEL_PATH", "")
DB_COLLECTION_NAME: str = os.getenv("DB_COLLECTION_NAME", "")
TRANSLATE_URL: str = os.getenv("TRANSLATE_URL", "http://localhost:3000/")
THE_CANDI_LABEL: Dict[int, str] = ast.literal_eval(os.getenv("LABEL", "{}"))


def predict() -> NoReturn:
    # Initialize HelakuruScraperProcessor
    processor = HelakuruScraperProcessor(
        db_client=db_client,
        political_predictor=the_poli_predictor,
        the_candi_dir=THE_CANDI_MODEL_PATH,
        label_dict=THE_CANDI_LABEL,
        tr_url=TRANSLATE_URL
    )
    processor.process()
    print({"message": "Prediction and update completed for unpredicted documents."})


if __name__ == '__main__':
    # Load the political model
    the_poli_model, the_poli_tokenizer, the_poli_device = load_model(
        THE_POLI_MODEL_PATH, THE_POLI_CONFIG_PATH
    )

    # Initialize the political predictor
    the_poli_predictor = politicalIncClassifier(
        model=the_poli_model,
        tokenizer=the_poli_tokenizer,
        device=the_poli_device,
        max_len=MAX_LEN,
        class_names=CLASS_NAMES,
    )

    # Get the database client
    db_client = get_db_client(DB_COLLECTION_NAME)
    print(db_client)

    # Run the prediction process
    predict()
