# Description: This file contains the configuration settings for the project.
# The configuration settings include the paths of the PDF and Excel files used in the program.
# Created by:  Dinuru Seniya - 4633587

import os
import pandas as pd 

#mypath definition
dir_path = os.path.dirname(os.path.realpath(__file__))
mypath=dir_path+"\\"

#process_knowledge_filename definition
process_knowledge_filename="CMG_article_process_knowledge.xlsx"
process_knowledge_file_fullpath=mypath+process_knowledge_filename

#myexcelfile definition
myexcelfile=mypath+'Cognitive Map Graph Processing v1 2024.08.21.xlsx'

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