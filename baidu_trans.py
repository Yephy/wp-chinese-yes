import http.client
import hashlib
import urllib
import random
import json


def baidu_trans(q="", fromLang="auto", toLang="zh"):
    appid = ""
    secretKey = ""

    httpClient = None
    myurl = "/api/trans/vip/translate"

    salt = random.randint(32768, 65536)
    sign = appid + q + str(salt) + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    myurl = myurl + "?appid=" + appid + "&q=" + urllib.parse.quote(
        q) + "&from=" + fromLang + "&to=" + toLang + "&salt=" + str(
        salt) + "&sign=" + sign

    try:
        httpClient = http.client.HTTPConnection("api.fanyi.baidu.com")
        httpClient.request("GET", myurl)

        # response是HTTPResponse对象
        response = httpClient.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)

        return (result)

    except Exception as e:
        print(e)
    finally:
        if httpClient:
            httpClient.close()
