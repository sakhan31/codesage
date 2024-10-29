### Inspiration
The motivation behind creating CodeSage stems from the challenges developers often face when navigating unfamiliar codebases or programming languages, especially in large-scale migration projects. New developers or those switching between languages often struggle with understanding existing code structures, tracking files, and rewriting code in a different language. CodeSage was developed to bridge this gap, offering a solution that not only simplifies code exploration and comprehension but also supports seamless language migration, ultimately enhancing productivity and reducing onboarding time for developers.

### What CodeSage Does
CodeSage is an AI-powered application designed to assist developers in understanding and migrating code effortlessly. It allows users to upload programs from their local machines or connect to Azure DevOps repositories, where they can query the code in plain language, request file translations across languages, and download the migrated code. With LangGraph-enabled agent capabilities, CodeSage provides direct interactions with code files for queries, explanations, and migrations—making it an essential tool for developers tackling new codebases or managing complex migration tasks.

### How we built it
We built it using:
1. Code - Databricks Compute Clusters and Notebook
2. Serving - Databricks Model Serving Endpoint and Cluster Driver 
3. Langgraph and LangChain


### Dataset
1. Local Code Bases
2. Azure Devops Repository

