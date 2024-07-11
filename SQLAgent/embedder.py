import os
import re
import requests
import logging
from tenacity import retry, wait_random_exponential, stop_after_attempt  
import cohere


class TextEmbedder():

    AZURE_COHERE_EMBEDDING_DEPLOYMENT=os.getenv["AZURE_COHERE_DEPLOYMENT_NAME"]


    def clean_text(self, text):
        # Clean up text (e.g. line breaks, )    
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[\n\r]+', ' ', text).strip()
        return text

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(2))
    def embed_content(self, text, clean_text=True, use_single_precision=True):
        # embedding_precision = 9 if use_single_precision else 18
        if clean_text:
            text = self.clean_text(text)

        cohere_api_key = os.getenv["AZURE_COHERE_API_KEY"]
        cohere_base_url = os.getenv["AZURE_COHERE_SERVICE_NAME"]
        co = cohere.Client(base_url=cohere_base_url,api_key=cohere_api_key) 

        model = self.AZURE_COHERE_EMBEDDING_DEPLOYMENT
        response = co.embed( 
        texts=[text], 
        model=model, 
        input_type="search_document", 
        embedding_types=["int8"], 
        ) 
        embedding = [embedding for embedding in response.embeddings.int8] 

        return embedding[0]
    




