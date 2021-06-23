import urllib
from asgiref.sync import sync_to_async

def send_message(message, phone):
    values = {
        'authkey': '213839AETQhgGL7605a05a5P1',
        'mobiles': phone,
        'message': message,
        'sender': 'MAZONT',
        'route': 4
    }
    url = "https://control.msg91.com/api/sendhttp.php"
    postdata = urllib.parse.urlencode(values)
    postdata = postdata.encode('utf-8')
    req = urllib.request.Request(url, postdata)
    response = urllib.request.urlopen(req)

async_message_sender = sync_to_async(send_message, thread_sensitive=True)
