#from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings

def taibif_mail_contact_us(data):

    ret = {
        'message': {
            'head': '信件已送出',
            'content': ''
        }
    }

    # send to admin
    subject = '[taibif.tw] {} - {}'.format(
        data['cat'], data['name'])
    content = '''關於我們表單:

----------------------
問題分類: {}
姓名: {}
Email: {}
留言內容: {}
----------------------
'''.format(data['cat'], data['name'], data['email'], data['content'])
    #print (content)
    try:
        msg = EmailMessage(
            subject,
            content,
            settings.TAIBIF_SERVICE_EMAIL,
            [settings.TAIBIF_SERVICE_EMAIL],
            settings.TAIBIF_BCC_EMAIL_LIST.split(','),
            #reply_to=['another@example.com'],
            #headers={'Message-ID': 'foo'},
        )
        msg.send()
    except Exception as e:
        ret['message']['head'] = '有錯誤(admin)'
        ret['message']['content'] = e



    # send to user
    subject = '[taibif.tw] 關於我們留言: {}'.format(data['cat'])
    content = '''{} 您好，
TaiBIF 已經收到您的留言如下:
----------------------
問題分類: {}
姓名: {}
Email: {}
留言內容: {}
----------------------

感謝您的寶貴意見

TaiBIF
臺灣生物多樣性機構
'''.format(data['name'], data['cat'], data['name'], data['email'], data['content'])
    try:
        msg = EmailMessage(
            subject,
            content,
            settings.TAIBIF_SERVICE_EMAIL,
            [data['email']],
            #reply_to=['another@example.com'],
            #headers={'Message-ID': 'foo'},
        )
        msg.send()
    except Exception as e:
        ret['message']['head'] = '有錯誤(user)'
        ret['message']['content'] = e

    return ret
