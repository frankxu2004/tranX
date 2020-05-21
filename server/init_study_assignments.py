from pymongo import MongoClient

def get_assignments():
    assignments = []
    with open('assignments.txt', encoding='utf-8') as f:
        for line in f:
            l = line.strip()
            if l:
                userid = l.split(':')[0]
                for taskinfo in l.split(':')[1].split(';'):
                    task, use_plugin = taskinfo.split(',')
                    use_plugin = int(use_plugin)
                    assignments.append({'userid': userid, "task": task, "use_plugin": use_plugin, "completion_status": 0})
    return assignments


if __name__ == '__main__':

    client = MongoClient()
    db = client['tranx']
    collection = db['user_assignments']
    collection.delete_many({})
    assignments = get_assignments()
    collection.insert_many(assignments)
