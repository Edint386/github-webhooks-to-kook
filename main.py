import asyncio
import hmac

import aiofiles
from khl import *
import aiohttp
import copy
import io
import json
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageFilter, ImageEnhance
from aiohttp import web, FormData
from aiohttp.web_request import Request
from khl.command import Rule

from card_ui import *
repo_secret = {}
ping_temp = {}
com_temp = {}

guild_setting = {}
routes = web.RouteTableDef()

bot = Bot(token='xxxxxxxxxxxxxxxxxx')
f.close()

# 读取文件
async def read_file(path) -> dict:
    async with aiofiles.open(path,'r',encoding='utf-8') as f:
        return json.loads(await f.read())

# 写入文件
async def write_file(path, value):
    async with aiofiles.open(path, 'w',encoding='utf-8') as f:
        await f.write(json.dumps(value,ensure_ascii=False))

path_repo = 'temp\\repo_setting.txt'
path_guild = 'temp\\guild_setting.txt'
path_did = 'temp\\did_temp.txt'
path_secret = 'temp\\secret.txt'
@bot.task.add_date()
async def tgrds():
    global res_setting
    res_setting = await read_file(path_repo)
    global guild_setting
    guild_setting = await read_file(path_guild)
    global ping_temp
    ping_temp = await read_file(path_did)
    global repo_secret
    repo_secret = await read_file(path_secret)






@bot.task.add_interval(seconds=60)
async def save_Data():
    await write_file(path_repo,res_setting)
    await write_file(path_guild,guild_setting)
    await write_file(path_did,ping_temp)
    await write_file(path_secret,repo_secret)




@routes.post('/hook')
async def github_webhook(request: web.Request):
    type = request.headers['X-GitHub-Event']
    did = request.headers['X-GitHub-Delivery']
    if 'X-HUB-SIGNATURE' in request.headers:
        secret_state = True
        sign = request.headers['X-HUB-SIGNATURE']
    else:
        secret_state = False
        sign = ''
    body = await request.content.read()
    data = json.loads(body.decode('UTF8'))
    rid = str(data["repository"]["id"])
    ping_temp[did] = {'rid': rid, 'secret': secret_state, 'sign': sign,'body':data}
    if type == 'ping':
        print('ping')
        return web.Response(body="Pong!", status=200)

    repo_name = data["repository"]["full_name"]
    repo_url = data["repository"]['url']
    sender_name = data["sender"]["login"]
    sender_url = data["sender"]["url"]
    sender_avatar = data["sender"]["avatar_url"]
    bhash = data['before'] if 'before' in data else ''
    ahash = data['after'] if 'after' in data else ''
    compare = data['compare']
    message :str= data["commits"][0]["message"]

    if rid in res_setting:

        c = Card(color=ui.default_color)
        c.append(Module.Header(f'New {type} Event'))
        c.append(Module.Section(Element.Text(f'> [{sender_name}]({sender_url}) \n[{repo_name}]({repo_url})'),
                                Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
        c.append(Module.Divider())
        if bhash != '':
            c.append(Module.Context(f'> Hash:\n[{bhash} -> {ahash}]({compare})'))
        print(message)
        while message.find('\n\n') >0:
            message = message.replace('\n\n','\n')
        c.append(Module.Context(f'> Message:\n**{message}**'))

        for cid, v in res_setting[rid].items():
            ch = await bot.client.fetch_public_channel(cid)

            if 'secret' in repo_secret:
                secret = repo_secret['secret']
                digest, signature = request.headers['X-HUB-SIGNATURE'].split("=", 1)
                assert digest == "sha1", "Digest must be sha1"  # use a whitelist
                h = hmac.HMAC(bytes(secret, "UTF8"), msg=body, digestmod=digest)


                await ch.send(
                    ui.card_uni(icon.error, 'secret错误', f'repo:[{repo_name}]({repo_url})', is_highlight=False))
                assert h.hexdigest() == signature, "Bad signature"
            await ch.send(CardMessage(c))
    return web.Response(body="Hi", status=200)

    # assert request.content_length < 1000000, "Request content too fat" # 1M

    # print("New commit by: {}".format((json.loads(body))['commits'][0]['author']['name']))


def card_help():
    c = Card(color=ui.default_color)
    # c.append(Module.Context('tips:完成操作后请点击底部按钮'))
    c.append(Module.Header('第一步 配置URL'))
    c.append(Module.Section(
        '在您的仓库下 前往**setting** -> **Webhooks**界面 并在**Payload URL**处填写以下url：\n`https://api.kookbot.cn/hook`'))
    c.append(Module.Header('第二步 Content type 选择 application/json'))
    c.append(Module.Header('第三步 Secret处输入任意字母或留空'))
    c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/GVNhpJJnj91e60pp.png')))
    c.append(Module.Header('第四步 点击页面底部Update Webhook'))
    c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/tj7t62gBsn1dp0pk.png')))
    c.append(Module.Header('第五步 输入绑定指令'))
    add = '\n若有密钥，请添加在id后方\n例：`g.bind xxx-xxx-xxx-xxx xxxxxx`'
    c.append(Module.Section(
        f'前往 **Recent Deliveries** 复制ping推送的id 返回开黑啦输入以下命令\n`g.bind {id}`\n例：`g.bind 5eb81820-4c93-11ed-96e9-87017811cb55`{add}'))

    c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/PgZvhk66HF1dy0pm.png')))
    # c.append(Module.ActionGroup(Element.Button('       我已完成上述操作      ',f'{"aid":"{aid}"},"action":"start"',theme=Types.Theme.SECONDARY)))
    # global com_temp
    # com_temp[aid] = 'start'
    return CardMessage(c)


@bot.command(regex=r'(.+)', rules=[Rule.is_bot_mentioned(bot)])
async def bot1_help_when_mentioned(msg: Message, d: str):
    await msg.ctx.channel.send(card_help())


@bot.command(regex=r'^(?:G|g|)(?:。|.|!|/|！|)(?:help|帮助)')
async def hhelp(msg: Message):
    await msg.ctx.channel.send(card_help())


@bot.command(regex=r'(?:G|g|git)(?:。|.|!|/|！|)(?:bind|绑定)(.+)')
async def bot1_add_uuid(msg: Message, d: str):
    print(d)
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
    if d not in ping_temp:
        await msg.ctx.channel.send(ui.card_uni(icon.error, 'github未向服务器推送webhook 请检查webhook设置'))
        raise 'webhook error'
    rid = ping_temp[d]['rid']
    secret_state = ping_temp[d]['secret']
    sign = ping_temp[d]['sign']
    body = ping_temp[d]['body']
    global res_setting
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
    res_setting[rid] = {msg.ctx.channel.id: {'gid': msg.ctx.guild.id, 'aid': msg.author_id}}
    print(res_setting)
    global guild_setting
    if msg.ctx.guild.id not in guild_setting:
        guild_setting[msg.ctx.guild.id] = {'repo':{},'display': 0}

    guild_setting[msg.ctx.guild.id]['repo'][rid] = msg.ctx.channel.id
    await msg.ctx.channel.send(ui.card_uni(icon.finished,'绑定成功！'))




# @bot.command


# @bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
# async def btn(b:Bot,e:Event):
#     aid = e.body['user_info']['id']
#
#
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
    asyncio.get_event_loop().run_until_complete(
        asyncio.gather(web._run_app(app, host='0.0.0.0', port=14726), bot.start()))




