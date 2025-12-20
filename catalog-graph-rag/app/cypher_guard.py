FORBIDDEN = ["CREATE","MERGE","DELETE","SET","DROP","CALL","LOAD","APOC","REMOVE"]
REQUIRED = ["MATCH", "RETURN"]

def validate_cypher(query: str):
    q = " ".join(query.split()).upper()
    for bad in FORBIDDEN:
        if bad in q:
            raise ValueError(f"Forbidden Cypher keyword: {bad}")
    for must in REQUIRED:
        if must not in q:
            raise ValueError(f"Cypher must include: {must}")
    if "LIMIT" not in q:
        raise ValueError("Cypher must include a LIMIT")
