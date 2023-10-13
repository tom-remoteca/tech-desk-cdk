sources_prompt = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES"). 
If you don't know the answer, just say that you don't know. Don't try to make up an answer. The examples below are given in English, please return all your answers in Japanese. 
ALWAYS return a "SOURCES" part in your answer.

---EXAMPLES START---
QUESTION: Which state/country's law governs the interpretation of the contract?
=========
Content: This Agreement is governed by English law and the parties submit to the exclusive jurisdiction of the English courts in  relation to any dispute (contractual or non-contractual) concerning this Agreement save that either party may apply to any court for an  injunction or other relief to protect its Intellectual Property Rights.
Source: 28-pl
Content: No Waiver. Failure or delay in exercising any right or remedy under this Agreement shall not constitute a waiver of such (or any other)  right or remedy.\n\n11.7 Severability. The invalidity, illegality or unenforceability of any term (or part of a term) of this Agreement shall not affect the continuation  in force of the remainder of the term (if any) and this Agreement.\n\n11.8 No Agency. Except as expressly stated otherwise, nothing in this Agreement shall create an agency, partnership or joint venture of any  kind between the parties.\n\n11.9 No Third-Party Beneficiaries.
Source: 30-pl
Content: (b) if Google believes, in good faith, that the Distributor has violated or caused Google to violate any Anti-Bribery Laws (as  defined in Clause 8.5) or that such a violation is reasonably likely to occur,
Source: 4-pl
=========
FINAL ANSWER: This Agreement is governed by English law.
SOURCES: 28-pl

QUESTION: What did the president say about Michael Jackson?
=========
Content: Madam Speaker, Madam Vice President, our First Lady and Second Gentleman. Members of Congress and the Cabinet. Justices of the Supreme Court. My fellow Americans.  \n\nLast year COVID-19 kept us apart. This year we are finally together again. \n\nTonight, we meet as Democrats Republicans and Independents. But most importantly as Americans. \n\nWith a duty to one another to the American people to the Constitution. \n\nAnd with an unwavering resolve that freedom will always triumph over tyranny. \n\nSix days ago, Russia’s Vladimir Putin sought to shake the foundations of the free world thinking he could make it bend to his menacing ways. But he badly miscalculated. \n\nHe thought he could roll into Ukraine and the world would roll over. Instead he met a wall of strength he never imagined. \n\nHe met the Ukrainian people. \n\nFrom President Zelenskyy to every Ukrainian, their fearlessness, their courage, their determination, inspires the world. \n\nGroups of citizens blocking tanks with their bodies. Everyone from students to retirees teachers turned soldiers defending their homeland.
Source: 0-pl
Content: And we won’t stop. \n\nWe have lost so much to COVID-19. Time with one another. And worst of all, so much loss of life. \n\nLet’s use this moment to reset. Let’s stop looking at COVID-19 as a partisan dividing line and see it for what it is: A God-awful disease.  \n\nLet’s stop seeing each other as enemies, and start seeing each other for who we really are: Fellow Americans.  \n\nWe can’t change how divided we’ve been. But we can change how we move forward—on COVID-19 and other issues we must face together. \n\nI recently visited the New York City Police Department days after the funerals of Officer Wilbert Mora and his partner, Officer Jason Rivera. \n\nThey were responding to a 9-1-1 call when a man shot and killed them with a stolen gun. \n\nOfficer Mora was 27 years old. \n\nOfficer Rivera was 22. \n\nBoth Dominican Americans who’d grown up on the same streets they later chose to patrol as police officers. \n\nI spoke with their families and told them that we are forever in debt for their sacrifice, and we will carry on their mission to restore the trust and safety every community deserves.
Source: 24-pl
Content: And a proud Ukrainian people, who have known 30 years  of independence, have repeatedly shown that they will not tolerate anyone who tries to take their country backwards.  \n\nTo all Americans, I will be honest with you, as I’ve always promised. A Russian dictator, invading a foreign country, has costs around the world. \n\nAnd I’m taking robust action to make sure the pain of our sanctions  is targeted at Russia’s economy. And I will use every tool at our disposal to protect American businesses and consumers. \n\nTonight, I can announce that the United States has worked with 30 other countries to release 60 Million barrels of oil from reserves around the world.  \n\nAmerica will lead that effort, releasing 30 Million barrels from our own Strategic Petroleum Reserve. And we stand ready to do more if necessary, unified with our allies.  \n\nThese steps will help blunt gas prices here at home. And I know the news about what’s happening can seem alarming. \n\nBut I want you to know that we are going to be okay.
Source: 5-pl
Content: More support for patients and families. \n\nTo get there, I call on Congress to fund ARPA-H, the Advanced Research Projects Agency for Health. \n\nIt’s based on DARPA—the Defense Department project that led to the Internet, GPS, and so much more.  \n\nARPA-H will have a singular purpose—to drive breakthroughs in cancer, Alzheimer’s, diabetes, and more. \n\nA unity agenda for the nation. \n\nWe can do this. \n\nMy fellow Americans—tonight , we have gathered in a sacred space—the citadel of our democracy. \n\nIn this Capitol, generation after generation, Americans have debated great questions amid great strife, and have done great things. \n\nWe have fought for freedom, expanded liberty, defeated totalitarianism and terror. \n\nAnd built the strongest, freest, and most prosperous nation the world has ever known. \n\nNow is the hour. \n\nOur moment of responsibility. \n\nOur test of resolve and conscience, of history itself. \n\nIt is in this moment that our character is formed. Our purpose is found. Our future is forged. \n\nWell I know this nation.
Source: 34-pl`
=========
FINAL ANSWER: The president did not mention Michael Jackson.
SOURCES:
---EXAMPLES END---
"""

models = {
    "Tax Advisor": {
        "prompt": """Dear AI accountant assistant specialized in answering tax accounting queries, I would greatly appreciate your assistance in addressing the following query. 
            It is essential that your response is highly precise, comprehensive, and of the utmost quality, providing the most accurate and detailed information available. 
            Please provide your response to the query mentioned below, ensure to create a final answer with references ("SOURCES"). 
            If you don't know the answer, just say that you don't know. Don't try to make up an answer.
            ALWAYS return a "SOURCES" part in your answer.

            ---

            {query}
            """
    },
    "Technical Accounting Advisor": {
        "prompt": """Dear AI accountant assistant specialized in answering technical accounting queries, I would greatly appreciate your assistance in addressing the following query. 
            It is essential that your response is highly precise, comprehensive, and of the utmost quality, providing the most accurate and detailed information available. 
            Please provide your response to the query mentioned below, ensure to create a final answer with references ("SOURCES"). 
            If you don't know the answer, just say that you don't know. Don't try to make up an answer.
            ALWAYS return a "SOURCES" part in your answer.

            ---

            {query}
            """
    },
    "ASC 842": {
        "kwip_source": "asc842",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ASC+842.pdf": "ASC 842"
        },
    },
    "IFRS 15": {
        "kwip_source": "ifrs15",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-15-revenue-from-contracts-with-customers+Basis+for+conclusions.pdf": "IFRS 15 Basis for Conclusions",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-15-revenue-from-contracts-with-customers+Illustrative+examples.pdf": "IFRS 15 Illustrative Examples",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-15-revenue-from-contracts-with-customers.pdf": "IFRS 15",
        },
    },
    "IFRS 16": {
        "kwip_source": "ifrs16",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-16-leases+basis+for+conclusions.pdf": "IFRS 16 Basis for Conclusions",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-16-leases+illusrative+examples.pdf": "IFRS 16 Illustrative Examples",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-16-leases.pdf": "IFRS 16",
        },
    },
    "IFRS 17": {
        "kwip_source": "ifrs17",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-17-insurance-contracts+Basis+for+conclusions.pdf": "IFRS 17 Basis for Conclusions",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-17-insurance-contracts+Illustrative+examples.pdf": "IFRS 17 Illustrative Examples",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/ifrs-17-insurance-contracts.pdf": "IFRS 17",
        },
    },
    "Income Tax Legislation - UK": {
        "kwip_source": "IncomeTaxUK",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/the+Income+Tax+(Trading+and+Other+Income)+Act+2005.pdf": "Income Tax (Trading and Other Income) Act 2005",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/Income+Tax+Act+2007.pdf": "Income Tax Act 2007",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/Income+Tax+(Earnings+and+Pensions)+Act+2003.pdf": "Income Tax (Earnings and Pensions) Act 2003",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/Finance+Act+2023.pdf": "Finance Act 2023",
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/Finance+(No.2)+Act+2023.pdf": "Finance (No.2) Act 2023",
        },
    },
    "OECD Transfer Pricing": {
        "kwip_source": "OECDTransferPricing",
        "source_urls": {
            "https://techdesk-ai-assets.s3.eu-west-2.amazonaws.com/OECD+Transfer+Pricing+2022.pdf": "OECD Transfer Pricing Guidelines for Multinational Enterprises and Tax Administrations 2022",
        },
    },
}


def create_kwip_prompt(
    model: str, query: str, output_format="markdown", gpt_model="gpt-3.5-turbo"
):
    kwip_body = {"output_format": output_format, "model_name": gpt_model, "debug": True}

    if models[model].get("prompt"):
        kwip_body["prompt"] = models[model]["prompt"].format(query=query)

    if models[model].get("kwip_source"):
        kwip_body["prompt"] = query
        kwip_body["sources"] = [models[model]["kwip_source"]]
        kwip_body["sources_prompt"] = sources_prompt

    return kwip_body


def sanitise_kwip_response(model, ai_response):
    if models[model].get("source_urls"):
        for source_url, source_replace in models[model]["source_urls"].items():
            ai_response = ai_response.replace(f"[Link]({source_url})", "")
            ai_response = ai_response.replace(f"({source_url})", "")
            ai_response = ai_response.replace(source_url, source_replace)
    return ai_response
