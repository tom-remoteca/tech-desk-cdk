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
    update_query_activity,
    change_query_status,
    get_all_company_queries,
    change_status,
    get_query,
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


# Functions for query update workflow
def manage_add_activity(query_id):
    questions = [
        {"type": "input", "name": "activity", "message": "Enter new activity:"}
    ]
    answers = prompt(questions)
    update_query_activity(query_id, answers["activity"])


def manage_change_status(query_id):
    questions = [
        {
            "type": "list",
            "name": "status",
            "message": "Choose new status:",
            "choices": ["Open", "Closed", "In Progress"],
        }
    ]
    answers = prompt(questions)
    change_query_status(query_id, answers["status"])


def manage_query():
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

    all_queries = get_all_company_queries(company["id"])
    if len(all_queries) == 0:
        print("No Queries")
        return
    questions = [
        {
            "type": "list",
            "name": "query",
            "message": "Select Company:",
            "choices": [f"{i['query_id']} - {i['query_title']}" for i in all_queries],
        },
    ]
    answers = prompt(questions)
    for q in all_queries:
        if q["query_id"] == answers["query"].split(" - ")[0]:
            query = q

    while True:
        print(f"Query status: {query['query_status']}")

        questions = [
            {
                "type": "list",
                "name": "action",
                "message": f"Choose an action for '{query['query_title']}'",
                "choices": [
                    "Change Status",
                    "Exit",
                ],
            },
        ]
        answers = prompt(questions)

        if answers["action"] == "Change Status":
            change_status(company["id"], query)

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
