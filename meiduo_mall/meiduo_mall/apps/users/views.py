import json
import re

from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection
from django.middleware.csrf import get_token

from users.models import User


# GET /usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/
class UsernameCountView(View):
    def get(self, request, username):
        """ 判断注册用户名是否重复 """
        # 1.查询数据库判断username是否存在
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '操作数据库失败!'})
        # 2.返回响应数据
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'count': count, })


# GET /mobiles/(?P<mobile>1[3-9]\d{9})/count/
class MobileCountView(View):
    def get(self, request, mobile):
        """ 判断注册手机号是否重复 """
        # 1.查询数据库判断mobile是否存在
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '操作数据库失败!'})
        # 2.返回响应
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'count': count, })


# POST /register/
class RegisterView(View):
    def post(self, request):
        """ 注册用户信息保存 """
        # 1.获取参数并校验
        req_data = json.loads(request.body)
        username = req_data.get('username')
        password = req_data.get('password')
        password2 = req_data.get('password2')
        mobile = req_data.get('mobile')
        allow = req_data.get('allow')
        sms_code = req_data.get('sms_code')

        if not all([username, password, password2, mobile, allow, sms_code]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数!'})
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'code': 400,
                                 'message': 'username格式错误'})

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'message': 'password格式错误'})

        if password != password2:
            return JsonResponse({'code': 400,
                                 'message': '两次密码不一致'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'message': '手机号格式错误'})

        if not allow:
            return JsonResponse({'code': 400,
                                 'message': '请同意协议!'})

        # 2.短信验证码校验
        redis_conn = get_redis_connection('verify_code')
        redis_sms_code = redis_conn.get('sms_%s' % mobile)

        if redis_sms_code is None:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码过期'})

        if sms_code != redis_sms_code:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码错误'})

        # 3.保存用户信息到数据库
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile, )
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '数据库保存错误!'})

        # 登陆状态保存
        login(request, user)

        # 4.返回响应
        response = JsonResponse({'code': 0,
                                 'message': 'OK'})

        response.set_cookie('username',
                            user.username,
                            max_age=14 * 24 * 3600)
        return response


# GET /csrf_token/
class CSRFTokenView(View):
    def get(self, request):
        """ 获取csrf_token的值 """
        # 1.生成csrf_token的值
        csrf_token = get_token(request)

        # 2.返回csrf_token的值
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'csrf_token': csrf_token, })


# POST /login/
class LoginView(View):
    def post(self, request):
        """ 用户登录试图 """
        # 1.获取参数并校验
        req_data = json.loads(request.body)
        username = req_data.get('username')
        password = req_data.get('password')
        remember = req_data.get('remember')

        if not all([username, password]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        # 判断客户端传递的 username 参数是否符合手机号格式
        if re.match(r'^1[3-9]\d{9}$', username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

        # 2.判断密码是否正确
        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse({'code': 400,
                                 'message': '用户名或密码错误!'})

        # 3.登陆状态保存
        login(request, user)
        if not remember:
            # 如果未选择记住登录，浏览器关闭即失效
            request.session.set_expiry(0)

        # 4.返回响应数据
        response = JsonResponse({'code': 0,
                                 'message': 'OK'})

        response.set_cookie('username',
                            user.username,
                            max_age=14 * 24 * 3600)
        return response


# DELETE /logout/
class LogoutView(View):
    def delete(self, request):
        """ 退出登录 """
        # 1.删除用户的session数据
        logout(request)

        # 2.删除用户的cookie数据
        response = JsonResponse({'code': 0,
                                 'message': 'OK'})
        response.delete_cookie('username')

        # 3.返回响应
        return response
