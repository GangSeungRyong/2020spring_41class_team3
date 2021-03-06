from django.db import models
from django.conf import settings
from NewShop import local_settings
from NewShop.settings import MEDIA_ROOT
from django.core.mail import EmailMessage
import datetime
import requests
import pandas as pd
import abc
import time
import sys, os, hashlib, hmac, base64
# Create your models here.

class HUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='handle')
    phone = models.CharField(max_length=13,null=True)
    interest = models.CharField(max_length=50,null=True)
    # profile = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=None, null=True)
    permit = models.BooleanField(default=False) #역할 변경 : 핸드폰 인증 여부
    alarmMethod = models.IntegerField(default=0) #비트로 다룸 : ex) 2^0자리 이메일, 2^1자리 문자

    #멤버함수 추가 예정
    '''
    DB를 건드리는 기능 : 회원가입, 로그인, 즐겨찾기 저장/삭제, 검색(가격 표시), 마이페이지 이미지/이름/알람 수단 변경, 알람 설정
    '''
    def sendEmail(self, title, content):
        email = EmailMessage(
            subject=title,
            body=content,
            to=[self.user.email],
            )
        email.send()

    def sendSMS(self, content):
        if not self.permit:
            return
        url='https://sens.apigw.ntruss.com'
        uri='/sms/v2/services/'+local_settings.svc_id+'/messages'
        data = {
            "type": "SMS",
            "from": local_settings.hp,
            # 이 부분은 저의 전화번호가 넷상에 남게 되는 실수가 있을 수 있기 때문에 sendSMS()는 로컬 테스트 금지입니다.
            # 만약 다른 기능 테스트 중 이 함수에서 인터프리터 오류가 발생한다면, local_settings에서 끌어온 것들은 빈 문자열로 수정하여 테스트해주시기 바랍니다.
            "messages":[{"to": self.phone}],
            "content": content
        }
        access_key=local_settings.access_key
        secret_key=bytes(local_settings.secret_key,'UTF-8')
        stamp=str(int(time.time()*1000))
        msg = "POST "+uri+"\n"+stamp+"\n"+access_key
        msg=bytes(msg,'UTF-8')
        sv2=base64.b64encode(hmac.new(secret_key,msg,digestmod=hashlib.sha256).digest())
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-iam-access-key": access_key,
            "x-ncp-apigw-signature-v2":sv2,
            "x-ncp-apigw-timestamp": stamp
        }
        res=requests.post(url+uri, json=data, headers=headers)
        res.raise_for_status()

    def phoneAuth(self, input):        
        if self.phonekey.all()[0].value==int(input):
            self.phone=self.phonekey.all()[0].new_p
            self.permit=True
            self.save()
            self.phonekey.all()[0].delete()
            return True
        else:
            return False

    def __str__(self):
        return self.user.username


class History(models.Model):
    #pk는 전체를 기준으로, 생성 순으로 부여되니 정렬 id는 따로 부여하지 않겠음
    user = models.ForeignKey("HUser", related_name='history', on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)+' - '+str(self.product)
    

class Favor(models.Model):
    user = models.ForeignKey("HUser", related_name='favor', on_delete=models.CASCADE)
    product = models.ForeignKey("Product",on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)+' - '+str(self.product)
    

class Alarm(models.Model):
    user = models.ForeignKey("HUser", related_name='alarm', on_delete=models.CASCADE)
    product = models.ForeignKey("Product", related_name='alarm',on_delete=models.CASCADE)
    lower = models.IntegerField(default=0)
    reuse = models.BooleanField()
    news_alarm = models.BooleanField()
    upper = models.IntegerField()

    def __str__(self):
        return str(self.user)+' - '+str(self.product)

class Product(models.Model):    #상표 없는 것과 있는 것의 공통 규약을 위한 추상 클래스
    name = models.CharField(max_length=100)
    imgUrl = models.CharField(max_length=200, null=True)
    def __str__(self):
        return self.name
    
    @abc.abstractmethod
    def getNews(self):
        n = NspProduct.objects.all().filter(name=self.name)
        s = SpProduct.objects.all().filter(name=self.name)
        if n.count()>0:
            return n.get(name=self.name).getNews() 
        elif s.count()>0:
            return s.get(name=self.name).getNews()
        else:
            return []

    @abc.abstractmethod
    def getPrice(self):
        n = NspProduct.objects.all().filter(name=self.name)
        s = SpProduct.objects.all().filter(name=self.name)
        if n.count()>0:
            return n.get(name=self.name).getPrice() 
        elif s.count()>0:
            return s.get(name=self.name).getPrice()
        else:
            return []

    @abc.abstractmethod
    def getInfluence(self):
        n = NspProduct.objects.all().filter(name=self.name)
        s = SpProduct.objects.all().filter(name=self.name)
        if n.count()>0:
            return n.get(name=self.name).getInfluence()
        elif s.count()>0:
            return s.get(name=self.name).getInfluence()
        else:
            return []

    def getPriceByTable(self):
        if not os.path.isdir('./xlsx'):
            os.mkdir('./xlsx')
        filepath = "./xlsx/"+str(self.name)+'.xlsx'
        data = self.getPrice()
        data_list = []        
        for row in data:
            data_list.append([row.date, row.value])
        data_frame = pd.DataFrame(data=data_list, columns=['일자', '가격'])
        data_frame.to_excel(filepath)
        return filepath

    def sendPriceAlarm(self):  # 가격에 관한 알림만. 반드시 호출하기 전에 데이터베이스에 새로운 가격이 저장된 상태여야 함
        alarms=self.alarm.all()
        pr=self.getPrice()[0].value
        for a in alarms:
            if a.lower>pr and a.reuse:
                a.reuse=False
                a.save()
                if int(a.user.alarmMethod/2)==1:
                    msg = '[NewShop]\n'
                    msg += (a.user.user.username+'님, '+self.name+'의 가격이 '+str(pr)+'이 되었으니 사이트에서 확인해 주세요.')
                    a.user.sendSMS(msg)
                if a.user.alarmMethod%2==1:
                    title='[NewShop]가격 변동 알림 ('+self.name+')'
                    msg = (a.user.user.username+'님, '+self.name+'의 가격이 '+str(pr)+'이 되었으니 사이트에서 확인해 주세요.')
                    a.user.sendEmail(title, msg)
            elif a.upper<pr and not a.reuse:
                a.reuse=True
                a.save()
                if int(a.user.alarmMethod/2)==1:
                    msg = '[NewShop]\n'
                    msg += (a.user.user.username+'님, '+self.name+'의 가격이 '+str(pr)+'이 되었으니 사이트에서 확인해 주세요.')
                    a.user.sendSMS(msg)
                if a.user.alarmMethod%2==1:
                    title='[NewShop]가격 변동 알림 ('+self.name+')'
                    msg = (a.user.user.username+'님, '+self.name+'의 가격이 '+str(pr)+'이 되었으니 사이트에서 확인해 주세요.')
                    a.user.sendEmail(title, msg)

    def sendNewsAlarm(self):  # 뉴스에 관한 알림만. 반드시 호출하기 전에 데이터베이스에 새로운 뉴스가 저장된 상태여야 함. 1일 1회 기준
        alarms=self.alarm.all()
        if self.getNews().first().date == datetime.date.today():
            for a in alarms:
                if a.news_alarm:
                    if int(a.user.alarmMethod/2)==1:
                        msg = '[NewShop]\n'
                        msg += (a.user.user.username+'님 안녕하세요. '+self.name+'과 관련한 새로운 소식이 있으니, 사이트에서 확인해 주시기 바랍니다.')
                        a.user.sendSMS(msg)
                    if a.user.alarmMethod%2==1:
                        title='[NewShop]뉴스 알림 ('+self.name+')'
                        msg = (a.user.user.username+'님 안녕하세요. '+self.name+'과 관련한 새로운 소식이 있으니, 사이트에서 확인해 주시기 바랍니다.')
                        a.user.sendEmail(title, msg)

class NspProduct(Product): #상표 무관 product 키워드를 말함
    field = models.CharField(max_length=50,null=True)
    influence = models.CharField(max_length=100,null=True)
    def getNews(self):
        return self.news.all().order_by('-date')
    # 날짜별 가장 낮은 가격 쿼리셋 리턴. 함수는 Product(부모)에서만 부를 거기 때문에 반드시 양식이 동일해야 함
    def getPrice(self):
        spproduct = self.brand.all()        
        price_list = Price.objects.none()
        for sp in spproduct:
            price_list |= sp.getPrice()
        price_list.order_by('-date','value')

        date = ''
        same = ''
        
        for pr in price_list:
            date=pr.date
            if date != same:
                price_list=price_list.exclude(value__gt=pr.value,date=pr.date)
            else:
                price_list=price_list.exclude(pk=pr.pk)
            same=date            
        return price_list

    def getInfluence(self):
        try:
            return self.cloud
        except:
            return None
        

class SpProduct(Product):  #상표가 있는 specific product 키워드를 말함.
    product=models.ForeignKey("NspProduct",related_name='brand',on_delete=models.CASCADE)
    def getNews(self):
        return self.product.getNews()
    def getPrice(self):
        return self.price.all().order_by('-date')
    def getInfluence(self):
        return self.product.getInfluence()
    # return pandas dataframe

class News(models.Model):
    product = models.ForeignKey("NspProduct", related_name='news', on_delete=models.CASCADE)
    date = models.DateField()
    piece = models.CharField(default="", max_length=200)
    title = models.CharField(max_length=200)
    subj = models.IntegerField()
    url = models.URLField(max_length=200)

    def __str__(self):
        return self.title
    

class Price(models.Model):
    product = models.ForeignKey("SpProduct",related_name='price', on_delete=models.CASCADE)
    value = models.IntegerField()
    date = models.DateField()

    def __str__(self):
        return str(self.product)+' '+str(self.date)

class PhoneKey(models.Model):
    value = models.IntegerField()
    user = models.ForeignKey("HUser", related_name='phonekey',on_delete=models.CASCADE)
    new_p = models.CharField(max_length=13)

class Report(models.Model):
    subj = models.CharField(max_length=40)
    content = models.CharField(max_length=400)

    def __str__(self):
        return self.subj

class WordCloudImg(models.Model):
    img = models.ImageField(upload_to='img')
    product = models.OneToOneField("NspProduct", related_name='cloud', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.product.name