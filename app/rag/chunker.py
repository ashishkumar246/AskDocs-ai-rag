from langchain_text_splitters import RecursiveCharacterTextSplitter


def recursive_chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n•", "\n", ". ", " ", ""]
    )

    return splitter.split_text(text)