import requests
import http,json
import openai 
import os
import pandas as pd
from datetime import datetime, time
import time
from GPTCall import ask_chatgpt
from SaveExcel_v2 import update_sheet_preserving_format, update_list_sheets_preserving_format
mypath="C:/Users/Chhayseng/Desktop/codebase-advancedproject/Cognitive map graph python program/"
process_knowledge_filename="CMG_article_process_knowledge.xlsx"
process_knowledge_file_fullpath=mypath+process_knowledge_filename

def keyfunction_readme():
    i=i
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
    print ("main function started \n--------------------")
    time_started=time.time()

    myexcelfile=mypath+'Cognitive Map Graph Processing v1 2024.08.14.xlsx'      
    #check_excelfile_info(myexcelfile)
    
    df_sentences = pd.read_excel(myexcelfile, sheet_name='sentences')
    row_start=0;       row_end=0 # end is 0 means to the end 
    convertsentence_toCMG(df_sentences,row_start, row_end )

    update_sheet_preserving_format(myexcelfile, 'sentences', df_sentences)

    time_finished=time.time()
    timeused=time_finished-time_started
    print("Time used=", round(timeused,2))


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



def convertCMG_prompt():
    myprompt=""" Convert the sentence into head, relation, tail structure. 
  1) If the sentence has a subclause, convert both the main clause and subclause separately. 
  For example, Very old Tom, who has bad diabetes, suddenly had a big increase in his creatine level.
  Will be converted as: 
  Main clause:  Very old Tom suddenly had a big increase in his creatine level.
  Sub-clause:  Very old Tom, has, bad diabetes.
  Connecting word: who 
  role of the connecting word in the sub-clause: as the subject 
  role of the connecting world in the main clause: describing the subject 
  
  2) Do not provide an explanation. Only response according to what I asked. 

  3) Sometimes, the tail is not a noun. For example, Weak Mary has to breathe over 30 times in a minute.
  It shall be converted into: Weak Mary, who has to breathe over 30 times in a minute.
  Here, the tail is to describe the relation. A similar case is 'John runs very fast.' shall be converted as John runs very fast.  

  4) use the same language as the original sentence. 

  5) It is possible that the relationship is not between the head and tail in the original sentence, but in front of head or behind the tail. You need to understand the meaning of the sentence and convert it accordingly. For example, 
  
  The doctor and patient need to work together to manage the disease.

  Be converted to:   The doctor, need to work together with (purpose: to manage the disease), the patient.

  In this case, the relationship is behind the tail in the original sentence. 
        
Here are more examples:

6) Example

Converting key knowledge points into a cognitive map graph is a principle that requires the conversion to keep the original meaning of the sentence. Compared to the knowledge graph, which uses only the root word, we keep the necessary descriptions and tenses. The tense of the word may carry the meaning of the sentence. For example,

The patient had an obviously unbalanced gait before taking the dopamine.

 In this case, 'obvious' is a word we shall not remove because it indicates that the symptom of Parkinson is strong. The 'had' is the word implies that the symptom is no longer there or at least not as obvious as before.  

In this case, the 'subclause' describes a temporal condition of the relationship. It is not a standard subclause but can be processed as such. 

  Main clause:  The patient, had, obviously unbalanced gait.
  Sub-clause:  Before the patient, taking, the dopamine.
  Connecting word: Before 
  role of the connecting word in the sub-clause: temporal condition, subclause happened first
  role of the connecting world in the main clause: temporal condition, subclause happened first 


        """
    # changed to read prompts from excel file 

    df = pd.read_excel(process_knowledge_file_fullpath, sheet_name="knowledge", engine='openpyxl')
    filtered_df = df[(df['knowledge_area'] == "step3_convert_sentence_to_cognitive_map_graph") ]
    if filtered_df.empty: 
        myprompt="Could not read the knowledge on step3_convert_sentence_to_cognitive_map_graph.\n" 
    else:
        myprompt = '\n'.join(filtered_df['knowledge'].astype(str))        
    return myprompt +"\n Here is the sentence:"


def convertsentence_toCMG(df_sentences,row_start, row_end ):
    print ("convertsentence_toCMG function started \n--------------------")
    myprompt=convertCMG_prompt()
    if row_end == 0:   row_end = df_sentences.index[-1]

    for index in range(row_start, row_end + 1):  # +1 because the range end is exclusive
        if index < len(df_sentences) : # Check to ensure index is within DataFrame bounds
            if df_sentences.at[index, 'processed'] !='Yes': 
                sentence_text = df_sentences.at[index, 'Sentence text']
                response_text = ask_chatgpt(myprompt, sentence_text)
                df_sentences.at[index, 'CMG Auto with GPT'] = response_text
                df_sentences.at[index, 'processed'] = 'Yes'
                
        else:
            break  
    
    return df_sentences
  


main()