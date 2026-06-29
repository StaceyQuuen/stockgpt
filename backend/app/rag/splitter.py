from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextSplitter:

    def __init__(self):

        self.splitter = RecursiveCharacterTextSplitter(

            chunk_size=300,

            chunk_overlap=50

        )


    def split(self, docs):

        return self.splitter.split_documents(docs)