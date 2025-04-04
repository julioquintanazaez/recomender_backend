import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('stopwords')


# model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')
def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-zA-Záéíóúñ\s]', '', texto)
    texto = re.sub(r'\W+', ' ', texto)
    tokens = word_tokenize(texto)
    stop_words = set(stopwords.words('spanish'))
    words = [word for word in tokens if word not in stop_words]
    stemmer = SnowballStemmer('spanish')
    words_stem = [stemmer.stem(word) for word in words]
    return ' '.join(words_stem)

def crear_matrix_tfidf(df):
    df['descripcion_limpia'] = df['desc_producto'].apply(limpiar_texto)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['descripcion_limpia'])
    return tfidf_matrix, vectorizer

def calcular_similitud(tfidf_matrix):
    return cosine_similarity(tfidf_matrix, tfidf_matrix)

def obtener_indices_similares(indice_producto, similitud_matrix, top_n=5):
    similitudes = similitud_matrix[indice_producto]
    indices_similares = similitudes.argsort()[::-1]
    indices_similares = indices_similares[indices_similares != indice_producto] 
    return indices_similares[:top_n]

def recomendar_productos(df, productos_nombres, top_n=5):
    tfidf_matrix, vectorizer = crear_matrix_tfidf(df)
    similitud_matrix = calcular_similitud(tfidf_matrix)
    indices_similares = []
    for producto in productos_nombres:
        indice_producto = df.index[df['nombre_producto'] == producto].tolist()
        indices_recomendados = obtener_indices_similares(indice_producto, similitud_matrix, top_n)
        for item in indices_recomendados:
            if item not in indices_similares:
                indices_similares.append(int(item))
    df.drop("descripcion_limpia", axis=1, inplace=True)
    return df.iloc[indices_similares]
