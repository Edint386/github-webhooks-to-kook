from khl.card import Element,Card,CardMessage,Module,Types

class icon:
    error="https://img.kookapp.cn/assets/2022-09/D1nqrTszjQ0e80e8.png"
    finished="https://img.kookapp.cn/assets/2022-09/DknXSpwrlQ0e80e8.gif"

# 标注文本标准缩进 
blank = "        "

class ui:
    default_color="#7d5abb" # 可自定义
    # 卡片消息：uni
    def card_uni(icon, title, cause='',is_bold:bool = True,is_highlight:bool=True,card_color = default_color):
        # 在标题内加入>引用
        if title[:2] == '> ':
            title = title[2:]
            extra_w = '> '
        else:
            extra_w = ''

        text = extra_w + title
        c = Card(color=card_color)
        c.append(Module.Section(Element.Text(text, Types.Text.KMD), Element.Image(icon,circle=True)))
        if cause != '':
            if is_highlight == True:
                c.append(Module.Context(Element.Text(blank + cause, Types.Text.KMD)))
            else:
                c.append(Module.Context(Element.Text(blank + cause, Types.Text.KMD)))
        cm = CardMessage(c)
        return cm