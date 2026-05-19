import chromadb

# 1. Create a local database folder
chroma_client = chromadb.PersistentClient(path="./t2_extension/chroma_db")

# 2. Create a "collection" (a table for our embeddings)
collection = chroma_client.get_or_create_collection(name="course_materials")

# 3. Add our specific university knowledge to the database
collection.add(
    documents=[
        "Lab Protocol (TP) Grading Rule: All lab protocols must be submitted via the university portal by Friday at 11:59 PM. Late submissions will receive an automatic 20% deduction from the final grade.",
        "Medallion Architecture Thesis Requirement: All Big Data master's theses must include a Gold Layer dashboard built with Spark Structured Streaming.",
        "Nidam Tayyibat Dietary Rule: Processed sugar is strictly forbidden. Meals should focus on natural, unrefined ingredients."
    ],
    ids=["rule_1", "rule_2", "rule_3"]
)

print("✅ Semantic Memory Database built successfully!")