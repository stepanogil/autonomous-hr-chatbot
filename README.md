# Autonomous HR Chatbot built using ChatGPT, LangChain, Pinecone and Streamlit




Companion Reading: [Creating a (mostly) Autonomous HR Assistant with ChatGPT and LangChain’s Agents and Tools](https://medium.com/@stephen.bonifacio/creating-a-mostly-autonomous-hr-assistant-with-chatgpt-and-langchains-agents-and-tools-1cdda0aa70ef)

<br>

### Instructions:

#### How to use this repo:

1. Clone the repo to a local directory  
2. Input your own API keys in the hr_agent_backend.py file  
3. Navigate to the local directory via terminal  
4. Run 'streamlit run hr_agent_frontent.py' in your terminal

#### Storing Embeddings in Pinecone:

1. Create a Pinecone account in [pinecone.io](pinecone.io) - there is a free tier.  Take note of the Pinecone API and environment values.
2. Run the notebook 'store_embeddings_in_pinecone.ipynb'. Replace the Pinecone and OpenAI API keys (for  the embedding model) with your own.


#### Running with a csv file saved locally (does not require Azure Data Lake)

![nodl](img/nodl.png)

#### Running with API keys from from platform.openai.com (and not Azure)
Replace the code blocks below in hr_agent_backend.py with the following openai counterparts.

![openaiapi](img/openaiapi.png)

### Tech Stack:

[Azure OpenAI Service](https://azure.microsoft.com/en-us/products/cognitive-services/openai-service) - the OpenAI service offering for Azure customers.  
[LangChain](https://python.langchain.com/docs/get_started/introduction.html) - development frame work for building apps around LLMs.    
[Pinecone](https://www.pinecone.io/) - the vector database for storing the embeddings.  
[Streamlit](https://streamlit.io/) - used for the front end. Lightweight framework for deploying python web apps.  
[Azure Data Lake](https://azure.microsoft.com/en-us/solutions/data-lake) - for landing the employee data csv files. Any other cloud storage should work just as well (blob, S3 etc).    
[Azure Data Factory](https://azure.microsoft.com/en-ca/products/data-factory/) - used to create the data pipeline.  
[SAP HCM](https://www.sap.com/sea/products/hcm/what-is-sap-hr.html) - the source system for employee data.   

### Author:

### Stephen Bonifacio

Feel free to connect with me on:

Linkedin: https://www.linkedin.com/in/stephenbonifacio/  
Twitter: https://twitter.com/Stepanogil  
Or drop me an email at: stephen.bonifacio@jgsummit.ph
