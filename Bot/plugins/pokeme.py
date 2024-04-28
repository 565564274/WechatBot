import random

a = ['那...那里...那里不能戳...绝对...', '嘤嘤嘤,好疼', '你再戳，我就把你的作案工具没收了，哼哼~',
     '别戳了别戳了，戳怀孕了',
     '嘤嘤嘤，人家痛痛', '我错了我错了，别戳了', '桥豆麻袋,别戳老子', '手感怎么样', '戳够了吗？该学习了',
     '戳什么戳，没戳过吗',
     '你用左手戳的还是右手戳的？', '不要啦，别戳啦', '给你一拳', '再摸就是狗', '你这么闲吗？', '代码写完了吗？', '爬去学习']

pre = 0


def pokeme_reply():
    try:
        global pre
        k = random.randint(0, len(a) - 1)
        while pre == k:
            k = random.randint(0, len(a) - 1)
        pre = k
        return a[k]
    except Exception as e:
        return "戳一戳插件出现故障，请联系开发者"

