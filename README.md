# MarkItDown
This MarkItDown program can mark down different types of files (including .pdf, .xsls, .csv, .json, .docx and others)
Some .pdf files had a problem with marking them down since it was a scanned version of a document (not a digital document). To solve this problem, the OCR mechanism was implemented into the program. 
The MarkItDown extension supports different languages, this addition solves the problem of OCR’ing the file in Chinese. The program creates two folders – one main folder (MD_All) and one additional folder (OCR_All). The marked down files are located in MD_All folder. Since photos, logos and some special digits can not be represent using basic English or/and Chinese alphabet, they are written down as random words made of random letters and/or numbers, special characters (! ? . , etc.), therefore to ensure the correctness of the MD file, the folder OCR_All was created. If there is a question about content in marked down file, a person can check the OCR file. All the marked down files have the same name as the original files. 
#How to run the program:
1. You can download code or copy this repo straight to your compiler
2. Ensure that you have installed correct version of python and download all the neccesary depndencies
```console pip install markitdown pdf2markdown4llm ocrmypdf```
3. Now you can run the code
