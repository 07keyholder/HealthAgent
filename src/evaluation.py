from langchain.evaluation import load_evaluator
from langchain_google_genai import ChatGoogleGenerativeAI


def evaluate_response(input_query, response):
    """
    Evaluates the agent's response based on a set of criteria.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    evaluator = load_evaluator("labeled_score_string", llm=llm)

    eval_result = evaluator.evaluate_strings(
        prediction=response,
        input=input_query,
        reference="The user is asking a question about a pharmaceutical company. The response should be helpful and relevant to the user's query.",
        criteria={
            "helpfulness": "Is the response helpful to the user?",
            "relevance": "Is the response relevant to the user's query?",
            "correctness": "Is the response factually correct?",
        },
    )
    return eval_result
