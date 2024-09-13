import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import os, time, config
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
    df_sentences = pd.read_excel(myexcelfile, sheet_name='sentences')
    row_start=0;       row_end=0 # end is 0 means to the end 
    convertsentence_toCMG(df_sentences,row_start, row_end )

    update_sheet_preserving_format(myexcelfile, 'sentences', df_sentences)

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

def convertCMG_prompt():
    # changed to read prompts from excel file 
    df = pd.read_excel(config.process_knowledge_file_fullpath, sheet_name="knowledge", engine='openpyxl')
    filtered_df = df[(df['knowledge_area'] == "step3_convert_sentence_to_cognitive_map_graph") ]
    if filtered_df.empty: 
        myprompt="Could not read the knowledge on step3_convert_sentence_to_cognitive_map_graph.\n" 
    else:
        myprompt = '\n'.join(filtered_df['knowledge'].astype(str))        
    return myprompt +"\n Here is the sentence:"


def convertsentence_toCMG(df_sentences,row_start, row_end ):
    print ("ConvertSentence_toCMG function started \n--------------------")
    myprompt=convertCMG_prompt()
    if row_end == 0:   row_end = df_sentences.index[-1]

    for index in range(row_start, row_end + 1):  # +1 because the range end is exclusive
        if index < len(df_sentences) : # Check to ensure index is within DataFrame bounds
            if df_sentences.at[index, 'processed'] !='Yes': 
                sentence_text = df_sentences.at[index, 'Sentence text']
                response_text = ask_gpt(myprompt, sentence_text)
                if response_text == " " or "error" in response_text:  
                # If response_text is erroneous, set 'processed' to 'No' and skip the rest of the loop
                    df_sentences.at[index, 'processed'] = 'No'
                else:
                    df_sentences.at[index, 'CMG Auto with GPT'] = response_text
                    df_sentences.at[index, 'processing user'] = os.getlogin()
                    df_sentences.at[index, 'processing date'] = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
                    df_sentences.at[index, 'processed'] = 'Yes'                
        else:
            break     
    return df_sentences

main()