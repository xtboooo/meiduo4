"""
xtbo97
"""
from celery_tasks.main import celery_app
from celery_tasks.sms.yuntongxun.ccp_sms import CCP


@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """ 封装任务函数 """
    print('手机号是: %s短信验证码为:%s' % (mobile, sms_code))
    # CCP().send_template_sms(mobile, [sms_code, 5], 1)

