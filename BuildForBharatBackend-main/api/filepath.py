from datetime import datetime


def gst_certificate_path(instance, filename):
    return f'thumb/categories/{datetime.now().year}/{datetime.now().month}/{datetime.now().day}/{instance}-{filename}'


def business_profile_pic_path(instance, filename):
    return f'business/pic/{datetime.now().year}/{datetime.now().month}/{datetime.now().day}/{instance}-{filename}'
