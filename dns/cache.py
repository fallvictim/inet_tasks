import datetime
import time
import json

cache = {'answers': dict(dict()), 'nss': dict(dict()), 'arrs': dict(dict())}


def get_answers(questions):
    ans = {'answers': [], 'nss': [], 'arrs': []}
    found = False
    for q in questions:
        for k in ans.keys():
            record = cache[k].get(q.get('name'), {}).get(q.get('qtype'))
            if record is not None:
                ttl = datetime.timedelta(seconds=record[0].get('ttl')) - (datetime.datetime.now() - record[1])
                if ttl.seconds > 0:
                    record[0]['ttl'] = ttl.seconds
                    ans[k].append(record[0])
                    found = True
                    clear_overdue()
    if found:
        return ans
    else:
        return


def add_answers(response, rec_time):
    for k in ['answers', 'nss', 'arrs']:
        for a in response.get(k):
            name, rtype, ttl = a.get('name'), a.get('type'), a.get('ttl')
            cache[k].update({name: {rtype: [a, rec_time]}})


def clear_overdue():
    for k in list(cache.keys()):
        for name in list(cache[k].keys()):
            for rtype in list(cache[k][name].keys()):
                record = cache[k][name][rtype]
                rec_time, ttl = record[1], datetime.timedelta(seconds=record[0].get('ttl'))
                time.sleep(2)
                past = datetime.datetime.now() - rec_time
                if past > ttl:
                    cache[k][name].pop(rtype)
            if cache[k].get(name) == {}:
                cache[k].pop(name)


def save_cache():
    clear_overdue()
    temp = cache.copy()
    for k in list(temp.keys()):
        for name in list(temp[k].keys()):
            for rtype in list(temp[k][name].keys()):
                record = temp[k][name][rtype][1]
                temp[k][name][rtype][1] = record.isoformat()
    with open('cache.json', 'w') as fp:
        json.dump(temp, fp)


def initialize_cache():
    global cache
    with open('cache.json', 'r') as fp:
        cache = json.load(fp)
    for k in list(cache.keys()):
        for name in list(cache[k].keys()):
            for rtype in list(cache[k][name].keys()):
                record = cache[k][name][rtype][1]
                cache[k][name][rtype][1] = datetime.datetime.strptime(record, "%Y-%m-%dT%H:%M:%S.%f")
    clear_overdue()
