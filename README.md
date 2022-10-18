# github-webhooks-to-kook
一款GitHub事件推送的KOOK机器人  [邀请链接](https://www.kookapp.cn/app/oauth2/authorize?id=13188&permissions=14352&client_id=J4JeHxjpdALjb_VT&redirect_uri=&scope=bot)  

## TO DO

- [ ] 增加其他类型Events
- [ ] 卡片模块可进行多选  
- [ ] 使用url后跟channel_id参数进行快速绑定（考虑中） 

## 注意事项

### 配置文件
使用前，请在`code/config`文件夹中添加`config.json`写入你的`kook-bot-token(websocket）`

示例如下
```json
{
    "token":"kook-bot-websocket-token"
}
```
除此之外，还需要在`code/log`文件夹中添加四个空的json文件
```
repo_setting.json
guild_setting.json
did_temp.json
secret.json
```
内容需填为`{}` 否则会影响bot开机加载文件

### 关于event loop报错

bot启动的时候，你可能会接收到下面这个报错。直接忽略即可，其不影响使用

```
/home/muxue/kook/webhook/code/main.py:284: DeprecationWarning: There is no current event loop
  asyncio.get_event_loop().run_until_complete(
/home/muxue/kook/webhook/code/main.py:285: DeprecationWarning: There is no current event loop
  asyncio.gather(web._run_app(app, host='127.0.0.1', port=5461), bot.start()))
```