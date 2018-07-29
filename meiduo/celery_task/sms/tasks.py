from celery_task.main import app
from celery_task.sms.yuntongxun.sms import CCP
import logging

logger = logging.getLogger('django')

#发送短信验证码
@app.task
def send_sms_code(mobile,sms_code,SMS_CODE_REDIS_EXPIRES):
    """

    :param mobile: 手机号
    :param sms_code: 验证码
    :param SMS_CODE_REDIS_EXPIRES: 有效期
    :return: None
    """
    # #发送短信

    ccp = CCP()
    sms_code_expires = str(SMS_CODE_REDIS_EXPIRES//60)
    # # 注意： 测试的短信模板编号为1
    sms_code = str(sms_code)
    ccp.send_template_sms(mobile, [sms_code, sms_code_expires], 1)
