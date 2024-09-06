import json, os, config, re, time
import pandas as pd
from GPTCall import ask_gpt 
from SaveExcel_v2 import update_list_sheets_preserving_format

# Key function steps 
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
# 1. read api_key and processing knowledge (promnpt) from an excel file, easier to edit
# 2. saveExcel to v2, which can save multiple sheets in one call 
# 3. GPTcall allows parameter to change model, tempearture and max_tokens

    
def main():
    time_started=time.time()
    print ("Program started \n--------------------")   
    myexcelfile=config.myexcelfile
    
    df_paragraphs = pd.read_excel(myexcelfile, sheet_name='paragraphs')
    df_articles = pd.read_excel(myexcelfile, sheet_name='articles')

    row_start=0;    row_end=0 # end is 0 means to the end 
    df_paragraphs, df_articles=group_paragraphs(df_paragraphs,  df_articles, row_start, row_end)

    data_sheets = [('paragraphs', df_paragraphs), ('articles', df_articles)]
    update_list_sheets_preserving_format(myexcelfile, data_sheets)

    time_finished=time.time()
    timeused=time_finished-time_started
    print("Time used = {:.0f} minutes {:.2f} seconds".format(timeused // 60, timeused % 60))

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

def group_paragraphs_prompt(): 
    process_knowledge_file_fullpath=config.process_knowledge_file_fullpath      
    df = pd.read_excel(process_knowledge_file_fullpath, sheet_name="knowledge", engine='openpyxl')
    filtered_df = df[(df['knowledge_area'] == "step1_group_paragraphs") ]
    if filtered_df.empty: 
        myprompt="Could not read the knowledge on step1_group_paragraphs.\n" 
    else:
        myprompt = '\n'.join(filtered_df['knowledge'].astype(str))        
    return myprompt +"\n Here is the article content:"

def group_paragraphs(df_paragraphs,  df_articles, row_start, row_end):
    print("\nRunning group_paragraphs function \n--------------------------------------")
    myprompt=group_paragraphs_prompt()    

    if row_end == 0:   row_end = df_articles.index[-1]
    for index in range(row_start, row_end + 1):
        if index > df_articles.index[-1]:  # Check to ensure index is within DataFrame bounds
            break  # Exit the loop if index exceeds the number of rows in the DataFrame

        # Access row by index
        row = df_articles.iloc[index]
        article_id=row['Article ID']
        fulltext = str(row['Full text'])
        processed_flag = row['processed']

        # Proceed if processed is not 'yes' and fulltext is not empty 
        if processed_flag!='Yes'and fulltext and fulltext.lower() != 'nan':            
            response_text = ask_gpt(myprompt, fulltext)
            print("-------Response_text-----------------------")
            print(response_text)

            # Update the DataFrame with the response
            df_paragraphs, article_label=parse_paragraphs_json(response_text,article_id,df_paragraphs) 
            if response_text == " " or "error" in response_text:  
                # If response_text is erroneous, set 'processed' to 'No' and skip the rest of the loop
                df_articles.loc[index, 'processed'] = 'No'
            else:
                df_articles.loc[index, 'processed'] = 'Yes'
                df_articles.loc[index, 'category labels'] = article_label
                df_articles.loc[index, 'json str'] = response_text
                df_articles.loc[index, 'processing user'] = os.getlogin()
                df_articles.loc[index, 'processing date'] = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
        
    return df_paragraphs,df_articles

def find_complete_pairs(json_str):
    match = re.search(r'"article_label":\s*"(.*?)"', json_str)  # the returned string may not have a complete json structure; use re to find the related components
    if match:  summary_label = match.group(1)        
    else:      summary_label ="Summary label not found."

    pattern = r'\{\s*"label"\s*:\s*(?:\[.*?\]|".*?")\s*,\s*"original text"\s*:\s*".*?"\s*\}'
    matches = re.findall(pattern, json_str, re.DOTALL)
    print("Found matching strings: \n---------------------\n", matches)
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

    print("Found", len(completed_pairs), "completed paragraphs in JSON string.")
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