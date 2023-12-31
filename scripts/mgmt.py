from PyInquirer import prompt
import time
from company_functions import (
    create_company,
    delete_company,
    create_invite_link,
    delete_user,
    list_users,
    get_company_info,
    get_all_companies,
)

from activity_functions import (
    get_all_company_queries,
    change_status,
    get_query,
    comment_as_expert,
    comment_as_techdesk,
    complete_add_report,
)


def manage_delete_user():
    questions = [
        {"type": "input", "name": "user_id", "message": "UserID of user to delete:"}
    ]
    answers = prompt(questions)
    delete_user(answers["user_id"])


def manage_create_company():
    questions = [
        {"type": "input", "name": "company_name", "message": "Enter new company name:"}
    ]
    answers = prompt(questions)
    create_company(answers["company_name"])


def manage_delete_company(company_id):
    questions = [
        {
            "type": "confirm",
            "message": "Are you sure?",
            "name": "confirm",
            "default": False,
        },
    ]
    answers = prompt(questions)
    if answers["confirm"]:
        delete_company(company_id)
    else:
        print("Not confirmed, company not deleted.")


def manage_delete_user(company_id):
    questions = [
        {
            "type": "input",
            "name": "user_id",
            "message": "Enter user_id of user to delete",
        },
        {
            "type": "confirm",
            "message": "Are you sure?",
            "name": "confirm",
            "default": False,
        },
    ]
    answers = prompt(questions)
    if answers["confirm"]:
        delete_user(company_id, answers["user_id"])
    else:
        print("Not confirmed, user not deleted.")


def manage_company():
    companies = get_all_companies()
    questions = [
        {
            "type": "list",
            "name": "comapny_name",
            "message": "Select Company:",
            "choices": [i["name"] for i in companies],
        },
    ]
    answers = prompt(questions)
    for c in companies:
        if c["name"] == answers["comapny_name"]:
            company = c
    while True:
        questions = [
            {
                "type": "list",
                "name": "action",
                "message": f"Choose an action for '{company['name']}'",
                "choices": [
                    "View Company Info",
                    "List Users",
                    "Create Invite Link",
                    "Delete User",
                    "Delete Company",
                    "Exit",
                ],
            },
        ]
        answers = prompt(questions)

        if answers["action"] == "List Users":
            list_users(company["id"])
        elif answers["action"] == "View Company Info":
            get_company_info(company["id"])
        elif answers["action"] == "Delete Company":
            manage_delete_company(company["id"])
        elif answers["action"] == "Delete User":
            manage_delete_user(company["id"])
        elif answers["action"] == "Create Invite Link":
            create_invite_link(company_id=company["id"], company_name=company["name"])

        elif answers["action"] == "Exit":
            print("Exiting...")
            break


def manage_query():
    companies = get_all_companies()
    questions = [
        {
            "type": "list",
            "name": "comapny_name",
            "message": "Select Company:",
            "choices": [i["name"] for i in companies],
        },
        # {
        #     "type": "input",
        #     "name": "query_id",
        #     "message": "Enter Query ID:",
        # },
    ]
    answers = prompt(questions)
    for c in companies:
        if c["name"] == answers["comapny_name"]:
            company = c

    while True:
        all_queries = get_all_company_queries(company["id"])
        if len(all_queries) == 0:
            print("No Queries")
            return
        choices = [f"{i['query_id']} - {i['query_title']}" for i in all_queries]
        choices.append("Exit")
        questions = [
            {
                "type": "list",
                "name": "query",
                "message": "Select Query:",
                "choices": choices,
            },
        ]

        answers = prompt(questions)
        if answers["query"] == "Exit":
            break

        for q in all_queries:
            if q["query_id"] == answers["query"].split(" - ")[0]:
                query = q
        while True:
            print(query)
            print(f"Query status: {query['query_status']}")

            questions = [
                {
                    "type": "list",
                    "name": "action",
                    "message": f"Choose an action for '{query['query_title']}'",
                    "choices": [
                        "Change Status",
                        "Comment As Expert",
                        "Comment As TechDesk",
                        "Complete & Add Report",
                        "Exit",
                    ],
                },
            ]
            answers = prompt(questions)

            if answers["action"] == "Change Status":
                change_status(company["id"], query)

            if answers["action"] == "Comment As Expert":
                comment_as_expert(company["id"], query)

            if answers["action"] == "Comment As TechDesk":
                comment_as_techdesk(company["id"], query)

            if answers["action"] == "Complete & Add Report":
                complete_add_report(company["id"], query)

            elif answers["action"] == "Exit":
                print("Exiting...")
                break

            time.sleep(2)
            query = get_query(
                company_id=company["id"],
                user_id=query["submittor_id"],
                query_id=query["query_id"],
            )


# Main function
def main():
    while True:
        questions = [
            {
                "type": "list",
                "name": "main_menu",
                "message": "What would you like to do?",
                "choices": [
                    "Create New Company",
                    "Manage Existing Company",
                    "Manage Query",
                    "Exit",
                ],
            }
        ]
        answers = prompt(questions)
        if answers["main_menu"] == "Manage Existing Company":
            manage_company()
        if answers["main_menu"] == "Create New Company":
            manage_create_company()
        elif answers["main_menu"] == "Manage Query":
            manage_query()
        elif answers["main_menu"] == "Exit":
            print("Exiting...")
            break


if __name__ == "__main__":
    main()
