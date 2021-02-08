import requests
import re
import json
import os
import sys
import progressbar
requests.packages.urllib3.disable_warnings()

class QQMusicSpider:
    def __init__(self):
        self.url1 = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
        self.url2 = 'https://u.y.qq.com/cgi-bin/musicu.fcg?data={"req_0":{"module":"vkey.GetVkeyServer","method":"CgiGetVkey","param":{"guid":"1796344836","songmid":["%s"],"songtype":[0],"uin":"0","loginflag":1,"platform":"20"}},"comm":{"uin":0,"format":"json","ct":24,"cv":0}}'
        # self.url3 = 'http://dl.stream.qqmusic.qq.com/'
        self.url3 = 'https://isure.stream.qqmusic.qq.com/'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
            "Referer": "https://y.qq.com/",
            "Cookie": "pgv_pvi=2567757824; ts_uid=64446952; pgv_pvid=6809245960; userAction=1; RK=0ID4VI/yGY; ptcz=6f4eaa825e99af36068b5d51b8e34c1c0087b9c95c44f7b062d5cff7b3c70d22; euin=owSF7e4kNKnz; qm_keyst=Q_H_L_2a6K5_50eO5-itw83Uio7kRWq8WgGbPI1BGlM1c8ng4qZt_ZAxTRmHb8B4SQBWD; uin=278455900; tmeLoginType=2; psrf_qqopenid=8E8FC9D9774A8788D4DF1FD73F2B8D88; psrf_qqaccess_token=22EEB4580A1D37E9AB61B4A2CD6FC0CE; psrf_qqunionid=; qqmusic_key=Q_H_L_2a6K5_50eO5-itw83Uio7kRWq8WgGbPI1BGlM1c8ng4qZt_ZAxTRmHb8B4SQBWD; psrf_musickey_createtime=1602572393; psrf_access_token_expiresAt=1610348393; psrf_qqrefresh_token=1873C9B55CC272116295F7B5AC7DE014; yqq_stat=0; pgv_info=ssid=s3690755542; ts_refer=ADTAGmyqq; pgv_si=s1594386432; yplayer_open=1; qqmusic_fromtag=66; yq_playschange=0; yq_playdata=; player_exist=1; yq_index=1; ts_last=y.qq.com/n/yqq/song/002t78Qs1Av9Kn.html"
        }
        self.w = ""

    def get_search_content(self):
        """获取搜索结果"""
        response = requests.get(self.url1, headers=self.headers, params={"w": self.w},verify=False)
        content = response.content.decode('utf-8')
        jsonStr = content.lstrip('callback(')
        jsonStr = jsonStr.rstrip(')')
        data = json.loads(jsonStr) # dict
        songData = data.get('data').get('song').get('list') # list
        songsList = []
        for i in songData:
            singersName = ''
            for singer in i['singer']:
                singerName = singer['name'] # 取歌手名
                singersName = f'{singersName},{singerName}' # PEP 498 F-strings 拼接
            singersName = singersName.lstrip(',') # 去除开头的逗号
            songDict = {'singers':singersName,'name':i['songname'],'mid':i['songmid']}
            songsList.append(songDict)
            del singersName,songDict
        return songsList
    
    def get_purl(self, songmid):
        """根据歌曲的mid搜索vk"""
        data = self.parse_json(url=self.url2 % songmid, headers=self.headers)
        return data["req_0"]["data"]["midurlinfo"][0]["purl"]

    def save_song(self, url,song_name):
        """下载歌曲"""
        print("-"*100)
        song_name = re.sub(r"|[\\/:*?\"<>|]+", "", song_name.strip())
        filename = os.path.split(os.path.realpath(sys.argv[0]))[0]+'\\'+song_name+".m4a"
        filename.replace('/','\\')
        print("{}下载中...".format(filename))
        response = requests.get(url, headers=self.headers, verify=False)
        code = response.status_code
        if code == 200:
            resLength = int(response.headers.get('Content-Length')) # 作为进度条总长
            with open(filename,"wb") as file:
                widgets = ['下载进度: ', progressbar.Percentage(), ' ',
                        progressbar.Bar(marker='#', left='[', right=']')]
                pBar = progressbar.ProgressBar(widgets=widgets, maxval=resLength).start()
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk :
                        file.write(chunk)
                    pBar.update(len(chunk)+1)
                pBar.finish()
            print("{}下载完毕".format(filename))
        elif code == 403 :
            print("{}下载失败，目前暂不支持非会员Cookie下载VIP歌曲".format(filename))
        elif not response:
            print("{}下载失败，建议VIP用户使用会员账号修改程序Cookie".format(filename))
        print("-" * 100)

    def parse_json(self, url, headers, params={}):
        """解析url，返回json"""
        response = requests.get(url, headers=headers, params=params,verify=False)
        return response.json()

    def start(self):
        """开始爬虫"""
        while True:
            self.w = input("输入要搜索的歌曲/歌手：")
            search_data = self.get_search_content()
            for index,value in enumerate(search_data):
                print("({}){} - {}".format(index + 1,value['singers'],value['name']))
            print("(0)退出程序")
            print("(-1)重新搜索")
            index = int(input("选择歌曲编号进行下载："))
            if index == 0:
                break
            if index == -1:
                continue
            purl = self.get_purl(search_data[index - 1]['mid'])
            self.save_song(url=self.url3 + purl,song_name=search_data[index - 1]['singers']+' - '+search_data[index - 1]['name'])
            
if __name__ == '__main__':
    QQMusicSpider().start()
    