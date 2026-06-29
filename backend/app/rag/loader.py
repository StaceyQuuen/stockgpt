import json
from pathlib import Path
from langchain_core.documents import Document


class NewsLoader:

    def load(self, file_path: str):

        path = Path(file_path)

        with open(path, "r", encoding="utf-8") as f:

            data = json.load(f)

        docs = []

        for item in data:

            docs.append(

                Document(

                    page_content=item["content"],

                    metadata={
                        "title": item["title"],
                        "date": item["date"]
                    }

                )

            )

        return docs