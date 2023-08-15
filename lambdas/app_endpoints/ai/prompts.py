models = {
    "Tax Advisor": {
        "prompt": "Dear AI accountant assistant specialized in answering tax accounting queries, I would greatly appreciate your assistance in addressing the following query. It is essential that your response is highly precise, comprehensive, and of the utmost quality, providing the most accurate and detailed information available. Please provide your response to the query mentioned below:\n{query}"
    },
    "Technical Accounting Advisor": {
        "prompt": "As an AI accountant assistant specialized in answering technical accounting queries, I kindly request your response to the following query, providing the most accurate and comprehensive information: {query}"
    },
    "ASC 842": {"sources": []},
    "IFRS 15": {"sources": []},
    "IFRS 16": {"sources": ["ifrs16"]},
    "IFRS 17": {"sources": ["ifrs17"]},
}


def create_kwip_prompt(
    model: str, query: str, output_format="markdown", gpt_model="gpt-3.5-turbo"
):
    kwip_body = {
        "output_format": output_format,
        "model_name": gpt_model,
    }

    if models[model].get("prompt"):
        kwip_body["prompt"] = models[model]["prompt"].format(query=query)

    if models[model].get("sources"):
        kwip_body["prompt"] = query
        kwip_body["sources"] = models[model]["sources"]

    return kwip_body
