import requests
import http,json
import openai 
import os
import pandas as pd
from datetime import datetime
from GPTCall import ask_chatgpt 
from SaveExcel_v2 import update_sheet_preserving_format, update_list_sheets_preserving_format

mypath="/Users/mathangikarunakaran/Documents/VU-NMIT/2ndYear/ResearchThesis1_NEF6101/UpdatedCode/Cognitive map graph python program/"
process_knowledge_filename="CMG_article_process_knowledge.xlsx"
process_knowledge_file_fullpath=mypath+process_knowledge_filename

def keyfunction_readme():
    i=i
    # key function steps 
    #-------------------------------------

    # 1.  In mypath folder, there is an excel file called Cognitive Map Graph Processing v3 2024.02.14.xlsx
    # 2.  The excel file has three sheets: articles, paragraphs, and sentences  
        # Sheet name: paragraphs
        #Columns: ['ID', 'Paragraph text', 'url', 'category labels', 'summarised key points in simple sentences', 'processing user', 'processing date']

        #Sheet name: sentences
        #Columns: ['ID', 'paragraph ID', 'CMG Auto with GPT', 'CMG by Human Expert', 'Justification of the correction', 'processing user', 'processing date', 'correction user', 'corrction date']

    # 3. Read the articles to a dataframe called df_article, run through it row by row, call ChatGPT API, 
    #     if the row processed is not yes, then, ask gpt to group it into major paragraphs and sub pagragphs, add to paragraph df
    #      #Columns: Article ID	Full text	url	category labels	processed	processing user	processing date

    # updated on 7/May 2024 
    # 1 read api_key and processing knowledge (promnpt) from an excel file, easier to edit
    # 2. saveExcel to v2, which can save multiple sheets in one call 
    # 3. GPTcall allow parameter to change model, tempearture and max_tokens

def main():
    print ("main function started \n--------------------")
    #myexcelfile=mypath+'\\Parkinson CN knowledge\\Cognitive Map Graph Processing v4 2024.02.21.xlsx'    
    myexcelfile=mypath+'Cognitive Map Graph Processing v2 2024.05.15.xlsx'
    
    #check_excelfile_info(myexcelfile) # print sheet heads
    
    df_paragraphs = pd.read_excel(myexcelfile, sheet_name='paragraphs')
    df_articles = pd.read_excel(myexcelfile, sheet_name='articles')

    row_start=0;    row_end=0 # end is 0 means to the end 
    df_paragraphs, df_articles=group_paragraphs(df_paragraphs,  df_articles, row_start, row_end)

    data_sheets = [('paragraphs', df_paragraphs), ('articles', df_articles)]
    update_list_sheets_preserving_format(myexcelfile, data_sheets)
    # both works
    #update_sheet_preserving_format(myexcelfile, 'paragraphs', df_paragraphs)
    #update_sheet_preserving_format(myexcelfile, 'articles', df_articles)


def check_excelfile_info(myexcelfile):
# check the sheet names and columns in the excel file
     # Iterate through all sheets
    print(myexcelfile)
    xls = pd.ExcelFile(myexcelfile)

    for sheet_name in xls.sheet_names:
        # Read each sheet
        df = pd.read_excel(xls, sheet_name)
        
        # Print the sheet name and its columns
        print(f"Sheet name: {sheet_name}")
        print("Columns:", df.columns.tolist())

def testjson():
    jsonstr="""json {
        "article_label": "Pressure Injuries Overview",
        "paragraphs": [
            {
            "label": "Definition and Causes of Pressure Injuries, Risk Factors for Pressure Injuries",
            "original text": "......"
            },

            {
            "label": "test 4",
            "original text": "......"
            },

        
            {
            "label": "test 3",
            "original text": "....

        """
    return jsonstr

def group_paragraphs_prompt():      
    # no longer use this prompt; read prompts from the knowledge excel file
    myprompt3=\
    """ 1) Group the following article content into paragraphs. 
        2) Each paragraph can have a few labels. Labels represents the category and key info of the article.  
        3) The labels are in a quoted string, using comma to separate different labels. 
        4) Labels should have full meaning, because each paragraph will be processed independently. For example, clinic observation is not a good label;  'Acute kideny injury clinic observation' is a clear label. 
        5) Give json as the output, in this structure  {"article_label": summary label, "paragraphs": [{"label": ****, "original text": ***},{"label": ****, "original text": ***},...]} 
        6) If the content is too long or whatever reason, make sure the json is completed. For example, if your output is limited at 4096 characters, and the contnt has more than that, make sure the output json is properly closed. 
        You can add into the label that the content has not been completed because of the character limits. 
        7) Answer only the json, do not provide other content. My program will parse your returned json. 
        8) Use the same language as the article content.
        
        Here is the article content: """ 
    
    df = pd.read_excel(process_knowledge_file_fullpath, sheet_name="knowledge", engine='openpyxl')
    filtered_df = df[(df['knowledge_area'] == "step1_group_paragraphs") ]
    if filtered_df.empty: 
        myprompt="Could not read the knowledge on step1_group_paragraphs.\n" 
    else:
        myprompt = '\n'.join(filtered_df['knowledge'].astype(str))        
    return myprompt +"\n Here is the article content:"

def group_paragraphs(df_paragraphs,  df_articles, row_start, row_end):
    print("\n group_paragraphs function \n --------------------------------------")
    myprompt=group_paragraphs_prompt()    

    """
    response_text = testjson()
    print(response_text)
    article_id=5
    df_paragraphs, article_label=parse_paragraphs_json(response_text,article_id,df_paragraphs)
    print(article_label)
    """

    if row_end == 0:   row_end = df_articles.index[-1]
    for index in range(row_start, row_end + 1):
        if index > df_articles.index[-1]:  # Check to ensure index is within DataFrame bounds
            break  # Exit the loop if index exceeds the number of rows in the DataFrame

        # Access row by index
        row = df_articles.iloc[index]
        article_id=row['Article ID']
        fulltext = str(row['Full text'])
        processed_flag = row['processed']
        #askgptcontent=myprompt+fulltext


        # Proceed if processed is not 'yes' and fulltext is not empty 
        if processed_flag!='Yes'and fulltext and fulltext.lower() != 'nan':            
            response_text = ask_chatgpt(myprompt, fulltext)
            print("-------response_text-----------------------")
            print(response_text)

            # Update the DataFrame with the response
            df_paragraphs, article_label=parse_paragraphs_json(response_text,article_id,df_paragraphs) 
            df_articles.loc[index, 'processed'] = 'Yes'
            df_articles.loc[index, 'category labels'] = article_label
            df_articles.loc[index, 'json str'] = response_text
        
    return df_paragraphs,df_articles

import re


def find_complete_pairs(json_str):
    match = re.search(r'"article_label":\s*"(.*?)"', json_str)  # the returned string may not have a complete json structure; use re to find the related components
    if match:  summary_label = match.group(1)        
    else:      summary_label ="Summary label not found."

    pattern = r'\{\s*"label"\s*:\s*(?:\[.*?\]|".*?")\s*,\s*"original text"\s*:\s*".*?"\s*\}'
    matches = re.findall(pattern, json_str, re.DOTALL)
    print("here are found maches strings: \n---------------------\n", matches)
    # Attempt to parse each match as JSON directly into dictionaries
    complete_pairs = []
    for match in matches:
        try:
            # Each match is expected to be a valid JSON string
            pair_dict = json.loads(match)
            complete_pairs.append(pair_dict)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from match: {e}")
    
    return complete_pairs, summary_label

def parse_paragraphs_json(response_text, article_id, df_paragraphs):
    completed_pairs, article_label = find_complete_pairs(response_text)

    #print("Found total ", len(completed_pairs), "completed paragraphs in json string.")
    #print ("completed pairs are: ", completed_pairs)
    if df_paragraphs.empty:   last_id = 0
    else:                     last_id = df_paragraphs['ID'].max()
    
    for paragraph in completed_pairs:  # Now 'paragraph' is already a dictionary
        if isinstance(paragraph, dict):
            label = paragraph.get("label", "")
            original_text = paragraph.get("original text", "")
            # Continue processing
        else:
            label = "Unexpected data format error"
            original_text = paragraph
           
        last_id += 1
        new_row = pd.DataFrame({
            'ID': [last_id], 
            'Article ID': [article_id],
            'category labels': [label],
            'Paragraph text': [original_text]
        })
        df_paragraphs = pd.concat([df_paragraphs, new_row], ignore_index=True)
    
    return df_paragraphs, article_label




main()