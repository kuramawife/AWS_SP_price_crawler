import time
import requests
import awsrefs as aws
import settings
import pandas as pd
import collections
from concurrent.futures import ThreadPoolExecutor

#印出所有 setting 資料
PLAN_TYPE = settings.PLAN_TYPE
INSTANCE_FAMILY = settings.INSTANCE_FAMILY
PLAN_LENGTH = settings.PLAN_LENGTH
PLAN_COMMIT = settings.PLAN_COMMIT
REGIONS = ["Asia Pacific (Tokyo)", "Asia Pacific (Seoul)"
           ]
OSES = settings.OSES
TENANCY = settings.TENANCY

# Compute Savings Plans 的 URL
BASE_URL = "https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/computesavingsplan/USD/current/"
MID_URLS = {'compute': "compute-savings-plan-ec2", 'ec2': "instance-savings-plan-ec2"}
END_URL = "index.json?timestamp="

def file_settings_overrides():
    global RI_INPUT_TEMPLATE
    RI_INPUT_TEMPLATE = settings.RI_INPUT_TEMPLATE

def get_terms():
    global SP_TERMS
    terms = []
    #組合-合約長度 x 合約支付方式
    for length in PLAN_LENGTH:
        for commit in PLAN_COMMIT:
            terms.append("{}{}".format(int(length), commit))
    SP_TERMS = terms

def construct_urls():
    URLS = []
    TIMESTAMP = str(int(time.time()))
    START_URL = "{}{}".format(BASE_URL, MID_URLS[PLAN_TYPE.lower()])
    ###print("START_URL:" + START_URL)
    for region in REGIONS:
        #如果是使用區域編碼會進行比對轉換成區域名稱
        for k, v in aws.regions.items():
            if region == k:
                region = v

        for os in OSES:
            for terms in SP_TERMS:
                terms = list(terms)
                for k, v in aws.commit.items():
                    #將commit(A/P/N 轉換成全名 All Upfront/Partial Upfront/No Upfront)
                    if terms[1] == k:
                        term = "{} year/{}".format(str(terms[0]), v)
                # TENANCY 分成 Shared 共享、專用主機等
                for tenancy in TENANCY:
                    # EC2 的 Plan 類型可以分成 Compute Savings Plans、EC2 Instance Savings Plans
                    #將 因素 合成網址 URL
                    if PLAN_TYPE.lower() == 'compute':
                        URLS.append(
                            "{}/{}/{}/{}/{}/{}{}".format(START_URL, term, region, os, tenancy, END_URL, TIMESTAMP))
                    if PLAN_TYPE.lower() == 'ec2':
                        for instance in INSTANCE_FAMILY:
                            URLS.append(
                                "{}/{}/{}/{}/{}/{}/{}{}".format(START_URL, term, instance, region, os, tenancy, END_URL,
                                                                TIMESTAMP))

    print("Working on {} URLS".format(len(URLS)))
    return URLS

def get_json(in_url):
    ''' 連線網頁 '''
    response = requests.get(in_url)
    if response.status_code != 200:
        print("ERROR : 無法連線 to\n{}".format(in_url))
    working_data = response.json()
    for i in working_data['regions'].values():
        for k, v in i.items():
            # k 為 x year No Upfront <<機器規格>> <<作業系統>> <<Tenancy>> 這層的內容
            # v 為 k 這層的內容
            entry = {}
            rate = v
            tenancy = rate['ec2:Tenancy']
            instance = rate['ec2:InstanceType']
            sp_region = rate['ec2:Location']
            # 找出區域對應的區域編碼並儲存到 sp_region_code
            for k, v in aws.regions.items():
                if sp_region == v:
                    sp_region, sp_region_code = v, k

            operatingsystem = rate['plc:OS']
            #網頁的OS為縮寫，故我們比對 awsrefs 內容對應出 OS 全名
            for k, v in aws.os.items():
                if operatingsystem == v:
                    operatingsystem = k

            commityear = rate['LeaseContractLength']
            commitamount = rate['PurchaseOption']
            # 網頁的 commitamount 為全名(No Upfront)，故我們比對 awsrefs 內容對應出縮寫
            for k, v in aws.commit.items():
                if commitamount == v:
                    commitamount = k
            # excel 我們僅要顯示縮寫(例如：3N >> 3 年 No Upfront )
            commitcode = commityear + commitamount
            #抓取SP的價錢以及Ondemand價錢
            sprate = rate['price']
            odrate = rate['ec2:PricePerUnit']
            spcode = "{}-{}-{}-{}-{}".format(instance, sp_region, operatingsystem, tenancy, commitcode)
            #json沒有此欄位，用SP以及Ondemand價錢相除
            savingper = ((float(odrate) - float(sprate)) / float(odrate))

            entry_key = instance + spcode
            #把需要寫入excel的資料 儲存成dict
            entry = {"instance": instance,
                     "region": sp_region,
                     "regioncode": sp_region_code,
                     "os": operatingsystem,
                     "tenancy": tenancy,
                     "commitcode": commitcode,
                     "odrate": "{:0.4f}".format(float(odrate)),
                     "sprate": sprate,
                     "savingper": "{:0.2f}".format(savingper)
                     }
#            print(type(entry)) >> dict 格式
            response_dict[entry_key] = entry

def main():
    ''' Main entry point of the app '''
    file_settings_overrides()
    get_terms()
    print("\nRegions - {}".format(', '.join(map(str, REGIONS))))
    print("OS - {}".format(', '.join(map(str, OSES))))
    print("Tenancy - {}".format(', '.join(map(str, TENANCY))))
    print("Commitment Types - {}".format(', '.join(map(str, SP_TERMS))))
    working_urls = construct_urls()

    with ThreadPoolExecutor() as executor:
        executor.map(get_json, working_urls, timeout=30)

    pd.DataFrame.from_dict(response_dict, orient="index").to_csv("data.csv")

if __name__ == "__main__":
    ''' This is executed when run from the command line '''
    start = time.time()
    response_dict = collections.OrderedDict()
    main()
    stop = time.time()
    print("\nRuntime {:0.2f}s\n".format(stop - start))



