from database import get_db_client, close_db
import subprocess
import json
import os

single_posts_client = get_db_client("single_posts")
poli_img_client = get_db_client("poli_img")

try:
    poli_img_ids = poli_img_client.collection.distinct('originalPostId')

    query = {
        "imgContent": {
            "$elemMatch": {
                "downloaded": False
            }
        }
    }

    undownloaded_images = single_posts_client.collection.find(query)

    for doc in undownloaded_images:
        doc_json = json.dumps(doc, default=str)  # Convert document to JSON
        print(doc_json)

        for index, img in enumerate(doc['imgContent']):
            image_url = f"https://www.facebook.com{img['url']}"
            print(f"Processing image {index + 1} for document {doc['postId']}")

            file_name = f"{doc['postId']}-{index}.jpg"
            file_path = os.path.join('./downloads', file_name)

            if not os.path.exists('./downloads'):
                os.makedirs('./downloads')

            try:
                # Run the image downloader script with the document JSON
                result = subprocess.run(
                    ['node', '../scrapers/dist/facebook_ImageDownloader.js', doc_json],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    check=True
                )
                print(result.stdout)

                if os.path.exists(file_path):
                    update_result = single_posts_client.collection.update_one(
                        {"postId": doc['postId'], "imgContent.url": img['url']},
                        {"$set": {"imgContent.$.downloaded": True}}
                    )

                    if update_result.modified_count > 0:
                        print(f"Updated downloaded status for image {index + 1} in document {doc['postId']}")
                    else:
                        print(f"Failed to update downloaded status for image {index + 1} in document {doc['postId']}")
                else:
                    print(f"Failed to download image {index + 1} for document {doc['postId']}")

            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")

finally:
    close_db(single_posts_client)
    close_db(poli_img_client)
