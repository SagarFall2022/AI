from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI


llm= ChatOpenAI(temperature=0)

class GraderHallunications(BaseModel):
    """Binary Score for hallucination present in the answer."""
    binary_score: bool =Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

structured_llm_grader= llm.with_structured_output(GraderHallunications)

system ="""You are a grader assesing whether an LLM generation is grounded in/ supported by a set of retrieved facts.
Give a binary score 'Yes' or 'No'. 
'Yes' means that the answer is grounded in/ supported by the set of facts.\n
'No' means that the answer is not grounded in/ supported by the set of facts."""

hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "LLM generation: {generation} \n\n Set of facts: \n\n {documents}  "),
    ]

)

hallunciation_grader : RunnableSequence = hallucination_prompt| structured_llm_grader