from langchain_core.documents import Document


doc=Document(
    page_content="this is page content of the doc im using to create RAG",
    metadata={
        "source":"example.txt",
        "pages":1,
        "author":"Krish Naik",
        "date_created":"2026-4-17"   
            
    }
)