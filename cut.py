#!/bin/usr/python
import os
import sys
import pdfplumber
import PyPDF2
from tqdm import tqdm

pdf_filepath = r'./test.pdf'
output_path = r'./output/'


# 提示用户输入路径
pdf_filepath = input("请拖拽文件并使用回车确认: ")
 
# 输出用户输入的路径
print("您输入的路径是: ", pdf_filepath)

dict_account = {'收款人户名：':'收款行行名',
                '付款人户名：':'付款行行名',
                '付款人户名:':'付款行行名',
                '收款人名称：':'收款人账号',
                '征收机关名称:':'收款',
                '付款户名：':'收款账户'
                }
dict_amount = {'RMB':''}           #大小写只能存在一种
dict_date1 = {'交易日期':'回单编号'}
dict_date2 = {'记账日期':''}

def datahandle(data,strcut):
    start_len = 0
    start = -1
    for key in strcut:
        if data.find(key) >= 0:
            start=data.find(key)
            stop=data.find(strcut[key])
            start_len = len(key)

    
    if (start >= 0) and 'RMB' in strcut:
        data=data[start+start_len:].strip().replace('\n', '')
    elif (start >= 0) and '记账日期' in strcut:
        data=data[start+start_len:start+start_len+11].strip().replace('\n', '').replace(':', '')
        data=data.replace('-', '年', 1)
        data=data.replace('-', '月', 1)
        data+='日'
    elif (start >= 0):
        data=data[start+start_len:stop].strip().replace('\n', '')
    else :
        data=''     #无法处理的赋值空字符串
    return data

TYPE_A = 1  #宁波银行客户回单
TYPE_B = 2  #宁波银行网上交易凭证
TYPE_C = 3  #中国工商银行

filename = []
file_type = 0
with pdfplumber.open(pdf_filepath) as pdf:
    if pdf.pages[0].extract_text().find('宁波银行客户回单') >= 0 :
        file_type = TYPE_A
    elif pdf.pages[0].extract_text().find('宁波银行网上交易凭证') >= 0:
        file_type = TYPE_B
    elif pdf.pages[0].extract_text().find('中国工商银行') >= 0:
        file_type = TYPE_C
    else :
        print("unknow file type! Contact Sandra~")
        sys.exit(0)
    for table_page1 in tqdm(pdf.pages ,bar_format='The page is being cropped :{l_bar}{bar}{r_bar}') :
        #table_page1 = pdf.pages[2]
        text = table_page1.extract_text()
        sheet_start = 0
        for table in table_page1.extract_tables():
            text = text[sheet_start:]           #获取交易日期
            if file_type == TYPE_A :
                amount = datahandle(table[3][1],dict_amount)
                account = datahandle(table[6][1],dict_account)
                date = datahandle(text,dict_date1)
            elif file_type == TYPE_B :
                amount = table[3][2]
                account = table[0][5]
                date = datahandle(text,dict_date2)
            elif file_type == TYPE_C :
                amount = table[3][2]
                account = table[0][7]
                date = table[9][8]
                if account == None:
                    account = table[0][8]
                if date == None:
                    date = table[9][9]

                account = account.replace('\n', '')

            sheet_start = text.find('记账日期')
            sheet_start += 30

            if account == None or amount == None or date == None:
                print("There is a file that cannot read information, please be aware！！！")

            if account == None:
                account = "unknow"
            if amount == None:
                amount = "unknow"
            if date == None:
                date = "unknow"
                
            filename.append(date + '-' + amount + '-' + account)
            #print(date + '-' + amount + '-' + account)
        
print('file type is ' + str(file_type))

pdf_file = open(pdf_filepath,'rb')
pdf_reader = PyPDF2.PdfReader(pdf_file)

total_page = len(pdf_reader.pages)

if os.path.exists(output_path) == False:
    os.mkdir(output_path)
#左下角为零点建立坐标轴，X为高度，Y为宽度，标准A4尺寸为842-595
if file_type == TYPE_A :
    y_point = (842,583,323,60)
    cut_num = 3
elif file_type == TYPE_B :
    y_point = (842,562,282,30)
    cut_num = 3
elif file_type == TYPE_C :
    y_point = (842,432,40)
    cut_num = 2
index = 0
for page in tqdm(range(0,total_page),bar_format='Page storage :{l_bar}{bar}{r_bar}'):
    page_adj = pdf_reader.pages[page]
    for i in range(0,cut_num) :
        page_adj.mediabox.upper_left = (0, y_point[i])         
        page_adj.mediabox.upper_right = (595, y_point[i])   
        page_adj.mediabox.lower_left = (0, y_point[i+1])        
        page_adj.mediabox.lower_right = (595, y_point[i+1])
        index = page * cut_num + i
        if index < len(filename) :
            out_pdf = PyPDF2.PdfWriter()  
            out_pdf.add_page(page_adj)
            out_pdf.write(open(output_path + str(index + 1) + '-' + filename[index] +'.pdf', 'wb')) 
            out_pdf.close()

print( 'PDF is divided into ' +  str(index + 1) + ' files.')

pdf_file.close()
