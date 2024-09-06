# Description: This program extracts text from a PDF file and writes it into an Excel worksheet.
# The text is split into parts based on the Excel cell limit (32,767 characters) without cutting off words.
# The program uses the PyPDF2 library to extract text from the PDF file and the openpyxl library to write text into the Excel worksheet.
# The main function takes the PDF file path and the Excel file path as input arguments and executes the program.
# The program also includes a function to calculate the length of the text extracted from the PDF file.
# The program uses a configuration file (config.py) to define the paths of the PDF and Excel files.
# Created by:  Dinuru Seniya - 4633587

import PyPDF2, openpyxl, os, config

# Get current directory path
dir_path = os.path.dirname(os.path.realpath(__file__))

# Specify the PDF file path
pdf_path = dir_path + "\\12943_2023_Article_1854.pdf"

# Function to split text based on Excel cell limit (32,767 characters) without cutting off words
def split_text(text, limit=32767):
    parts = []
    while len(text) > limit:
        split_point = text[:limit].rfind(' ')
        if split_point == -1:
            split_point = limit
        parts.append(text[:split_point])
        text = text[split_point:].strip()
    parts.append(text)
    return parts

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
    return full_text

def get_pdf_text_length(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        print(f'The length of the text in the PDF is: {len(text)} characters')

# Function to write text parts into an Excel worksheet
def write_text_to_excel(text_parts, output_path):
    workbook = openpyxl.load_workbook(output_path)
    worksheet = workbook['articles']
    row = 2 #assuming the first row is the header, full text is at column 2
    while worksheet.cell(row=row, column=2).value is not None: # find next empty row
        row += 1
    for part in text_parts:
        if part.strip():
            worksheet.cell(row=row, column=2).value = part
            row += 1
    workbook.save(output_path)    
    print(f"Data written to {output_path}")

# Main function to execute the program
def main(pdf_path, excel_path):
    full_text = extract_text_from_pdf(pdf_path)
    get_pdf_text_length(pdf_path)
    text_parts = split_text(full_text)
    write_text_to_excel(text_parts, excel_path)

# Run the program
main(pdf_path, config.myexcelfile)
