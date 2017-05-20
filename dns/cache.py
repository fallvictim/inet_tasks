from datetime import datetime, timedelta
import pickle
import os.path
import threading


cache = dict()


def get_answers(questions):
    ans = {'answers': [], 'nss': [], 'arrs': []}
    found = False
    for q in questions:
        name, rtype = q['name'], q['qtype']
        cur_time = datetime.now()
        for k in list(cache.keys()):
            n, t, end = k
            if end < cur_time:
                cache.pop(k)
                continue
            if name == n and rtype == t:
                found = True
                if len(ans['answers']) > 0:
                    ans['arrs'] += cache[k]
                else:
                    ans['answers'] += cache[k]
    if found:
        return ans
    else:
        return


def add_answers(response):
    cur_time = datetime.now()
    for k in ['answers', 'arrs']:
        for a in response.get(k):
            name, rtype, ttl = a['name'], a['type'], a['ttl']
            end = cur_time + timedelta(seconds=ttl)
            if cache.get((name, rtype, end)) is None:
                cache[(name, rtype, end)] = [a]
            else:
                cache[(name, rtype, end)].append(a)


def clear_overdue():
    print('cleaning cache')
    cur_time = datetime.now()
    for n,t,end in list(cache.keys()):
        if end < cur_time:
            cache.pop((n, t, end))


def do_every(interval, worker_func, iterations=0):
    if iterations != 1:
        threading.Timer(
            interval,
            do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1]
        ).start()
    worker_func()


def save_cache():
    print('Saving cache')
    clear_overdue()
    with open('cache.pickle', 'wb') as fp:
        pickle.dump(cache, fp)


def initialize_cache():
    global cache
    print('Initializing cache')
    try:
        with open('cache.pickle', 'rb') as fp:
            cache = pickle.load(fp)
    except ValueError:
        print('something wrong with cache file')
        open('cache.pickle', 'wb').close()
    clear_overdue()


if os.path.isfile('cache.pickle'):
    initialize_cache()

do_every(60, clear_overdue)
