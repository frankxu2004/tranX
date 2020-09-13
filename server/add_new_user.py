import gspread
import random
from oauth2client.service_account import ServiceAccountCredentials
from server.init_study_assignments import get_assignments, update_database


def to_userid(email_addr):
    return email_addr.split('@')[0]


def get_records(name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('nlp-research-472d123ba8a3.json', scope)
    client = gspread.authorize(creds)
    if name == 'survey':
        sheet = client.open('CodeGen Pre-study Survey (Responses)').worksheets()[0]
    elif name == 'consent':
        sheet = client.open('CodeGen Pre-study Survey (Responses)').worksheets()[1]
    else:
        raise RuntimeError("Wrong record name.")
    return sheet.get_all_records()


def assign_tasks(user_data):
    # all users get task 1 and 2 (Basic Python and File)
    assigned = ['task1', 'task2']
    scores = [user_data['OS'], user_data['Web Scraping'], user_data['Web Server & Client'],
              user_data['Data Analysis & Machine Learning'], user_data['Data Visualization']]
    idxs = sorted(range(len(scores)), key=lambda k: scores[k], reverse=True)
    selected = sorted(idxs[:2])
    for idx in selected:
        assigned.append('task' + str(3 + idx))
    return assigned


def randomize(assignment):
    tasks = []
    use_plugin = []
    for task_cat in assignment:
        tasks.append(task_cat + '-1')
        tasks.append(task_cat + '-2')
        plugin = [0, 0]
        plugin[random.randint(0, 1)] = 1
        use_plugin.extend(plugin)
    return tasks, use_plugin


if __name__ == '__main__':
    already_assigned_users = set([x['userid'] for x in get_assignments()])
    consented_users = get_records('consent')
    surveyed_users = get_records('survey')
    surveyed_dict = {}
    for surveyed_user in surveyed_users:
        if surveyed_user['Name']:
            surveyed_dict[to_userid(surveyed_user['Email Address'])] = surveyed_user
    with open('assignments.txt', 'a', encoding='utf-8') as f:
        for consented_user in consented_users:
            email = consented_user['Your Email']
            user_id = to_userid(email)
            if user_id not in already_assigned_users:
                already_assigned_users.add(user_id)
                print(surveyed_dict[user_id])
                tasks, use_plugin = randomize(assign_tasks(surveyed_dict[user_id]))
                assign_string_list = []
                for task_name, if_use in zip(tasks, use_plugin):
                    assign_string_list.append(task_name + ',' + str(if_use))
                f.write(user_id + ':' + ';'.join(assign_string_list) + '\n')
    update_database()
