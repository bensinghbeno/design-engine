from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Initialize the Llama model
llm = Ollama(model="llama2")

# Create a prompt template
template = """
You are a helpful assistant. 
Answer the following question: {question}
"""
prompt = PromptTemplate(template=template, input_variables=["question"])

# Create an LLM chain
chain = LLMChain(llm=llm, prompt=prompt)

# Run the chatbot loop
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    response = chain.run(question=user_input)
    print("Bot:", response)