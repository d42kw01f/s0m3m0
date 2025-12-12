from pymongo import MongoClient

def calculate_candidate_scores():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')  # Update with your MongoDB connection string
    db = client['your_database_name']  # Replace with your database name
    collection = db['esana_scraper']  # Replace with your collection name

    # Initialize scores
    total_scores = {'anura': 0, 'sajith': 0, 'ranil': 0, 'other': 0}

    # Fetch all documents and calculate total weights
    for doc in collection.find():
        candidate_weights = doc.get('pt_the_waiter', {}).get('total_candidate_weights', {})
        for candidate in ['anura', 'sajith', 'ranil', 'other']:
            total_scores[candidate] += candidate_weights.get(candidate, 0)

    # Determine the highest scored candidate
    highest_candidate = max(total_scores, key=total_scores.get)
    highest_score = total_scores[highest_candidate]

    # Return the results
    return total_scores, highest_candidate, highest_score

if __name__ == "__main__":
    scores, top_candidate, top_score = calculate_candidate_scores()
    print(f"Total Scores: {scores}")
    print(f"Highest Scored Candidate: {top_candidate} with Score: {top_score}")
