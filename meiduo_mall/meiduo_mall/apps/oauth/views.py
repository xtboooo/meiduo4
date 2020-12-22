from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django.http import JsonResponse
from django.views import View


# GET /qq/authorization/?next=<登录之后的访问地址>
class QQLoginView(View):
    def get(self, request):
        """ 获取QQ登录网址 """

        next1 = request.GET.get('next', '/')

        # 1.创建OAuthQQ对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next1)

        # 2.获取QQ登陆网址并返回
        login_url = oauth.get_qq_url()

        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'login_url': login_url,})
