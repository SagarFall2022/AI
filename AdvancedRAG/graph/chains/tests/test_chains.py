from dotenv import load_dotenv
load_dotenv()
from graph.chains.retrieval_grader import GradeDocuments,retrieval_grader
from graph.chains.generation import generation_chain
from graph.chains.halluncination_grader import hallunciation_grader, GraderHallunications
from ingestion import retriever
from pprint import pprint


def test_retrival_grader_answer_yes() -> None:
    question ="agent memory"
    docs=retriever.invoke(question)
    doc_txt=docs[1].page_content

    res:GradeDocuments=retrieval_grader.invoke(
        {"question": question, 
        "document": doc_txt}
    )
    assert res.binary_score=="yes"

def test_retrival_grader_answer_no() -> None:
    question ="agent memory"
    docs=retriever.invoke(question)
    doc_txt=docs[1].page_content

    res:GradeDocuments=retrieval_grader.invoke(
        {"question": "How to make pizza", 
        "document": doc_txt}
    )
    assert res.binary_score=="no"

def test_generation_chain() -> None:
    question ="agent memory"
    docs=retriever.invoke(question)
    generation = generation_chain.invoke({"context": docs,
                                          "question":question})
    pprint(generation)


def test_hallunication_grader_answer_yes() -> None:
    question="agent memory"
    docs= retriever.invoke(question)
    generation = generation_chain.invoke({"context": docs,
                                          "question":question})
    res: GraderHallunications = hallunciation_grader.invoke(
        {"documents": docs, "generation": generation}
    )
    assert res.binary_score

def test_hallunication_grader_answer_no() -> None:
    question="agent memory"
    docs= retriever.invoke(question)
    generation="one plate Pizza"
    res: GraderHallunications = hallunciation_grader.invoke(
        {
            "documents": docs, 
            "generation": generation,
        }
    )
    assert not res.binary_score, f"Expected res.binary_score to be False, but got {res.binary_score}"