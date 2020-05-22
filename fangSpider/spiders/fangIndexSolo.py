# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from fangSpider.items import FangspiderLoupanItem
from fangSpider.items import NewhouseIndexItem
import time
import sys
import re
from bs4 import BeautifulSoup
from fangSpider.items import NewhouseDetailItem
from fangSpider.items import NewhouseKaipanDetail
from fangSpider.items import NewhouseKaipanPostDetail
from fangSpider.items import NewhouseDeliveryTimeDetailIndex

class FangindexSpider(CrawlSpider):
    name = 'fangIndexSolo'
    allowed_domains = ['fang.com']
    start_urls = ['https://www.fang.com/SoufunFamily.htm']
    #start_urls = ['https://zz.newhouse.fang.com/house/s/']

    rules = (
        #Rule(LinkExtractor(allow=r'http://.+\.fang\.com/$'), callback='parse_family', follow=True),
        Rule(LinkExtractor(allow=r'http://zz\.fang\.com/$'), callback='dircet_to_family', follow=True),
        #Rule(LinkExtractor(allow=r'https://yufujk\.fang\.com/$'), callback='parse_loupanindex', follow=True),
        #http://zz.fang.com/
        
    )

    def parse_item(self, response):
        item = {}
        #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        #item['name'] = response.xpath('//div[@id="name"]').get()
        #item['description'] = response.xpath('//div[@id="description"]').get()
        return item

    def dircet_to_family(self,response):
        newhouse_family = response.xpath('//a[contains(text(),"新房")]/@href').re('.*new.*')[0] 
        esf_family = response.xpath('//a[contains(text(),"二手房")]/@href').re('.*esf.*')[0] 
        zu_family = response.xpath('//a[contains(text(),"找租房")]/@href').re('.*zu.*')[0]

        if newhouse_family is None:
            pass
        else:
            yield scrapy.Request(newhouse_family,callback=self.parse_family)

        if esf_family is None:
            pass
        else:
            pass

        if zu_family is None:
            pass
        else:
            pass
        pass

    def parse_family(self,response):
        print(response.url)
        
        loupans = response.xpath('//div[@id="newhouse_loupai_list"]/ul//li')
        #city = response.xpath('//div[@class="s4Box"]/a/text()').get()
        print('-'*100)
        print(loupans)
        loupans = loupans.xpath('.//div[@class="nlcd_name"]/a/@href').getall()
            
        for i in loupans:
            if 'newhouse.fang.com' in i:
                continue
            else:
                u = response.urljoin(i)

                print('发起请求的url'+'@'*80+u)
                yield scrapy.Request(u,callback=self.parse_loupanindex,meta={'midtag':False})
            

    def parse_loupanindex(self,response):
        #print('解析详情页的parse启动+'+response.url)
        url = self.format_url(response.url)
        
        print('@'*80+response.url+'----'+response.request.url)

        script = response.xpath('//script') 
        part_dis = script.re('district.*')
        if len(part_dis)>0:
            part = part_dis[0].split('"')[1] 
        else:
            part_dis = script.re('address.*')
            if len(part_dis)>0:
                part = part_dis[0].split('"')[1] 
            else:
                pass
        compart = response.xpath('//script[@type="text/javascript"]').re('ub_com.*')[0].split('"')[1]
        name = response.xpath('//div[@class="tit"]/h1//text()').get()
        other_name = response.xpath('//div[class="title"]/span/@title').get()
        tag_ = response.xpath('//div[@class="biaoqian1"]//text()').getall()
        tag = ' '.join(tag_).strip('')
        tag = self.format_text(tag)
        unit_price_ = response.xpath('//div[@class="inf_left fl mr30"]//text()').getall()
        unit_price_ = "".join(unit_price_).strip()
        unit_price__ = response.xpath('//div[@class="inf_left fl "]//text()').getall()
        if len(unit_price__):
            unit_price__ = ''.join(unit_price__).strip()
            unit_price = unit_price_+unit_price__
        else:
            unit_price = unit_price_
        unit_price = self.format_text(unit_price)
        huxin_main_ = response.xpath('//div[@class="fl zlhx"]//text()').getall()
        huxin_main = "".join(huxin_main_).strip()
        huxin_main = self.format_text(huxin_main)
        # louaddress_ = response.xpath('//div[@id="xfptxq_B04_12"]//text()').getall()
        # louaddress = "".join(louaddress_).strip()
        # louaddress = self.format_text(louaddress)
        # 处理部分项目没有值的问题
        louaddress_ = response.xpath('//div[contains(string(),"项目地址")]').re('项目地址.*')[0].split('"')  
        louaddress_len = len(louaddress_)
        louaddress = louaddress_[louaddress_len-2] 
        #sale_time = response.xpath('//a[@class="kaipan"]/text()').get()
        sale_time =''
        deliver_table = response.xpath('//table[@class="tf"]/tbody//tr')
        delivery_time = ''
        for tr in deliver_table:
            delivery_time+="".join(tr.xpath('.//text()').getall()).strip()
        delivery_time = self.format_text(delivery_time)
        city = response.xpath('//div[@class="s4Box"]/a/text()').get()

        item = NewhouseIndexItem(url=url,name=name,unit_price=unit_price,tag=tag,louaddress=louaddress,
        sale_time=sale_time,delivery_time=delivery_time,
        huxin_main = huxin_main,other_name=other_name,part=part,compart=compart,city=city)
        print(item)
        yield item
        detail_url = response.xpath('//a[contains(text(),"楼盘详情")]/@href').get() 
        print('0'*100+detail_url)
        detail_url = response.urljoin(detail_url)
        
        yield scrapy.Request(detail_url,callback=self.parse_loupanDetail)

        #处理开盘时间
        sale_time_url = response.xpath('//a[@class="kaipan"]/@href').get() 
        sale_time_url = response.urljoin(sale_time_url)
        yield scrapy.Request(sale_time_url,callback=self.parse_sale_time)

        #处理post信息
        #post_history_url = response.xpath('//a[@id="xfptxq_B03_12"]/@href').get() 
        #post太多了 考虑单独抓取 
        post_history_url = response.xpath('//a[contains(text(),"楼盘动态")]//@href').get() 
        post_history_url = response.urljoin(post_history_url)
        yield scrapy.Request(post_history_url,callback=self.parse_history_post_index)

        delivery_time_url = response.xpath('//a[contains(text(),"更多交房详情>>")]/@href').get()
        delivery_time_url = response.urljoin(delivery_time_url)
        yield scrapy.Request(delivery_time_url,callback=self.parse_delivery_time_index)


    def parse_delivery_time_index(self,response):
        url = self.format_url(response.url)
        delivery_list = []
        trs = response.xpath('//div[@class="kpjjlu"]//tr') 
        if len(trs)>1:
            for index, tr in enumerate(trs):
                if index==0:
                    continue
                else:
                    try:
                        tds = tr.xpath('.//td/text()').getall()
                        date = tds[0]
                        note = tds[1]
                    except Exception as e:
                        date = ''
                        if tds is None:
                                pass
                        else:  
                            note = '出现错误 下面为原文'+str(tds)
                delivery_list.append({'date':date,'note':note})  
            item = NewhouseDeliveryTimeDetailIndex(url = url, delivery_time = delivery_list)  
            print(item)
            print('-'*100)
            yield item

        
                        


    def parse_history_post_index(self,response):
        url = self.format_url(response.url)
        short_post = True
        if short_post:
            short_post_list = []
            lis = response.xpath('//div[@id="gushi_all"]//li')
            for li in lis:
                tex = li.xpath('.//text()').getall()
                text = "".join(tex)
                text = self.format_text(text)
                short_post_list.append(self.format_red(text))
            
            post = {'url':response.url,'short_data':short_post_list}
            item = NewhouseKaipanPostDetail(url = url, post_list = post)
            print(item)
            yield item
            return  
        else:
            if 'item' in response.meta.keys():
                item = response.meta['item']
            else:
                item = NewhouseKaipanPostDetail(url = url, post_list= [])
            
            lis = response.xpath('//div[@id="gushi_all"]//li//a/@href').getall() 
            for li in lis:
                if ',' in li:
                    url_ = response.urljoin(li)
                    yield scrapy.Request(url_,meta={'item':item},callback=self.parse_history_post_index)
                    #处理发起下一页
                else:
                    url_ = response.urljoin(li)
                    yield scrapy.Request(url_,meta={'item':item},callback=self.parse_history_post_detail)


    def parse_history_post_detail(self,response):
        url = self.format_url(response.url)
        if 'item' in response.meta.keys():
            item = response.meta['item']
        else:
            print('&'*80+'程序出错 这里应该能获得item对象' + response.url)
            return

        title = response.xpath('//h1[@class="atc-tit"]/text()').get()
        source_ = response.xpath('//h2[@class="atc-source"]//text()').getall()
        source = self.format_text("".join(source_).strip().replace('\r','').replace(' ',''))
        content_ = response.xpath('//div[@class="leftboxcom"]//text()').getall() 
        content = self.format_text("".join(content_).strip())
        item['post_list'].append({'title':title,'source':source,'content':content})

        syp = response.xpath('//a[@class="syp"]/@href').get() 
        if 'javascript' in syp:
            print(item)
            return item
        

    def request_family(self,request):
        print(request)
        pass

    def parse_sale_time(self,response):
        trs = response.xpath('//div[@class="kpjjlu"]').xpath('.//tr') 
        url = self.format_url(response.url)
        
        td_l = []
        for index,tr in enumerate(trs):
            if index==0:
                continue
            td = tr.xpath('td//text()').getall()
            if len(td)>1:
                td_l.append({'data':td[0],'note':td[1]})
            elif len(td)==1:
                td_l.append({'data':td[0]})
            else:
                print('^'*20+'数据量可能不够'+response.url)
                return 
            #for td in tr.xpath('td//text()').getall():
            
        #dic['kaipan'] = td_l
        item = NewhouseKaipanDetail(kaipan=td_l,url=url)
        print(item)
        yield item


        
        
                


        pass
    def parse_loupanDetail(self,response):
        print('正在解析Detail页面-------'+response.url)
        url = self.format_url(response.url)
        contents = response.xpath('//div[@class="main-info-price"]/../..').xpath('.//li')[1].get()  
        contents = self.format_text(contents)
        bs = BeautifulSoup(contents,'lxml')
        lis = bs.find_all('li')
        poi_tag = 0
        poi = ''
        buiding_type,alright,location,property_,status,marker_address,phone_plat,floor_area,gross_area,gross_area_ratio,parking,counter_buidings,counter_households,wuye_corp,wuye_cost,wuye_note,status_buidings,sale_time = None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None
        for i in lis:
            t = i.get_text().replace(' ','').replace('\n','')
            if '建筑类别' in t:
                buiding_type = t.replace('建筑类别：','')
            elif '装修状况' in t:
                pass
                #没有考虑
            elif '产权年限' in t:
                alright = t.replace('产权年限：','')
            elif '环线位置' in t:
                location = t.replace('环线位置：','')
            elif '开发商' in t:
                property_ = t.replace('开发商：','')
            elif '销售状态' in t:
                status = t.replace('销售状态：','')
            elif '开盘时间' in t:
                sale_time = t.replace('开盘时间：','')
            elif '售楼地址' in t:
                marker_address = t.replace('售楼地址：','')
            elif '主力户型' in t:
                huxin_main = t.replace('主力户型：','')
                huxin_main = huxin_main
            elif '预售许可证' in t:
                pass
                #这里只捕获内容 但不会在这个item中处理
            elif '咨询电话' in t:
                phone_plat = t.replace('咨询电话：','')
                poi_tag = 1
            elif '占地面积' in t:
                poi_tag = 0
                floor_area = t.replace('占地面积：','')
            elif poi_tag:
                poi+=(t+' ')
            elif '建筑面积' in t:
                gross_area = t.replace('建筑面积：','')
            elif '容积率' in t:
                gross_area_ratio = t.replace('容积率：','')
            elif '绿化率' in t:
                greening_ratio = t.replace('绿化率：','')
            elif '停车位' in t:
                parking = t.replace('停车位：','')
            elif '楼栋总数' in t:
                counter_buidings = t.replace('楼栋总数：','')
            elif '总户数' in t:
                counter_households = t.replace('总户数：','')
            elif '物业公司' in t:
                wuye_corp = t.replace('物业公司：','')
            elif '物业费：' in t:
                wuye_cost = t.replace('物业费：','')
            elif '物业费描述' in t:
                wuye_note = t.replace('物业费描述：','')
            elif '楼层状况' in t:
                status_buidings = t.replace('楼层状况：','')
            else:
                pass
        profile_ = response.xpath('//div[@class="main-item"]/p[@class="intro"]').get()
        profile = self.format_text(profile_).replace('<p class="intro">','').replace('<br>','').replace('</p>','')

        tbs = response.xpath('//div[@class="main-table"]//table') 
        #处理没有预售证或者其他情况
        presale_list = []
        price_history_list =[]
        t_presale,t_price_history = None,None
        for tb in tbs:
            if len(tb.re('绑定楼栋'))>0:
                if t_presale is None:
                    t_presale = tb.get()
                else :
                    if len(tb.get())>len(t_presale):
                        t_presale = tb.get() 

            if len(tb.re('价格描述'))>0:
                if t_price_history is None:
                    t_price_history = tb.get()
                else :
                    if len(tb.get())>len(t_price_history):
                        t_price_history = tb.get() 
            

        if not t_presale is None:
            bs_presale = BeautifulSoup(t_presale,'lxml')
            trs = bs_presale.find_all('tr')
            for index,tr in enumerate(trs):
                if index==0:
                    continue
                tds = tr.find_all('td')
                td_dict = {}
                for index,td in enumerate(tds): 
                    t = td.get_text()
                    if index==0:
                        td_dict['name'] = t
                    elif index==1:
                        td_dict['date'] = t
                    elif index==2:
                        td_dict['bind'] = t
                        presale_list.append(td_dict)

        if not t_price_history is None:
            bs_history = BeautifulSoup(t_price_history,'lxml')
            trs = bs_history.find_all('tr')
            for index,tr in enumerate(trs):
                if index==0:
                    continue
                tds = tr.find_all('td')
                dic = {}
                for index,td in enumerate(tds):
                    t = td.get_text()
                    if index==0:
                        dic['date'] =t
                    elif index ==1:
                        dic['price'] = t
                    elif index ==2:
                        dic['startprice'] = t
                    elif index ==3:
                        dic['description']   = t
                        price_history_list.append(dic)
                 

                


            
        item = NewhouseDetailItem(profile=profile,presale=presale_list,price_history=price_history_list,url=url,buiding_type=buiding_type,alright=alright,
        location=location,property_ =property_,status=status,marker_address=marker_address,
        phone_plat=phone_plat,floor_area=floor_area,gross_area=gross_area,gross_area_ratio=gross_area_ratio,
        greening_ratio=greening_ratio,parking=parking,counter_buidings=counter_buidings,
        counter_households=counter_households,wuye_corp=wuye_corp,wuye_cost=wuye_cost,
        wuye_note=wuye_note,status_buidings=status_buidings,sale_time=sale_time,poi=poi)
        print(item)
        #print(poi)
        return item



                



    def format_url(self,url):
        u = url.split('/')[2]
        newurl = 'http://'+u
        return newurl
    
    def format_text(self,text):
        return text.replace('\t','').replace('\n','').replace('\xa0','')

    def format_red(self,text):
        return text.replace('<','').replace('>','').replace('"','').replace(' ','').replace('/','')