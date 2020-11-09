import urllib

def send_message(message, phone):
    values = {
        'authkey': '213839AHVCFomzdt5e274930P1',
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