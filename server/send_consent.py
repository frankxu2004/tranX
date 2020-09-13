from server.add_new_user import get_records, to_userid

if __name__ == '__main__':
    consented_users = get_records('consent')
    surveyed_users = get_records('survey')
    surveyed_dict = {}
    for surveyed_user in surveyed_users:
        if surveyed_user['Name']:
            surveyed_dict[to_userid(surveyed_user['Email Address'])] = surveyed_user
    consented_dict = {}
    for consented_user in consented_users:
        consented_dict[to_userid(consented_user['Your Email'])] = consented_user
    for userid in surveyed_dict.keys() - consented_dict.keys():
        print(surveyed_dict[userid]['Email Address'])