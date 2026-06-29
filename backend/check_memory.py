import chromadb
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "../data/chroma_memory"))
memory_collection = chroma_client.get_or_create_collection(name="advisor_history")

# Pull everything stored in the collection
results = memory_collection.get()

print(f"Number of entries stored: {len(results['ids'])}")
print("---")
for i in range(len(results['ids'])):
    print(f"ID: {results['ids'][i]}")
    print(f"Metadata: {results['metadatas'][i]}")
    print(f"Document (AI recommendation): {results['documents'][i][:100]}...")  # first 100 chars
    print("---")