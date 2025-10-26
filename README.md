Python Selenium and data analysis code to automate the process of data collection for the GRAIL Project. You need to setup Google Cloud to run main.py.

make sure to create metadata, logs, and comments folder

`main.py` -> retrieves AI-related notices that are requests for information/comments and adds them to the spreadsheet

`fetchComments.py` -> enter doc ID to get all comments as PDFs in the appropriate naming conventions. make sure to have a comments folder

`fetchPDF.py` -> backend to download / save the PDFs

`analyzeComment.py` -> analyzes one specific comment that was previously scraped (needs metadata)

`analyzeComments.py` -> analyzes all comments and adds them to spreadsheet

**NOTE** 
To use the comment analysis files, you need to have an Ollama cloud account.
