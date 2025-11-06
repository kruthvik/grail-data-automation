from markdown_pdf import MarkdownPdf, Section

import os

def standardizeFormat(documentId):
    targetFolder = f"./standardized_comments/{documentId}"
    
    for filename in os.listdir(targetFolder):
        if filename.endswith(".md"):
            filePath = os.path.join(targetFolder, filename)
            fileBase = os.path.splitext(filename)[0]
            
            markdown = MarkdownPdf(toc_level=2, optimize=True)
            markdown.add_section(Section(open(filePath, "r", encoding="utf-8").read()))
            markdown.save(f"{targetFolder}/{fileBase}.pdf")
            os.remove(filePath)
    
if __name__ == "__main__":
    docId = input("Enter document id: ")
    standardizeFormat(docId)