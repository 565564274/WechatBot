import requests
from bs4 import BeautifulSoup


user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/65.0.3325.146 Safari/537.36')


def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    # 找到相应的标签和属性
    span_element = soup.find('span', id='text')
    # 提取文本
    desired_text = span_element.get_text(strip=True)
    if not desired_text:
        assert False, 'Could not find desired text'
    return desired_text


def get_yulu(type):
    if type == '舔狗日记':
        url = 'https://du.liuzhijin.cn/dog.php'
        error_msg = "舔狗日记插件出现故障，请联系开发者"
    elif type == '毒鸡汤':
        url = 'https://du.liuzhijin.cn/'
        error_msg = "毒鸡汤插件出现故障，请联系开发者"
    elif type == '社会语录':
        url = 'https://du.liuzhijin.cn/yulu.php'
        error_msg = "社会语录插件出现故障，请联系开发者"
    else:
        assert False, 'type error'
    try:
        headers = {
            'user-agent': user_agent
        }
        resp = requests.get(url, headers=headers)
        return parse_html(resp.text)
    except Exception as e:
        return error_msg


