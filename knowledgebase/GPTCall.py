import requests
import openai 
import pandas as pd

mypath="/Users/mathangikarunakaran/Documents/VU-NMIT/2ndYear/ResearchThesis1_NEF6101/UpdatedCode/Cognitive map graph python program/"
process_knowledge_filename="CMG_article_process_knowledge.xlsx"
process_knowledge_file_fullpath=mypath+process_knowledge_filename

api_key ="" 
# launch vscode from anaconda launcher to have proper environments
def read_api_key(process_knowledge_file_fullpath):    
    df = pd.read_excel(process_knowledge_file_fullpath, sheet_name="knowledge", engine='openpyxl')
    filtered_df = df[(df['knowledge_area'] == "chatgpt_apikey") ]
    if filtered_df.empty: 
        print ("\n Could not read the ChatGPT apikey.\n")   
        return "no_apikey"    
    else:
        api_key=filtered_df.iloc[0]['knowledge']
        return api_key


def ask_chatgpt(myPrompt, myContent,model="gpt-4o",max_tokens=4096,temperature=0.2):
    response_text=ask_chatgpt_online(myPrompt,myContent,model,max_tokens,temperature)
    # response_text=ask_local_llama2(myPrompt,myContent)
    #response_text=ask_huggingface_llama2(myPrompt,myContent)
    
    return  response_text

def ask_chatgpt_online(myPrompt, myContent,model="gpt-4o",max_tokens=4096,temperature=0.2):
    api_key=read_api_key(process_knowledge_file_fullpath)
    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
            'Accept': 'text/event-stream', #'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }    
    msg=[]   

    msg.append({'role': 'user', 'content': myPrompt+myContent})

    data = {
                #'model': 'gpt-4',
                'model': model, # 'gpt-4-1106-preview',
                #'model': 'gpt-3.5-turbo',  # test well then change to gpt-4
                'messages': msg, # f"{prompt} Answer without explanation:" can do it more precise
                'max_tokens': max_tokens, #4096, # Adjust this value to limit the response data
                'temperature': temperature #0.2 # Lower values (e.g., 0.5) will make the output more focused and deterministic, while higher values (e.g., 1.0) will make it more random.
            }
    
    response = requests.post(endpoint, headers=headers, json=data).json()
    if 'choices' in response:
            response_text = response['choices'][0]['message']['content'].strip()   
    else:
            print ('An error occurred while processing your request. Please try again.')
            response_text ="GPT: An error occurred while processing your request. Please try again."    
    return  response_text


def ask_local_llama2(myPrompt, myContent):
    
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
