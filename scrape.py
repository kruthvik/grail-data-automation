import requests as req
import csv

"""
This is a simple script to scrape the federal register for documents related to artificial intelligence.

The script will search for documents related to artificial intelligence and write them to a csv file.

The csv file will have the following columns:
    title
    url
    publication date
    document number
    agencies
    
Change the NUM_PAGES and TERMS variables to change the number of pages to search and the terms to search for.

The script will search for documents related to artificial intelligence and write them to a csv file. 

Set the delimiter to ";" to match the csv file when importing.
"""

NUM_PAGES = 50 # Number of pages to search
TERMS=["artificial intelligence", "ai", "machine learning"] # Terms to search for


with open("federalRegister.csv", "w") as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(["Title", "URL", "Publication Date", "Document Number", "Agencies"])

for term in TERMS:
    url = f"https://www.federalregister.gov/api/v1/documents.json?per_page={NUM_PAGES}&order=relevance&conditions[term]={term}&conditions[publication_date][gte]=2021-01-01"
    aRes = req.get(url).json()
    res = aRes["results"]

    searchTerms = [
        "request for ",
        "rfi",
        "rfc",
        "anprms",
        "nprm"
    ]

    res = [i for i in res if any(j in i["title"].lower() for j in searchTerms)]

    with open("federalRegister.csv", "r") as f:
        reader = csv.reader(f, delimiter=';')
        alreadyIncluded = [i for i in reader if len(i) > 0]
        alreadyIncludedTitles = [j[0] for j in alreadyIncluded]
    print(alreadyIncludedTitles)


    for i in res:
        if i["title"] not in alreadyIncludedTitles:
            with open("federalRegister.csv", "a") as f:
                print(i)
                agencies = ", ".join([m["raw_name"] for m in i["agencies"]])
                writer = csv.writer(f, delimiter=';')
                writer.writerow([i["title"], i["html_url"], i["publication_date"], i["document_number"], agencies])
                