# -*- coding: utf-8 -*-

from BuglyLogin import Bugly
import json, time, os, random, traceback

class Spider:
    workplace           = ''
    appId               = ''
    pid                 = ''
    version             = ''
    urlIssueList        = 'https://bugly.qq.com/v2/issueList'
    urlCrashList        = 'https://bugly.qq.com/v2/crashList'
    urlCrashDoc         = 'https://bugly.qq.com/v2/crashDoc/appId/%(appId)s/platformId/%(pid)s/crashHash/%(crashId)s'
    urlAppDetailCrash   = 'https://bugly.qq.com/v2/appDetailCrash/appId/%(appId)s/platformId/%(pid)s/crashHash/%(crashId)s'
    issueIdx            = 0
    crashIdx            = 0
    bugly               = None
    def __init__(self, qq, pwd, workplace, appId, pid, version):
        print('开始登陆...')
        self.bugly = Bugly(qq,pwd)
        if os.path.exists(workplace) == False:
            os.mkdir(workplace)
        os.chdir(workplace)
        self.workplace = workplace
        self.appId = appId
        self.pid = pid
        self.version = version
        if os.path.isfile('cfg.json') == True:
            with open('cfg.json', 'r') as f:
                file = f.read()
                jsonData = json.loads(file)
                self.issueIdx = jsonData['issueIdx']
                self.crashIdx = jsonData['crashIdx']
        
        print('登陆完成...')
    def run(self):
        try:
            if self.__runIssueList() == True:
                return True
        except Exception as e:
            print('run发生异常:')
            print(str(e))
            print(traceback.print_exc())
            return False
        return False
            
    def __runIssueList(self):
        print('获取错误列表长度...')
        self.__random_wait(1,1)
        jsonData = self.bugly.get(self.urlIssueList, {
            'start':0,
            'searchType':'errorType',
            'pid':self.pid,
            'exceptionTypeList':'AllCatched,Unity3D,Lua,JS',
            'sortOrder':'desc',
            'version':self.version,
            'sortField':'crashCount',
            'appId':self.appId,
            'platformId':'1',
            'rows':'10',
            })
    
        if jsonData == None:
            return False
        
        issueNum = jsonData['numFound']
        print('错误列表长度[%(issueNum)d]...'%{'issueNum':issueNum})
        
        while self.issueIdx < issueNum:
            page = self.issueIdx - self.issueIdx%50
            print('获取错误列表分页[%(page)d]...'%{'page':page})
            self.__random_wait(1,1)
            jsonData = self.bugly.get(self.urlIssueList, {
                'start':str(page),
                'searchType':'errorType',
                'pid':self.pid,
                'exceptionTypeList':'AllCatched,Unity3D,Lua,JS',
                'sortOrder':'desc',
                'version':self.version,
                'sortField':'crashCount',
                'appId':self.appId,
                'platformId':'1',
                'rows':'50',
                })
    
            if jsonData == None:
                return False

            issueList = jsonData['issueList']
            while self.issueIdx < page+len(issueList):
                issueId = issueList[self.issueIdx-page]['issueId']
                if (self.__runCrashList(issueId)== False):
                    return False
                self.issueIdx+=1
                self.crashIdx=0
                self.__save_cfg()
        return True
        
    def __runCrashList(self, issueId):
        print('获取机型列表长度...')
        self.__random_wait(1,1)
        jsonData = self.bugly.get(self.urlCrashList, {
            'start':0,
            'searchType':'detail',
            'pid':self.pid,
            'exceptionTypeList':'AllCatched,Unity3D,Lua,JS',
            'sortOrder':'desc',
            'sortField':'crashCount',
            'appId':self.appId,
            'platformId':1,
            'rows':'10',
            'issueId':issueId,
            'version':self.version,
            })
    
        if jsonData == None:
            return False

        crashNum = jsonData['numFound']
        print('机型列表长度[%(crashNum)d]...'%{'crashNum':crashNum})
        
        while self.crashIdx < crashNum:
            page = self.crashIdx - self.crashIdx%50
            print('获取机型列表分页[%(page)d]...'%{'page':page})
            self.__random_wait(1,1)
            jsonData = self.bugly.get(self.urlCrashList, {
                'start':str(page),
                'searchType':'detail',
                'pid':self.pid,
                'exceptionTypeList':'AllCatched,Unity3D,Lua,JS',
                'sortOrder':'desc',
                'sortField':'crashCount',
                'appId':self.appId,
                'platformId':1,
                'rows':'50',
                'issueId':issueId,
                'version':self.version,
                })
        
            if jsonData == None:
                return False

            crashIdList = jsonData['crashIdList']
            while self.crashIdx < page+len(crashIdList):
                crashId = crashIdList[self.crashIdx-page]
                if (self.__runCrashDetail(crashId)== False):
                    return False
                self.crashIdx += 1
                self.__save_cfg()
            #每拉取50个，随机休息20-30s
            self.__random_wait(5,5)
        return True
        
    def __runCrashDetail(self, crashId):
        name = crashId.replace(':','_')
        
        if os.path.isfile(name+'_crashDoc.json') == False:
            #print('拉取机型CrashDoc信息%(name)s...'%{'name':name})
            crashDocUrl = self.urlCrashDoc%{'appId':self.appId, 'pid':self.pid, 'crashId':crashId}
            self.__random_wait(0.5,0.5)
            crashDoc = self.bugly.get(crashDocUrl)
            if crashDoc != None:
                with open(name+'_crashDoc.json','w') as f:
                    f.write(json.dumps(crashDoc))
            else:
                print('忽略文件:',name+'_crashDoc.json')
                
        if os.path.isfile(name+'_appDetail.json') == False:
            #print('拉取机型AppDetail信息%(name)s...'%{'name':name})
            appDetailCrashUrl = self.urlAppDetailCrash%{'appId':self.appId, 'pid':self.pid, 'crashId':crashId}
            #self.__random_wait(1,1.5)
            appDetailCrash = self.bugly.get(appDetailCrashUrl)
            if appDetailCrash != None:
                with open(name+'_appDetail.json','w') as f:
                    f.write(json.dumps(appDetailCrash))
            else:
                print('忽略文件:',name+'_appDetail.json')
                
        print('机型信息%(name)s存储完成...'%{'name':name})
        return True
        
    def __save_cfg(self):
        with open('cfg.json','w') as f:
            jsonData = {
                'issueIdx':self.issueIdx,
                'crashIdx':self.crashIdx,
            }
            f.write(json.dumps(jsonData))

    def __random_wait(self, min, max):
        time.sleep(random.uniform(min,max))
        
if __name__ == '__main__':
    spider = Spider('qq','pwd', 'outpath', 'appId', 'pid', 'version')
    spider.run()
