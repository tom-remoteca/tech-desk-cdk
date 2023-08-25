models = {
    "Tax Advisor": {
        "prompt": "Dear AI accountant assistant specialized in answering tax accounting queries, I would greatly appreciate your assistance in addressing the following query. It is essential that your response is highly precise, comprehensive, and of the utmost quality, providing the most accurate and detailed information available. Please provide your response to the query mentioned below:\n{query}"
    },
    "Technical Accounting Advisor": {
        "prompt": "As an AI accountant assistant specialized in answering technical accounting queries, I kindly request your response to the following query, providing the most accurate and comprehensive information: {query}"
    },
    "ASC 842": {
        "kwip_source": "asc842",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ASC+842.html": "ASC 842"
        },
    },
    "IFRS 15": {
        "kwip_source": "ifrs15",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-15-revenue-from-contracts-with-customers+Basis+for+conclusions.html": "IFRS 15 Basis for Conclusions",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-15-revenue-from-contracts-with-customers+Illustrative+examples.html": "IFRS 15 Illustrative Examples",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-15-revenue-from-contracts-with-customers.html": "IFRS 15",
        },
    },
    "IFRS 16": {
        "kwip_source": "ifrs16",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-16-leases+basis+for+conclusions.html": "IFRS 16 Basis for Conclusions",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-16-leases+illusrative+examples.html": "IFRS 16 Illustrative Examples",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-16-leases.html": "IFRS 16",
        },
    },
    "IFRS 17": {
        "kwip_source": "ifrs17",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-17-insurance-contracts+Basis+for+conclusions.html": "IFRS 17 Basis for Conclusions",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-17-insurance-contracts+Illustrative+examples.html": "IFRS 17 Illustrative Examples",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-17-insurance-contracts.html": "IFRS 17",
        },
    },
}


def create_kwip_prompt(
    model: str, query: str, output_format="markdown", gpt_model="gpt-4"
):
    kwip_body = {
        "output_format": output_format,
        "model_name": gpt_model,
    }

    if models[model].get("prompt"):
        kwip_body["prompt"] = models[model]["prompt"].format(query=query)

    if models[model].get("kwip_source"):
        kwip_body["prompt"] = query
        kwip_body["sources"] = [models[model]["kwip_source"]]

    return kwip_body


def sanitise_kwip_response(model, ai_response):
    if models[model].get("source_urls"):
        for source_url, source_replace in models[model]["source_urls"].items():
            ai_response = ai_response.replace(source_url, source_replace)
    return ai_response
