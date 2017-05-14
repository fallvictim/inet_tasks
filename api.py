import vk
import sys
import datetime


def print_info(user_id):
    user = vk_api.users.get(user_id=user_id, fields='bdate, online, last_seen')[0]
    friends = vk_api.friends.get(user_id=user_id, fields='first_name')
    albums = vk_api.photos.getAlbums(user_id=user_id)

    if user['online'] == 1:
        print('Online')
    else:
        last_seen = user['last_seen']['time_serv']
        if last_seen > 1262304000:
            time = datetime.datetime.fromtimestamp(last_seen).strftime('%d.%m.%Y %H:%M:%S')
            print('Был в сети ' + time)
    print('\nИмя: ' + user['first_name'])
    print('Фамилия: ' + user['last_name'])
    print('Дата рождения: ' + user.get('bdate', 'не указана') + '\n')
    print('Друзья:')
    for friend in friends:
        print(friend['first_name'] + ' ' + friend['last_name'])
    print('\nАльбомы:')
    for album in albums:
        print(album['title'])

if __name__ == '__main__':
    if len(sys.argv) > 1 and (sys.argv[1] == 'help' or sys.argv[1] == '/?'):
            print('''
            Usage: api.py help|user_id
            Print info about vk user.
            By default user_id is 1.
            ''')
    else:
        vk_api = vk.API(vk.Session())
        user_id = 1

        if len(sys.argv) > 1:
            user_id = sys.argv[1]

        print('ID: ' + str(user_id))
        try:
            print_info(user_id)
        except vk.exceptions.VkAPIError:
            print('User deactivated. Information is unavailable.')
