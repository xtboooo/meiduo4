import random

from django.http import HttpResponse, JsonResponse
from django.views import View
from django_redis import get_redis_connection
from meiduo_mall.libs.captcha.captcha import captcha

import logging

from meiduo_mall.libs.yuntongxun.ccp_sms import CCP

logger = logging.getLogger('django')


# GET /image_codes/(?P<uuid>[\w-]+)/
class ImageCodeView(View):
    def get(self, request, uuid):
        """ 获取图片验证码数据 """
        # 1.生成图片验证码数据
        text, image = captcha.generate_captcha()

        # 2.保存图片验证码文本到redis
        redis_conn = get_redis_connection('verify_code')
        redis_conn.set('img_%s' % uuid, text, 300)

        # 3.返回图片验证码
        return HttpResponse(image, content_type='image/jpg')


# GET /sms_codes/(?P<mobile>1[3-9]\d{9})/
class SMSCodeView(View):
    def get(self, request, mobile):
        """ 获取短信验证码 """
        # 判断短信是否60s内重复发送
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)

        if send_flag:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码发送过于频繁!', })

        # 1.获取参数并校验
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 验证参数完整性
        if not all([image_code, uuid]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数!'})

        # 2.对比图片验证码
        # 获取redis中的图形验证码

        redis_image_code = redis_conn.get('img_%s' % uuid)

        if redis_image_code is None:
            return JsonResponse({'code': 400,
                                 'message': '图形验证码失效!'})

        # 删除redis中的文本验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        if image_code.lower() != redis_image_code.lower():
            return JsonResponse({'code': 400,
                                 'message': '输入图形验证码有误!'})

        # 3.生成保存并发送短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info('短信验证码为:%s' % sms_code)

        # 创建redis pipeline管道
        pl = redis_conn.pipeline()
        # 将redis请求操作添加到队列
        # 保存短信验证码
        pl.set('sms_%s' % mobile, sms_code, 300)

        # 设置短信发送的标记，有效期为：60s
        pl.set('send_flag_%s' % mobile, 1, 60)

        # 执行redis pipeline请求
        pl.execute()

        # 发送短信验证码
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        # 返回响应
        return JsonResponse({'code': 0,
                             'message': '发送短信成功!'})
