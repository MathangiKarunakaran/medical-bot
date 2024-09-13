import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import os, config, time
from GPTCall import ask_gpt
from SaveExcel_v2 import update_sheet_preserving_format

# key function steps 
#-------------------------------------

# 1.  In mypath folder, there is an excel file called Cognitive Map Graph Processing v3 2024.02.14.xlsx
# 2.  The excel file hastwo sheets, one are paragraphs, and one are cognitive map graph sentences 
    # Sheet name: paragraphs
    #Columns: ['ID', 'Paragraph text', 'url', 'category labels', 'summarised key points in simple sentences', 'processing user', 'processing date']

    #Sheet name: sentences
    #Columns: ['ID', 'paragraph ID', 'CMG Auto with GPT', 'CMG by Human Expert', 'Justification of the correction', 'processing user', 'processing date', 'correction user', 'corrction date']

# 3. Read the original text to a dataframe called df, run through it row by row, call ChatGPT API, 
#     use the following myprompt to summarise the key points of the text:
#     myprompt="1) Summarise the key point, or information/knowledge, of the following text,  
#               2) use simple structrued setnecnes;  3) each sentence should be self contained, avoid using propositions 
#               to refer to entities in ealrier sentences; 4) response in format of  Key Points =  'the key points' " 
# 4. Parse the ChatGPT response to extract the keypoints, and update the keypoints in col4 of the dataframe df 
# 5. For each row in col4, ask chatGPT API to convert the sentences into  head, relation, tail structure. For example, 
#        Acute kidney injury is a rapid decrease in renal function over days to weeks. will be separated into: 
#        Acute kidney injury, is, a rapid decrease in renal function (duration: over days to weeks).  
#     Here we use () to enclose properties of the head, tail or relation. Multiple properties can be separated with comma. 
# 6. Note that a sentence may not have a tail, which can be represented with a -. For example, 
#       Acute kidney injury can be fatal.   can be converted as
#       Acute kidney injury, can be fatal, -. 
# 7. For a sentence with a sub clause, use [] to enclose the main sentence and the sub clause. Use []-(connecting word)-[]. for the converted sentence. 
#      for example,  Tom had AKI when he was 50.  will be converted as 
#                   [Tom, had AKI, -]-(when)-[Tom, was 50, -]
#      note the relationship needs to be meaningful. is, have, get are too short to represent the meaning of the relation. 
# 8. Resonse will be in format of  FCM scripts= ' ****' 
# 9. Extract FCM scripts from the response, and write to col5 of df

def main():
    time_started=time.time()
    print ("Program started \n--------------------")    

    myexcelfile=config.myexcelfile    
    df_paragraphs = pd.read_excel(myexcelfile, sheet_name='paragraphs')
    df_sentences = pd.read_excel(myexcelfile, sheet_name='sentences')

    row_start=0;    row_end=0 # end is 0 means to the end 
    df_paragraphs, df_sentences=summarise_keypoints(df_paragraphs,  df_sentences, row_start, row_end)

    update_sheet_preserving_format(myexcelfile, 'paragraphs', df_paragraphs)
    update_sheet_preserving_format(myexcelfile, 'sentences', df_sentences)

    time_finished=time.time()
    timeused=time_finished-time_started
    print("Time used = {:.0f} minutes {:.2f} seconds".format(timeused // 60, timeused % 60))

def summarise_prompt():    
    df = pd.read_excel(config.process_knowledge_file_fullpath, sheet_name="knowledge", engine='openpyxl')
    filtered_df = df[(df['knowledge_area'] == "step2_summarise_paragraphs") ]
    if filtered_df.empty: 
        myprompt="Could not read the knowledge on step2_summarise_paragraphs.\n" 
    else:
        myprompt = '\n'.join(filtered_df['knowledge'].astype(str))        
    return myprompt +"\n Here is the paragraph:" 
      

def summarise_keypoints(df, df_sentences,row_start, row_end):
    print("\nSummarise_keypoints function \n --------------------------------------")
    myprompt=summarise_prompt()
    
    if row_end == 0:   row_end = df.index[-1]
    for index in range(row_start, row_end + 1):
        if index > df.index[-1]:  # Check to ensure index is within DataFrame bounds
            break  # Exit the loop if index exceeds the number of rows in the DataFrame

        # Access row by index
        row = df.iloc[index]
        mycontent = row['Paragraph text']
        summary = row['summarised key points in simple sentences']
        processedflag=row['processed']

        # Proceed if 'Paragraph text' is not empty and processed is not 'Yes' 
        if processedflag!='Yes' and pd.notna(mycontent)  and mycontent.strip():
            response_text = ask_gpt(myprompt, mycontent)
            print("-------Response_text-----------------------")
            print(response_text)

            # Update the DataFrame with the response
            if response_text == " " or "error" in response_text:  
                # If response_text is erroneous, set 'processed' to 'No' and skip the rest of the loop
                df.at[index, 'processed'] = 'No'
            else:
                df.at[index, 'summarised key points in simple sentences'] = response_text
                paragraph=response_text
                df_sentences=write_summarisedPoints_to_sentence_rows(paragraph,index, df_sentences)
                df.at[index,'processed']='Yes'
                df.at[index, 'processing user'] = os.getlogin()
                df.at[index, 'processing date'] = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
        
    return df,df_sentences


def write_summarisedPoints_to_sentence_rows(paragraph,index, df_sentences):
    print ("\n Split_sentences function index=",index," \n -------------------------------------")
    
    if not df_sentences.empty:
        # If df_sentences is not empty, continue IDs from the last used ID
        sentence_id = df_sentences['Sentence ID'].max() + 1
    else:  sentence_id = 1  # If df_sentences is empty, start IDs from 1

    new_rows = []  # Initialize a list to hold new rows
    paragraph_id = index+1  
    summarised_sentences = paragraph.split('\n')
        
    for sentence in summarised_sentences:
            #print("\n here=", sentence)
            if sentence and sentence.strip():  # Check if the sentence is not just whitespace
                # Create a new row with existing columns, setting default values for unspecified columns
                new_row = {col: '' for col in df_sentences.columns}  # Initialize all columns to default values
                new_row.update({
                    'Sentence ID': sentence_id, 
                    'Paragraph ID': paragraph_id, 
                    'Sentence text': sentence.strip()
                })
                new_rows.append(new_row)
                sentence_id += 1

    # Append new rows to df_sentences DataFrame
    if new_rows:
        df_sentences = pd.concat([df_sentences, pd.DataFrame(new_rows)], ignore_index=True)    
    return df_sentences

main()