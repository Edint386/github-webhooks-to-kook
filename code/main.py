import asyncio
import uuid
import traceback
from typing import Union
import aiofiles
import aiohttp
import time
import copy
import io
import os
import json
from aiohttp import web, FormData
from aiohttp.web_request import Request
from khl import Bot, Message, PrivateMessage, EventTypes, Event, ChannelPrivacyTypes
from khl.card import Element, Card, CardMessage, Module, Types
from khl.command import Rule
from khl import Bot, Message, PrivateMessage, EventTypes, Event, ChannelPrivacyTypes, Cert
from card_ui import icon, ui

ppp = '\\]'
routes = web.RouteTableDef()
# 初始化bot
with open('config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
bot = Bot(token=config['token'])


# 获取当前时间
def GetTime():
    return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())


# 读取文件
async def read_file(path) -> dict:
    if not os.path.exists(path):
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps({}))
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        return json.loads(await f.read())


# 写入文件
async def write_file(path, value):
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, ))


async def img_requestor(img_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as r:
            return await r.read()

async def has_admin(aid, gid):
    user_roles = (await user_view(aid, gid))["roles"]
    roles = await (await bot.fetch_guild(gid)).fetch_roles()
    for i in roles:
        if i.id in user_roles and any([i.has_permission(0), i.has_permission(1)]):
            return True
    return False

repo_info = {'gitee': {}, 'github': {}}
repo_info_ex = {'gitee': {}, 'github': {
    '123456(repo_id)': {'name': 'Edint386/github-wehbhook-to-kook', 'repo_author': '131245125',
                        'push': {'342656(gid)': '4366734(cid)'}, 'message': ['xxx-xxxx-x-x--x-x-x-']}}}

name_to_rid = {}
name_to_rid_ex = {'Edint386/github-wehbhook-to-kook': {'github': '123456(repo_id)', 'gitee': ''}}

post_message_record = {"github": {}, "gitee": {}}
post_message_record_ex = {
    'github': {'xxxxxx-xxxxxx-xxxxxx-xxxxx-xxxxx': {'rid': '123456', 'time': '1666666666', 'body': {}}}, 'gitee': {}}

bind_request_temp = {}
bind_request_temp_ex = {'仓库名': {'aid': '131244241', 'cid': '5436443636634'}}

guild_setting = {}
guild_setting_ex = {'53456436436(gid)': {'repo': [{'rid': '13124', 'binder': '21434', 'platform': 'github'}],
                                         'display': {'push': 0, 'release': 0}}}

com_temp = {}
com_temp_ex = {'324235(aid)': {'choose_repo(command_type)': {'rid': '000'}}}

path_repo = 'log/repo_setting.json'
path_guild = 'log/guild_setting.json'
path_ping = 'log/ping_temp.json'
path_bind = 'log/bind_temp.json'
path_repo_name = 'log/name_to_id.json'


# 开机加载
@bot.task.add_date()
async def tgrds():
    try:  # github
        global repo_info, guild_setting, name_to_rid, post_message_record, bind_request_temp
        repo_info = await read_file(path_repo)
        guild_setting = await read_file(path_guild)
        name_to_rid = await read_file(path_repo_name)
        bind_request_temp = await read_file(path_bind)
        post_message_record = await read_file(path_ping)
        # 添加在函数末端
        if not repo_info:
            repo_info = {'github': {}, 'gitee': {}}
        if not post_message_record:
            post_message_record = {'github': {}, 'gitee': {}}
    except:
        print(f"ERR while starting!\n{traceback.format_exc()}")
        os._exit(-1)


# 定时保存
@bot.task.add_interval(seconds=60)
async def save_Data():
    await write_file(path_repo, repo_info)
    await write_file(path_guild, guild_setting)
    await write_file(path_ping, post_message_record)
    await write_file(path_repo_name, name_to_rid)
    await write_file(path_bind, bind_request_temp)

    print(f"[{GetTime()}] save_data success!")


# 在控制台打印msg内容，用作日志
async def logging(msg: Message, PrivateBan=False):
    now_time = GetTime()
    if isinstance(msg, PrivateMessage):
        log_str = f"[{now_time}] PrivateMessage - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} = {msg.content}"
        if PrivateBan:
            log_str += " ban"
            await msg.reply(f"本命令需要在公共频道使用！")
        print(log_str)
        return True
    else:
        print(
            f"[{now_time}] G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} = {msg.content}")
        return False


async def upd_card(msg_id: str, content, target_id='', channel_type: Union[ChannelPrivacyTypes, str] = 'public',
                   bot=bot):
    content = json.dumps(content)
    data = {'msg_id': msg_id, 'content': content}
    if target_id != '':
        data['temp_target_id'] = target_id
    if channel_type == 'public' or channel_type == ChannelPrivacyTypes.GROUP:
        result = await bot.client.gate.request('POST', 'message/update', data=data)
    else:
        result = await bot.client.gate.request('POST', 'direct-message/update', data=data)
    return result


async def upd_msg(msg_id: str, content: str, channel_type: Union[str, ChannelPrivacyTypes] = 'public', bot=bot):
    if channel_type == 'public' or channel_type == ChannelPrivacyTypes.GROUP:
        result = await bot.client.gate.request('POST', 'message/update', data={'msg_id': msg_id, 'content': content})
    else:
        result = await bot.client.gate.request('POST', 'direct-message/update',
                                               data={'msg_id': msg_id, 'content': content})
    return result


async def msg_view(mid, b=bot):
    return await b.client.gate.request('GET', 'message/view', params={'msg_id': mid})


async def user_view(aid, gid):
    return await bot.client.gate.request('GET', 'user/view', params={'user_id': aid, 'guild_id': gid})


# 基本请求，用于验证是否在线且能正常访问
@routes.get('/')
async def link_test(request: web.get):
    print(f"[request] / [{GetTime()}]")
    return web.Response(body="HELLO! Do you want to view bot? pleasme go to www.botarket.cn", status=200)


@routes.post('/hook')
async def webhook(request: web.Request):
    print(f"[request] /hook [{GetTime()}]")
    try:
        global post_message_record, name_to_rid, repo_info
        user_agent = request.headers["User-Agent"]
        body = await request.content.read()
        data = json.loads(body.decode('UTF8'))
        if "git-oschina" in user_agent:
            platform = 'gitee'
            Etype = request.headers['X-Gitee-Event']
            if Etype != "Push Hook":
                return web.Response(body="Unsupported gitee event!", status=400)

            sender_name = data["sender"]["login"]
            did = f'{uuid.uuid1()}'
        elif "GitHub" in user_agent:
            platform = 'github'
            Etype = request.headers['X-GitHub-Event']
            did = request.headers['X-GitHub-Delivery']
            sender_name = data["sender"]["login"]
        else:
            return web.Response(body="Unsupported git platform", status=400)
        repo_url = data["repository"]['url']
        rid = str(data["repository"]["id"])
        repo_name = data["repository"]["full_name"]
        sender_url = data["sender"]['url']
        sender_avatar = data["sender"]["avatar_url"]
        bhash = data['before'][:7] if 'before' in data else ''
        ahash = data['after'][:7] if 'after' in data else ''
        compare = data['compare'] if 'compare' in data else ''
        
   
        post_message_record[platform][did] = {'rid': rid, 'body': data}
        print(f"[{Etype}] from {repo_name}, rid:{rid}")
        if repo_name not in name_to_rid:
            name_to_rid[repo_name] = {platform: rid}
        else:
            name_to_rid[repo_name][platform] = rid
        if rid not in repo_info[platform]:
            repo_info[platform][rid] = {'name': repo_name, 'push': {}, 'message': [did]}
        elif rid in repo_info[platform]:
            repo_info[platform][rid]['message'].append(did)

        if repo_name in bind_request_temp:
            aaid = bind_request_temp[repo_name]['aid']
            ccid = bind_request_temp[repo_name]['cid']
            ccc = await bot.client.fetch_public_channel(ccid)
            bind_add(platform, rid, ccc.guild_id, ccid, aaid)
        else:

            for k, v in bind_request_temp.items():
                if repo_name.lower() == k.lower():
                    aaid = bind_request_temp[repo_name.lower()]['aid']
                    ccid = bind_request_temp[repo_name.lower()]['cid']
                    ccc = await bot.client.fetch_public_channel(ccid)
                    c = Card(color=ui.default_color)
                    c.append(Module.Header('请确认以下是否为您的仓库'))
                    c.append(Module.Section(
                        Element.Text(f'[{sender_name}]({sender_url})\n[{repo_name}]({repo_url})', Types.Text.KMD),
                        Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
                    c.append(Module.Divider())
                    c.append(Module.ActionGroup(
                        Element.Button('    是    ', json.dumps(
                            {'action': 'choose_repo', 'data': [{'rid': rid, 'platform': platform}]})),
                        Element.Button('    否    ', json.dumps({'action': 'choose_repo', 'data': []}),
                                       theme=Types.Theme.DANGER)))
                    bind_add(platform, rid, ccc.guild_id, ccid, aaid, k.lower)
                    await (await bot.client.fetch_public_channel(bind_request_temp[repo_name.lower()]['cid'])).send(
                        CardMessage(c))

        if Etype == 'ping':
            return web.Response(body="Pong!", status=200)
        elif Etype == 'push':
            if "refs/tags" in data["ref"]:
                return web.Response(body="only handle user.push", status=200)
        elif Etype == 'release':
            if data["action"] != "published":
                return web.Response(body="wait for release.published", status=200)
        else:
            return web.Response(body="Unsupported github event!", status=400)

        time_words = f'at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}'

        for gid, cid in repo_info[platform][rid]['push'].items():
            ch = await bot.client.fetch_public_channel(cid)
            card_type = guild_setting[gid]['display'][Etype]
            if Etype == 'push':
                if card_type == 0:
                    commit_num = len(data["commits"])  # commit数量
                    # 为多个commit显示message
                    # message = '-/-/-/-/-/-/-/-/-/-/-/-/--/-/---/-/-/--/-/'.join([f"{i['message']}\n by:[{i['committer']['name']}](https://github.com/{i['committer']['username']})" for i in data['commits'] if 'Signed-off-by' not in i['message']])

                    message = '-/-/-/-/-/-/-/-/-/-/-/-/--/-/---/-/-/--/-/'.join([
                                                                                    f"**[{i['committer']['name'].replace(']', ppp)}](https://github.com/{i['committer']['username']}):**\n{i['message']}"
                                                                                    for i in data['commits'] if
                                                                                    'Signed-off-by' not in i[
                                                                                        'message']])

                    while message.find('\n\n') > 0:
                        message = message.replace('\n\n', '\n')
                    message = message.replace('-/-/-/-/-/-/-/-/-/-/-/-/--/-/---/-/-/--/-/', '\n\n> ')
                    c = Card(color=ui.default_color)
                    c.append(Module.Header(f'New Push Event from Github'))
                    c.append(Module.Context(f"{commit_num} commit{'s' if commit_num > 1 else ''} {time_words}"))
                    c.append(Module.Section(Element.Text(
                        f'[{sender_name.replace("]", ppp)}]({sender_url})\n[{repo_name.replace("]", ppp)}]({repo_url})',
                        Types.Text.KMD),
                                            Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
                    c.append(Module.Divider())
                    if bhash != '':
                        c.append(Module.Context(
                            Element.Text(f'**Hash:**\n>  [{bhash} -> {ahash.replace("]",ppp)}]({compare})',
                                         Types.Text.KMD)))
                    print(f"[github repo:{repo_name} = {message} ]")
                    c.append(Module.Context(Element.Text(f'**Message:**\n> {message}', Types.Text.KMD)))
                elif card_type == 1:
                    c = Card(color=ui.default_color)
                    ...
                else:
                    raise "card_type doesn't exist"

            elif Etype == 'release':
                if card_type == 0:
                    tag_name = data["release"]["tag_name"]
                    release_name = data["release"]["name"]
                    release_body = data["release"]["body"]
                    release_url = data["release"]["html_url"]
                    c = Card(color=ui.default_color)
                    c.append(Module.Header(f'New Release Event from Github'))
                    c.append(Module.Section(Element.Text(
                        f'[{sender_name.replace("]", ppp)}]({sender_url}) release {release_name}\n[{repo_name.replace("]", ppp)}]({repo_url})',
                        Types.Text.KMD),
                                            Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
                    c.append(Module.Divider())
                    c.append(Module.Context(
                        Element.Text(f'**Tag:**\n>  [{tag_name.replace("]", ppp)}]({release_url})', Types.Text.KMD)))
                    c.append(Module.Context(Element.Text(f'**Info:**\n> {release_body}', Types.Text.KMD)))
                else:
                    raise "card_type doesn't exist"
            else:
                raise 'egassagouiop'
            await ch.send(CardMessage(c))
        return web.Response(body=json.dumps({'message': 'Success!', 'id': did}), status=200,
                            content_type='application/json')
    except:
        err_cur = str(traceback.format_exc())
        err_str = f"ERR! [{GetTime()}] /hook\n{err_cur}"
        print(err_str)
        return web.Response(body=err_str, status=400)

    # assert request.content_length < 1000000, "Request content too fat" # 1M
    # print("New commit by: {}".format((json.loads(body))['commits'][0]['author']['name']))


def card_help():
    c = Card(color=ui.default_color)
    c.append(Module.Header('基础指令'))
    c.append(Module.Section('`g.bind 仓库名` | 绑定仓库'))
    c.append(Module.Section('`g.gsetting` | 服务器设置（绑定仓库，卡片样式）（仅管理员可用）'))
    c.append(Module.Header("第一步 配置URL"))
    c.append(Module.Section(
        Element.Text(
            "在您的仓库下 前往**setting** -> **Webhooks**界面 并在**Payload URL**处填写以下url：\n`https://api.kookbot.cn/hook`",
            Types.Text.KMD)))
    c.append(Module.Header("第二步 Content type 选择 application/json"))
    # c.append(Module.Header("第三步 Secret处输入任意字母或留空"))
    c.append(Module.Header("第三步 Secret处留空"))
    # c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/GVNhpJJnj91e60pp.png')))
    c.append(Module.Header("第四步 点击页面底部Update Webhook"))
    c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/tj7t62gBsn1dp0pk.png')))
    c.append(Module.Header("第五步 输入绑定指令"))
    c.append(Module.Section(Element.Text( "例：`g.bind Edint386/github-webhooks-to-kook`")))
    # add = '\n若有密钥，请添加在id后方\n例：`g.bind xxx-xxx-xxx-xxx 密钥`'
    # text = f"[Github] 前往 **Recent Deliveries** 复制ping推送的id\n在kook输入命令 `g.bind {'{id}'}`\n例：`g.bind 5eb81820-4c93-11ed-96e9-87017811cb55`\n"
    # text += f"[Gitee]  复制浏览器url中的用户/仓库名\n在kook输入命令 `g.bind {'{repo}'}`\n例：仓库url为`https://gitee.com/oschina/git-osc.git`\n绑定命令为`g.bind oschina/git-osc`"
    # c.append(Module.Section(Element.Text(text, Types.Text.KMD)))
    # c.append(Module.Container(Element.Image('https://img.kookapp.cn/assets/2022-10/PgZvhk66HF1dy0pm.png')))
    return CardMessage(c)


async def com_help(msg):
    try:
        await logging(msg)
        await msg.ctx.channel.send(card_help())
    except:
        print(f"ERR! [{GetTime()}] help_mentioned\n{traceback.format_exc()}")


@bot.command(regex=r'(.+)', rules=[Rule.is_bot_mentioned(bot)])
async def bot_help_when_mentioned(msg: Message, d: str):
    await com_help(msg)


@bot.command(regex=r'^(?:G|g|)(?:。|.|!|/|！|)(?:help|帮助)')
async def bot_help_message(msg: Message):
    await com_help(msg)


def bind_add(platform, rid, gid, cid, aid, repo_name=''):
    global repo_info, guild_setting, bind_request_temp
    repo_info[platform][rid]['push'][gid] = cid
    if gid not in guild_setting:
        guild_setting[gid] = {'repo': [], 'display': {'push': 0, 'release': 0}}
    guild_setting[gid]['repo'].append({'rid': rid, 'binder': aid, 'platform': platform})
    if repo_name != '':
        del bind_request_temp[repo_name]
    elif repo_info[platform][rid]['name'] in bind_request_temp:
        del bind_request_temp[repo_info[platform][rid]['name']]


def remove_repeat(l: list) -> list:
    ll = []
    for i in l:
        if i not in ll:
            ll.append(i)
    return ll


def bind_del(gid, rid='', platform='', binder='', data=''):
    global repo_info, guild_setting, bind_request_temp

    guild_setting[gid]['repo'] = remove_repeat(guild_setting[gid]['repo'])
    if data == "":
        del repo_info[platform][rid]['push'][gid]
        guild_setting[gid]['repo'].pop(
            guild_setting[gid]['repo'].index({'rid': rid, 'binder': binder, 'platform': platform}))

    else:
        del repo_info[platform][rid]['push'][gid]
        guild_setting[gid]['repo'].pop(
            guild_setting[gid]['repo'].index(data))


def bind_add_by_name(name, gid, cid, aid):
    d = name
    rrrr = name_to_rid[d]
    platform = list(rrrr.keys())[0]
    rid = str(name_to_rid[d][platform])
    bind_add(platform, rid, gid, cid, aid)


bind_trust_card = []


@bot.command(regex=r'(?:G|g|git)(?:。|.|!|/|！|)(?:bind|绑定)(?: |)(.+)')
async def bot_bind_repo(msg: Message, d: str):
    try:
        global bind_request_temp, repo_info, guild_setting
        if await logging(msg, True):
            return
        Trust = 0

        if d in name_to_rid:
            Trust = 3
            if len(name_to_rid[d]) > 1:
                Trust = 1
        else:
            for k, v in name_to_rid.items():
                if d.lower() == k.lower():
                    Trust = 2
        c = Card(ui.default_color)
        if Trust == 0:
            bind_request_temp[d] = {'aid': msg.author_id, 'cid': msg.ctx.channel.id}
            cm = ui.card_uni(icon.finished, '已经为您记录仓库名称，将在下次事件推送时自动绑定')
        elif Trust == 3:
            bind_add_by_name(d, msg.ctx.guild.id, msg.ctx.channel.id, msg.author_id)
            cm = ui.card_uni(icon.finished, f'已绑定 {d} 至 (chn){msg.ctx.channel.id}(chn)')
        elif Trust in [1, 2]:
            # n = 1
            l = []
            for platform, data in name_to_rid[d].items():
                c.append(Module.Header('请确认以下是否为您的仓库'))
                if platform == 'gitee':
                    repo_url = data["repository"]['url']
                    sender_name = data["sender"]["login"]
                elif platform == 'github':
                    repo_url = data["project"]['url']
                    sender_name = data["sender"]["name"]
                else:
                    raise 'platform DNE'
                rid = str(data["repository"]["id"])
                l.append({'rid': rid, 'platform': platform, 'binder': msg.author_id})
                repo_name = data["repository"]["full_name"]
                sender_url = data["sender"]['url']
                sender_avatar = data["sender"]["avatar_url"]
                c.append(Module.Section(
                    Element.Text(
                        f'[{sender_name.replace("]", ppp)}]({sender_url})\n[{repo_name.replace("]", ppp)}]({repo_url})',
                        Types.Text.KMD),
                    Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
                # global com_temp
                # com_temp[msg.author_id]['choose_repo'] = {'rid': rid}
                c.append(Module.Divider())
                # if n < platform_length:
                #     c.append(Module.Divider())
                #     n += 1
            if Trust == 1:
                c.append(Module.ActionGroup(
                    Element.Button('  第一  ', json.dumps({'action': 'choose_repo', 'data': [l[0]]}),
                                   theme=Types.Theme.SECONDARY),
                    Element.Button('  第二  ', json.dumps({'action': 'choose_repo', 'data': [l[1]]}),
                                   theme=Types.Theme.SECONDARY),
                    Element.Button('  二者  ', json.dumps({'action': 'choose_repo', 'data': [l[1], l[0]]})),
                    Element.Button(' 非二者 ', json.dumps({'action': 'choose_repo', 'data': []}),
                                   theme=Types.Theme.DANGER)))

            elif Trust == 2:
                c.append(Module.ActionGroup(
                    Element.Button('    是    ', json.dumps({'action': 'choose_repo', 'data': [l[0]]})),
                    Element.Button('    否    ', json.dumps({'action': 'choose_repo', 'data': []}),
                                   theme=Types.Theme.DANGER)))
            cm = CardMessage(c)
        else:
            cm = ui.card_uni(icon.error, '发生错误 请联系开发者')
        await msg.ctx.channel.send(cm)
    except:
        print(f"ERR! [{GetTime()}] bind\n{traceback.format_exc()}")


@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btn(b: Bot, e: Event):
    aid = e.body['user_info']['id']
    mid = e.body['msg_id']
    if 'guild_id' not in e.body:
        channel_type = 'person'
        channel = await b.client.fetch_user(aid)
        await channel.send(ui.card_uni(icon.error, '请前往服务器频道使用该功能'))
        return
    channel_type = 'public'
    gid = e.body['guild_id']
    user = await b.client.fetch_user(aid)
    channel = await b.client.fetch_public_channel(e.body['target_id'])
    val = json.loads(e.body['value'])
    action = val['action']
    data = val['data'] if 'data' in val else {}
    if action == 'choose_repo':
        binder = data[0]['binder']
        if aid != binder:
            content = (await msg_view(mid))["content"]
            await upd_card(mid, ui.card_uni(icon.error, '您不是绑定请求发起者'), aid)
            await asyncio.sleep(1.5)
            await upd_card(mid, content, aid)
        if data == []:
            await channel.send(ui.card_uni(icon.finished, '命令取消'))
            return
        for i in data:
            rid = i['rid']
            platform = i['platform']
            bind_add(platform, rid, channel.guild_id, channel.id, binder)
            await channel.send(
                ui.card_uni(icon.finished, f'已绑定 {repo_info[platform][rid]["name"]} 至 (chn){channel.id}(chn)'))
    elif action == 'del_repo':
        bind_del(gid, data=data)
        if has_admin(aid,gid):
            await channel.send(
                ui.card_uni(icon.finished, f'已解除订阅仓库{repo_info[data["platform"]][data["rid"]]["name"]}'))
            return
        await upd_card(mid, ui.card_uni(icon.error, '权限不足，您不是该服务器管理员'), aid)
        content = (await msg_view(mid))["content"]
        await asyncio.sleep(1.4)
        await upd_card(mid, content, aid)

    elif action == "card_setting":
        await channel.send(card_setting(gid, data))


def card_setting(gid, mode='view'):
    global guild_setting
    guild_setting[gid]['repo'] = remove_repeat(guild_setting[gid]['repo'])
    repo_list: list = copy.deepcopy(guild_setting[gid]['repo'])
    c = Card(color=ui.default_color)
    for i in repo_list:
        if 'platform' not in i:
            flag = 1
            for p, v in repo_info.items():
                if i['rid'] in v:
                    index = repo_list.index(i)
                    guild_setting[gid]['repo'].pop(index)
                    i['platform'] = p
                    guild_setting[gid]['repo'].append(i)
                    flag = 0
            if flag == 1:
                raise 'gfrdshdhiodjhio'
        platform = i['platform']
        print(platform)
        last_msg = repo_info[platform][i['rid']]['message'][0]
        data = post_message_record[platform][last_msg]['body']
        if platform == 'gitee':
            sender_name = data["sender"]["login"]
        elif platform == 'github':
            print(data["sender"])
            sender_name = data["sender"]["login"]
        else:
            raise 'platform DNE'
        repo_url = data["repository"]['url']
        repo_name = data["repository"]["full_name"]
        sender_url = data["sender"]['url']
        sender_avatar = data["sender"]["avatar_url"]
        c.append(Module.Section(
            Element.Text(
                f'[{sender_name.replace("]", ppp)}]({sender_url})\n[{repo_name.replace("]", ppp)}]({repo_url})',
                Types.Text.KMD),
            Element.Image(sender_avatar), mode=Types.SectionMode.LEFT))
        current_repo_info = repo_info[platform][i["rid"]]
        text = f'> 订阅者：(met){i["binder"]}(met)   \n频道：(chn){current_repo_info["push"][gid]}(chn)   \n所有者：{"暂无" if "author" not in current_repo_info else current_repo_info["author"]}'
        if mode == 'view':
            c.append(Module.Context(text))
        elif mode == 'modify':
            c.append(Module.Section(text, Element.Button('删除', json.dumps({'action': 'del_repo', 'data': i}),
                                                         theme=Types.Theme.DANGER)))
        c.append(Module.Divider())
    if mode == 'view':
        c.append(Module.ActionGroup(
            Element.Button('   管理订阅   ', json.dumps({'action': 'card_setting', 'data': 'modify'}),
                           theme=Types.Theme.DANGER)))
    elif mode == 'modify':
        c.append(Module.ActionGroup(
            Element.Button('    返回    ', json.dumps({'action': 'card_setting', 'data': 'view'}),
                           theme=Types.Theme.SECONDARY)))
    return CardMessage(c)


@bot.command(regex=r'(?:G|g|git)(?:。|.|!|/|！|)(?:服务器设置|gsetting)')
async def setting(msg: Message):
    try:
        cm = card_setting(msg.ctx.guild.id)
        await msg.ctx.channel.send(cm)
    except:
        print(f"ERR command guild setting!\n{traceback.format_exc()}")


if __name__ == '__main__':
    app = web.Application()
    app.add_routes(routes)
    # loop = asyncio.new_event_loop()
    # timeout = aiohttp.ClientTimeout(total=10)
    asyncio.get_event_loop().run_until_complete(
        asyncio.gather(web._run_app(app, host='0.0.0.0', port=14726), bot.start()))
