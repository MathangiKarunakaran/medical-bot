import requests, config 
import pandas as pd
from openai import OpenAI

def get_api_key():    
    df = pd.read_excel(config.process_knowledge_file_fullpath, sheet_name="knowledge", engine='openpyxl')
    filtered_df = df[(df['knowledge_area'] == "chatgpt_apikey") ]
    if filtered_df.empty:    
        print ("\n Could not read the ChatGPT API key.\n")  
        return "no_apikey"      
    else:
        api_key=filtered_df.iloc[0]['knowledge']
        return api_key
    
client = OpenAI(
        api_key=get_api_key()
)


def ask_gpt(myPrompt, myContent):
    response_text=ask_chatgpt_online(myPrompt,myContent)
    # response_text=ask_local_llama2(myPrompt,myContent)    
    return  response_text

def ask_chatgpt_online(myPrompt, myContent):
    msg = [{'role': 'user', 'content': myPrompt + myContent}]

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=msg,
        temperature=0.2)

    if hasattr(response, 'choices') and len(response.choices) > 0:
        response_text = response.choices[0].message.content.strip()
    else:
        response_text = "GPT: An error occurred while processing your request. Please try again."
    
    return response_text


def ask_local_llama2(myPrompt, myContent):
    # Can only be run in VU internal network    
    endpoint = "http://140.159.50.187:5000/v1/chat/completions"    
    headers = {  "Content-Type": "application/json"     }
    history = []

#     user_message = input("> ")
    history.append({"role": "user", "content": myPrompt+myContent})
    data = {
        "mode": "chat",
        "character": "Example",
        "messages": history
    }

    response = requests.post(endpoint, headers=headers, json=data).json()

    if 'choices' in response:
            response_text = response['choices'][0]['message']['content'].strip()   
    else:
            print ('An error occurred while processing your request. Please try again.')
            response_text ="GPT: An error occurred while processing your request. Please try again."    
    history.append({"role": "assistant", "content": response_text})
    return  response_text
