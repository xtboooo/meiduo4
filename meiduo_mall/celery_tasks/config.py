"""
xtbo97
"""
# 指定broker中间人(消息队列)地址，本示例使用redis作为broker
# 格式：broker_url='redis://<redis-ip>:<redis-port>/<db>'
# 注意：将192.168.19.131改成自己的redis数据库ip，并且redis数据库一定要启动！！！
broker_url='redis://192.168.19.131:6379/3'