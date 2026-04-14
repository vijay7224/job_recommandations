import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
data = pd.read_csv('jobs.csv')

# 🔥 FIX: Replace NaN with empty string
data['skills'] = data['skills'].fillna('')

vectorizer = TfidfVectorizer()
job_vectors = vectorizer.fit_transform(data['skills'])

def recommend_jobs(user_skills):
    user_vector = vectorizer.transform([user_skills])
    similarity = cosine_similarity(user_vector, job_vectors)
    data['score'] = similarity[0]
    return data.sort_values(by='score', ascending=False).head(5)
