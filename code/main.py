import asyncio
from contextvars import Context
import hmac
import traceback
import aiofiles
import aiohttp
import time
import copy
import io
import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageFilter, ImageEnhance
from aiohttp import web, FormData
from aiohttp.web_request import Request
from khl import Bot,Message,PrivateMessage
from khl.card import Element,Card,CardMessage,Module,Types
from khl.command import Rule

from card_ui import icon,ui
repo_secret = {}
gh_ping_temp = {}
com_temp = {}
gh_guild_setting = {}
routes = web.RouteTableDef()
# 初始化bot
with open('./config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
bot = Bot(token=config['token'])

# 获取当前时间
def GetTime():  
    return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

# 读取文件
async def read_file(path) -> dict:
    async with aiofiles.open(path,'r',encoding='utf-8') as f:
        return json.loads(await f.read())

# 写入文件
async def write_file(path, value):
    async with aiofiles.open(path, 'w',encoding='utf-8') as f:
        await f.write(json.dumps(value,ensure_ascii=False,indent=2, sort_keys=True,))

async def img_requestor(img_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as r:
            return await r.read()

path_github_repo = './log/github/repo_setting.json'
path_github_guild = './log/github/guild_setting.json'
path_github_ping = './log/github/ping_temp.json'
path_github_secret = './log/github/secret.json'
path_gitee_ping = './log/gitee/ping_temp.json'
path_gitee_repo = './log/gitee/repo_setting.json'
path_gitee_guild = './log/gitee/guild_setting.json'
# 开机加载
@bot.task.add_date()
async def tgrds():
    try:# github
        global gh_res_setting
        gh_res_setting = await read_file(path_github_repo)
        global gh_guild_setting
        gh_guild_setting = await read_file(path_github_guild)
        global gh_ping_temp
        gh_ping_temp = await read_file(path_github_ping)
        global repo_secret
        repo_secret = await read_file(path_github_secret)
        # gitee
        global ge_res_setting
        ge_res_setting = await read_file(path_gitee_repo)
        global ge_guild_setting
        ge_guild_setting = await read_file(path_gitee_guild)
        global ge_ping_temp
        ge_ping_temp = await read_file(path_gitee_ping)
    except:
        print(f"ERR while starting!\n{traceback.format_exc()}")
        os._exit(-1)
# 定时保存
@bot.task.add_interval(seconds=60)
async def save_Data():
    await write_file(path_github_repo,gh_res_setting)
    await write_file(path_github_guild,gh_guild_setting)
    await write_file(path_github_ping,gh_ping_temp)
    await write_file(path_github_secret,repo_secret)
    # gitee
    await write_file(path_gitee_repo,ge_res_setting)
    await write_file(path_gitee_guild,ge_guild_setting)
    await write_file(path_gitee_ping,ge_ping_temp)
    print(f"[{GetTime()}] save_data success!")

# 在控制台打印msg内容，用作日志
async def logging(msg: Message,PrivateBan=False):
    now_time = GetTime()
    if isinstance(msg, PrivateMessage):
        log_str = f"[{now_time}] PrivateMessage - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} = {msg.content}"
        if PrivateBan:
            log_str+= " ban"
            await msg.reply(f"本命令需要在公频使用！")
        print(log_str)
        return True
    else:
        print(f"[{now_time}] G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} = {msg.content}")
        return False

async def type_push(data:dict,request: web.Request,body,rid):
    repo_name = data["repository"]["full_name"] # 完整的仓库名字
    repo_url = data["repository"]['url']
    sender_name = data["sender"]["login"]
    sender_url = data["sender"]["url"]
    sender_avatar = data["sender"]["avatar_url"]
    compare = data['compare']
    head_cmt_time = data["head_commit"]["timestamp"] if "head_commit" in data else ''
    bhash = data['before'] if 'before' in data else ''
    ahash = data['after'] if 'after' in data else ''
    if len(bhash) >8:
        bhash = bhash[0:7]
    if len(ahash) >8:
        ahash = ahash[0:7]
    if head_cmt_time!='':
        head_cmt_time = "at "+head_cmt_time[0:19]
    commit_num = len(data["commits"]) # commit数量
    # 为多个commit显示message
    message=(data['commits'][0]['message'])
    i=1
    while i < commit_num:
        if i==1: message+="\n"
        message+=data["commits"][i]["message"]
        if i < commit_num-1: message+="\n"
        i+=1

    c = Card(color=ui.default_color)
    c.append(Module.Header(f'New Push Event from Github'))
    usr_text = f"> [{sender_name}]({sender_url})\n"
    usr_text+= f"> [{repo_name}]({repo_url})"
    c.append(Module.Section(Element.Text(usr_text,Types.Text.KMD),
                            Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
    c.append(Module.Context(f"{commit_num} commit {head_cmt_time}"))
    c.append(Module.Divider())
    if bhash != '':
        c.append(Module.Context(Element.Text(f'Hash: [{bhash} -> {ahash}]({compare})',Types.Text.KMD)))
    while message.find('\n\n') >0:
        message = message.replace('\n\n','\n')
    print(f"[github repo:{repo_name} = {message} ]")
    c.append(Module.Context(Element.Text(f'Message:\n**{message}**',Types.Text.KMD)))
    return c

async def type_release(data:dict,request: web.Request,body,rid):
    repo_name = data["repository"]["full_name"] # 完整的仓库名字
    repo_url = data["repository"]['url']
    sender_name = data["sender"]["login"]
    sender_url = data["sender"]["url"]
    sender_avatar = data["sender"]["avatar_url"]
    tag_name = data["release"]["tag_name"]
    release_name = data["release"]["name"]
    release_body = data["release"]["body"]
    release_url = data["release"]["html_url"]
    
    c = Card(color=ui.default_color)
    c.append(Module.Header(f'New Release Event from Github'))
    usr_text = f"> [{sender_name}]({sender_url}) release {release_name}\n"
    usr_text+= f"> [{repo_name}]({repo_url})"
    c.append(Module.Section(Element.Text(usr_text,Types.Text.KMD),
                            Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
    c.append(Module.Divider())
    c.append(Module.Context(Element.Text(f'> Tag: [{tag_name}]({release_url})',Types.Text.KMD)))
    c.append(Module.Context(Element.Text(f'> Info:\n**{release_body}**',Types.Text.KMD)))
    return c

#处理github请求
async def github_webhook(request: web.Request):
    Etype = request.headers['X-GitHub-Event']
    did = request.headers['X-GitHub-Delivery']
    if 'X-HUB-SIGNATURE' in request.headers:
        secret_state = True
        sign = request.headers['X-HUB-SIGNATURE']
    else:
        secret_state = False
        sign = ''
    # 获取post的body
    body = await request.content.read()
    data = json.loads(body.decode('UTF8'))
    rid = str(data["repository"]["id"])
    repo_name = data["repository"]["full_name"] # 完整的仓库名字
    global gh_ping_temp
    gh_ping_temp[did] = {'rid': rid, 'secret': secret_state, 'sign': sign,'body':data}
    print(f"[{Etype}] from {repo_name}, rid:{rid}")
    c = None
    if Etype == 'ping':
        return web.Response(body="Pong!", status=200)
    elif Etype == 'push':
        if "refs/tags" not in data["ref"]:
            c = await type_push(data,request,body,rid)
        else:
            return web.Response(body="only handle user.push", status=200)
    elif Etype == 'release':
        if data["action"] == "published":
            c = await type_release(data,request,body,rid)
        else:
            return web.Response(body="wait for release.published", status=200)
    else:
        return web.Response(body="Unsupported github event!", status=400)
        
    # 遍历文件，如果在setting里面，代表已经bind过了
    if rid in gh_res_setting:
        for cid, v in gh_res_setting[rid].items():
            ch = await bot.client.fetch_public_channel(cid)
            # if 'secret' in repo_secret: 
            #     secret = repo_secret['secret']
            #     digest, signature = request.headers['X-HUB-SIGNATURE'].split("=", 1)
            #     assert digest == "sha1", "Digest must be sha1"  # use a whitelist
            #     h = hmac.HMAC(bytes(secret, "UTF8"), msg=body, digestmod=digest)
            #     await ch.send(
            #         ui.card_uni(icon.error, 'secret错误', f'repo:[{repo_name}]({repo_url})'))
            #     assert h.hexdigest() == signature, "Bad signature"
            #     print( f"[secret err] repo:[{repo_name}]({repo_url})")
            await ch.send(CardMessage(c))
        
    return web.Response(body="get you!", status=200)

# gitee请求
async def gitee_webhook(request: web.Request):
    Etype = request.headers['X-Gitee-Event']
    if Etype != "Push Hook":
        return web.Response(body="Unsupported gitee event!", status=400)
    # 获取post的body
    body = await request.content.read()
    data = json.loads(body.decode('UTF8'))
    rid = str(data["repository"]["id"])
    repo_name = data["repository"]["full_name"] # 完整的仓库名字
    repo_url = data["repository"]['url']
    sender_name = data["sender"]["login"]
    sender_url = data["sender"]["url"]
    sender_avatar = data["sender"]["avatar_url"]
    global ge_ping_temp
    if repo_name not in ge_ping_temp:
        ge_ping_temp[repo_name] = {'rid': rid,'url':repo_url,'avatar_url':sender_avatar,'body':data}
    
    print(f"[{Etype}] from {repo_name}, rid:{rid}")

    # 上传用户头像到kook
    if ("avatar_url_kook" not in ge_ping_temp[repo_name]) or (sender_avatar != ge_ping_temp[repo_name]['avatar_url']):
        bg = Image.open(io.BytesIO(await img_requestor(sender_avatar)))
        imgByteArr = io.BytesIO()
        bg.save(imgByteArr, format='PNG')
        imgByte = imgByteArr.getvalue()
        sender_avatar = await bot.create_asset(imgByte)
        ge_ping_temp[repo_name]["avatar_url_kook"] = sender_avatar
        print(f"[{repo_name}] new user-avatar {sender_avatar}")
    else:
        sender_avatar = ge_ping_temp[repo_name]["avatar_url_kook"]
    
    compare = data['compare']
    head_cmt_time = data["repository"]["updated_at"] if "updated_at" in data["repository"] else ''
    bhash = data['before'] if 'before' in data else ''
    ahash = data['after'] if 'after' in data else ''
    if len(bhash) >8:
        bhash = bhash[0:7]
    if len(ahash) >8:
        ahash = ahash[0:7]
    if head_cmt_time!='':
        head_cmt_time = "at "+head_cmt_time[0:19]
    commit_num = len(data["commits"]) # commit数量
    # 为多个commit显示message
    message=(data['commits'][0]['message'])
    i=1
    while i < commit_num:
        if i==1: message+="\n"
        message+="\n"
        message+=data["commits"][i]["message"]
        i+=1
    
    c = Card(color=ui.default_color)
    c.append(Module.Header(f'New Push Event from Gitee'))
    usr_text = f"> [{sender_name}]({sender_url})\n"
    usr_text+= f"> [{repo_name}]({repo_url})"
    c.append(Module.Section(Element.Text(usr_text,Types.Text.KMD),
                            Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
    c.append(Module.Context(f"{commit_num} commit {head_cmt_time}"))
    c.append(Module.Divider())
    if bhash != '':
        c.append(Module.Context(Element.Text(f'Hash: [{bhash} -> {ahash}]({compare})',Types.Text.KMD)))
    while message.find('\n\n') >0:
        message = message.replace('\n\n','\n')
    print(f"[gitee repo:{repo_name} = {message} ]")
    c.append(Module.Context(Element.Text(f'Message:\n**{message}**',Types.Text.KMD)))
    # 遍历文件，如果在setting里面，代表已经bind过了
    if rid in ge_res_setting:
        for cid, v in ge_res_setting[rid].items():
            ch = await bot.client.fetch_public_channel(cid)
            await ch.send(CardMessage(c))

    return web.Response(body="get you!", status=200)

# 基本请求，用于验证是否在线且能正常访问
@routes.get('/')
async def link_test(request:web.get):
    print(f"[request] / [{GetTime()}]")
    return web.Response(body="Hello", status=200)

@routes.post('/hook')
async def webhook(request: web.Request):
    print(f"[request] /hook [{GetTime()}]")
    try: 
        user_agent = request.headers["User-Agent"]
        if "git-oschina" in user_agent:
            return await gitee_webhook(request)
        elif "GitHub" in user_agent:
            return await github_webhook(request)
        else:
            return web.Response(body="Unsupported git platform", status=400)
    except:
        err_cur = str(traceback.format_exc())
        err_str = f"ERR! [{GetTime()}] /hook\n{err_cur}"
        return web.Response(body=err_str, status=400)

    # assert request.content_length < 1000000, "Request content too fat" # 1M
    # print("New commit by: {}".format((json.loads(body))['commits'][0]['author']['name']))


def card_help():
    c = Card(color=ui.default_color)
    c.append(Module.Header("第一步 配置URL"))
    c.append(Module.Section(Element.Text("在您的仓库下 前往**setting** -> **Webhooks**界面 并在**Payload URL**处填写以下url：\n`https://api.kookbot.cn/hook`",Types.Text.KMD)))
    c.append(Module.Header("第二步 Content type 选择 application/json"))
    c.append(Module.Header("第三步 Secret处输入任意字母或留空"))
    c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/GVNhpJJnj91e60pp.png')))
    c.append(Module.Header("第四步 点击页面底部Update Webhook"))
    c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/tj7t62gBsn1dp0pk.png')))
    c.append(Module.Header("第五步 输入绑定指令"))
    #add = '\n若有密钥，请添加在id后方\n例：`g.bind xxx-xxx-xxx-xxx 密钥`'
    text = f"[Github] 前往 **Recent Deliveries** 复制ping推送的id\n在kook输入命令 `g.bind [id]`\n例：`g.bind 5eb81820-4c93-11ed-96e9-87017811cb55`\n"
    text+= f"[Gitee]  复制浏览器url中的用户/仓库名\n在kook输入命令 `g.bind [repo]`\n例：仓库url为`https://gitee.com/oschina/git-osc.git`\n绑定命令为`g.bind oschina/git-osc`"
    c.append(Module.Section(Element.Text(text,Types.Text.KMD)))
    c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/PgZvhk66HF1dy0pm.png')))
    return CardMessage(c)


@bot.command(regex=r'(.+)', rules=[Rule.is_bot_mentioned(bot)])
async def bot_help_when_mentioned(msg: Message, d: str):
    try:
        await logging(msg)
        await msg.ctx.channel.send(card_help())
    except:
        print(f"ERR! [{GetTime()}] help_mentioned\n{traceback.format_exc()}")

@bot.command(regex=r'^(?:G|g|)(?:。|.|!|/|！|)(?:help|帮助)')
async def bot_help_message(msg: Message):
    try:
        await logging(msg)
        await msg.ctx.channel.send(card_help())
    except:
        print(f"ERR! [{GetTime()}] help_message\n{traceback.format_exc()}")

# github绑定
async def github_bind(msg:Message,d:str,dd:str):
    if d not in gh_ping_temp:
        await msg.ctx.channel.send(ui.card_uni(icon.error, 'github未向服务器推送webhook 请检查webhook设置'))
        return
    rid = gh_ping_temp[d]['rid']
    secret_state = gh_ping_temp[d]['secret']
    sign = gh_ping_temp[d]['sign']
    body = gh_ping_temp[d]['body']
    global gh_res_setting
    if dd != '':
        await msg.delete()
        if secret_state ==False:
            await msg.ctx.channel.send(ui.card_uni(icon.error, '您输入了secret但并未设置'))
            return
        digest, signature = sign.split("=", 1)
        assert digest == "sha1", "Digest must be sha1"  # use a whitelist
        h = hmac.HMAC(bytes(dd, "UTF8"), msg=json.dumps(body,ensure_ascii=True), digestmod=digest)
        if h.hexdigest() != signature:
            await msg.ctx.channel.send(ui.card_uni(icon.error, 'secret错误'))
            raise "Bad signature"
        global repo_secret
        repo_secret[rid] = dd
    else:
        if secret_state ==True:
            await msg.ctx.channel.send(ui.card_uni(icon.error, '缺少secret'))
            return
    gh_res_setting[rid] = {msg.ctx.channel.id: {'gid': msg.ctx.guild.id, 'aid': msg.author_id}}
    print(gh_res_setting)
    global gh_guild_setting
    if msg.ctx.guild.id not in gh_guild_setting:
        gh_guild_setting[msg.ctx.guild.id] = {'repo':{},'display': 0}

    gh_guild_setting[msg.ctx.guild.id]['repo'][rid] = msg.ctx.channel.id
    await msg.ctx.channel.send(ui.card_uni(icon.finished,'绑定github仓库成功！'))

# gitee绑定
async def gitee_bind(msg:Message,d:str,dd:str):
    if d not in ge_ping_temp:
        await msg.ctx.channel.send(ui.card_uni(icon.error, 'gitee未向服务器推送webhook 请检查webhook设置'))
        return
    
    rid = ge_ping_temp[d]['rid']
    global ge_res_setting
    ge_res_setting[rid] = {msg.ctx.channel.id: {'gid': msg.ctx.guild.id, 'aid': msg.author_id}}
    print(ge_res_setting)
    global ge_guild_setting
    if msg.ctx.guild.id not in ge_guild_setting:
        ge_guild_setting[msg.ctx.guild.id] = {'repo':{},'display': 0}

    ge_guild_setting[msg.ctx.guild.id]['repo'][rid] = msg.ctx.channel.id
    await msg.ctx.channel.send(ui.card_uni(icon.finished,'绑定gitee仓库成功！'))

@bot.command(regex=r'(?:G|g|git)(?:。|.|!|/|！|)(?:bind|绑定)(.+)')
async def bot_bind_repo(msg: Message, d: str):
    try:
        if await logging(msg,True):
            return

        l = d.split(' ')
        x = 0
        for i in copy.deepcopy(l):
            if i == '':
                l.pop(x)
            x+= 1
        if len(l) == 1:
            d = l[0]
            dd = ''
        elif len(l) == 2:
            d = l[0]
            dd = l[1]
        else:
            await msg.ctx.channel.send(ui.card_uni(icon.error, '参数错误'))
            return

        if "/" in d:
            await gitee_bind(msg,d,dd)
        elif "-" in d:
            await github_bind(msg,d,dd)
        else:
            await msg.reply(f"不支持的绑定")
        
    except:
        print(f"ERR! [{GetTime()}] bind\n{traceback.format_exc()}")


# @bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
# async def btn(b:Bot,e:Event):
#     aid = e.body['user_info']['id']
#     if 'guild_id' not in e.body:
#         channel_type = 'person'
#         channel = await b.client.fetch_user(aid)
#         await channel.send(ui.card_uni(icon.error,'请前往服务器频道使用该功能'))
#         return
#     channel_type = 'public'
#     user = await b.client.fetch_user(aid)
#     channel = await b.client.fetch_public_channel(e.body['target_id'])
#
#     val = json.loads(e.body['value'])
#     action = val['action']
#     if action == 'start':
#         aaid = val['aid']
#         if aaid != aid:
#             return


if __name__ == '__main__':
    app = web.Application()
    app.add_routes(routes)
    # loop = asyncio.new_event_loop()
    # timeout = aiohttp.ClientTimeout(total=10)
    asyncio.get_event_loop().run_until_complete(
        asyncio.gather(web._run_app(app, host='127.0.0.1', port=5461), bot.start()))