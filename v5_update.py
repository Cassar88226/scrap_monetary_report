import tkinter as tk
from tkinter.filedialog import askopenfilename,asksaveasfilename
import requests
from bs4 import BeautifulSoup
from datetime import datetime

import tika
from tika import parser

# import tabula 
import csv
import camelot
import socket
import threading
import os
import re
from io import BytesIO, StringIO
num_rows=1
text_rules=''
master=''
qwe = []
qwe_pdf = []
current_view = 'setup'
current_view_pdf = 'setup'
greens = ['white','white','white','white','white','red2','firebrick1','IndianRed1','SeaGreen2','SpringGreen2','green2','white','white','white','white','white']
headings = ['Name','Act1','Dev','Actual','Forecast','-LT3','-LT2','-LT1','+UT1','UT2','UT3','R','G1','G2','Max','Action']
headings2 = ['Repo Rate','Act1','Dev','Actual','Forecast','-LT3','-LT2','-LT1','+UT1','UT2','UT3','Max-']
years = []
years_in_pdf = []
logs = ''
rules_headers =[]
rules_headers_pdf = []
mode = ''
signal_t = ''
signal_p = ''
repo_rate_data = {}
repo_rate_number = ''
text_logs = ''
pdf_logs = ''
report_log = ''
scrollbar = ''
del_row = ''
flag = False
thread=''
start_marker=''
end_marker=''
def startt():
    global thread
    thread = threading.Thread(target=starttt,name='start')
    thread.start()
    # thread.join()
def send_signal(msg):
    global port,report_log
    try:
        udp_port = int(port.get())
    except:
        # report_log+='Port not defined'+'\n'
        print('Port not defined')
        return
    print(udp_port,msg)
    report_log+= str(datetime.now()) + ' - ' +  msg + ' signal sent\n'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg.encode('utf-8'), ("127.0.0.1", udp_port))

def starttt():
    global repo_rate_data,mode,live_url,prog,test_html,years_in_pdf,repo_rate_data,enable_check_pdf,enable_check_text,repo_rate_number,report_log,text_logs,pdf_logs,flag,interval,timeout,start_marker,end_marker
    repo_rate_number=''

    run_pdf = enable_check_pdf.get()
    run_text = enable_check_text.get()
    print('run_pdf',run_pdf,'run_text',run_text)
    run_type = mode.get()
    print(run_type)
    # report_log = 'Running in ' + run_type + '\n'
    # send_signal('hello')
    report_log=''
    if(run_type=='Live Mode'):
        flag=True
        url  = live_url.get()
        # report_log+= 'url : ' + url + '\n'
        if(url==''):
            prog.set("Live url cannot be empty in Live Mode.")
            # report_log += 'URL not found' + '\n'
            flag=False
        else:
            while(flag):
                flag=False
                try:
                    time_out = timeout.get()
                    try:
                        time_out = float(time_out)
                    except:
                        time_out=None
                    prog.set('Attempting request to the main page.')
                    report_log += str(datetime.now()) + ' - Attempting request to the main page.\n'
                    html = requests.get(url,timeout=time_out, allow_redirects=False)

                except Exception as e:
                    print(e)
                    # report_log+= str(datetime.now()) + ' - ' + e+'\n'
                    prog.set(e)
                    continue
                if(html.status_code==404):
                    print('Page not found')
                    report_log+=str(datetime.now()) + ' - Page not found.\n'
                    prog.set('Page not found.')
                    continue
                # prog.set("Extracting text from the page")
                soup = BeautifulSoup(html.content, features="lxml")
                try:
                    text = soup.find('p', {'class':'preamble'}).text
                except:
                    prog.set("Unable to extract text.Please check your url")
                    continue
                lines  = ' '.join(text.split()).replace('–','-').split('. ')
                report_log += str(datetime.now()) + ' - main page extracted.\n'

                prog.set('Attempting to get the pdf.')
                pdf_link = soup.findAll('li',{'class':'link-list-block__item'})
                for i in pdf_link:
                    # print(i.a['href'])
                    if('press-release' in i.a['href']):
                        pdf_link = i.a['href']
                        break
                report_log += str(datetime.now()) + ' - Pdf link found.\n'
                
                repo_rate_data= {}
                report_log += str(datetime.now()) + ' - Starting processing on Text rules.\n'

                if(run_text):
                    text_rules_calculations(lines)
                report_log += str(datetime.now()) + ' - Text rules processing Done.\n'
                
                pdf_url = 'https://www.riksbank.se/'+ str(pdf_link)
                # print(pdf_url)
                report_log += str(datetime.now()) + ' - Attempting to get Pdf.\n'

                html = requests.get(pdf_url, allow_redirects=False)
                report_log += str(datetime.now()) + ' - ' + 'Pdf downloaded.' + '\n'

                with open('press_release.pdf', 'wb') as f:
                    f.write(html.content)
                prog.set('Extracting data from pdf')
                report_log+=str(datetime.now()) + ' - ' + 'Extracting data from pdf'+'\n'
                start_mar = 'average'
                end_mar = 'Note'
                if(start_marker):
                    start_mar = start_marker
                if(end_marker):
                    end_mar = end_marker
                table = []
                years_in_pdf = []
                parsed = parser.from_file("press_release.pdf")
                text = parsed['content']

                extracted = re.search('{}[0-9A-Za-z(),-\\.\\*\\n\\s]*{}'.format(start_mar, end_mar), text)
                start = len(start_mar)
                end = extracted[0].find(end_mar)
                text = extracted[0][start:end]

                # lines = text.replace(' ','').replace('(\n','(').replace('\n)',')').replace('−','-').replace(',','.').replace('âˆ’','-').replace('Œ','-').split('\n')
                lines = text.split('\n')
                lines = list(filter(('').__ne__, lines))
                yrs = ['2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030']
                for year in lines:
                    n = len(years_in_pdf)
                    for yr in yrs:
                        if yr in year:
                            years_in_pdf.append(yr)
                result = []
                for line in lines:
                    if 'Repo rate, per cent' in line:
                        full_re = '(–*−*-*[0-9]+\\.[0-9]+\\s*\\(\\s*–*−*-*[0-9]+\\.[0-9]+\\))|(–*−*-*[0-9]+\\.[0-9]+)'
                        extracted_num_list = [list(n) for n in re.findall(full_re, line)]
                        for num_list in extracted_num_list:
                            result.append(num_list[0].replace(' ','').replace('−','-')+num_list[1])
                        result.insert(0, "Repo rate, per cent")
                lines = result
                table=[lines]
                # .replace('−','-').replace('–','-').replace(',','.').replace('âˆ’','-')
                report_log += str(datetime.now()) + ' - ' + 'Data from pdf extracted.' + '\n'
                
                if(table!=[]):
                    table = [table[-1]]
                report_log += str(datetime.now()) + ' - Processing of pdf data started.\n'
                
                for i in table:
                    calc(i)
                print("repo_rate_data")
                print(repo_rate_data)
                if(run_pdf):
                    pdf_rules_calculations()
                report_log += str(datetime.now()) + ' - Processing of pdf data done.\n'
                report_log += str(datetime.now()) + ' - Completed.\n'
                prog.set('Completed')
                cvb = open('report'+str(datetime.now()).replace(' ','').replace(':','-')+'.log','w')
                cvb.write(report_log)
                cvb.close()

                # prog.set(lines)
        
    else:
        file_name = test_html.get()  
        if(file_name==''):
            prog.set('Test Html cannot be empty in Test Mode')
        else:
            html=''
            with open(file_name,'r', encoding='utf-8', errors='ignore') as f:
                html = f.read()
            soup = BeautifulSoup(html, features="lxml")
            text = ''
            try:
                text = soup.find('p', {'class':'preamble'}).text
            except:
                prog.set("Unable to extract text.Please check your html file")
            lines  = ' '.join(text.split()).replace('–','-').split('. ')
            try:
                repo_rate_number = soup.find('div', {'class':'data-block__value'}).find('span').text
                repo_rate_number = repo_rate_number.replace('−','-').replace(',','.').replace('âˆ’','-')

                repo_rate_number = float(repo_rate_number)
            except:
                repo_rate_number=''
            pdf_link = soup.findAll('li',{'class':'link-list-block__item'})
            for i in pdf_link[0:1]:
                # print(i.a['href'])
                print(i.a['href'])
                if('press-release' in i.a['href'] or True):
                    # print(i.a['href'])
                    if repo_rate_number=='':
                        repo_rate_number = i.span.text
                        repo_rate_number = repo_rate_number.replace('−','-')
                        repo_rate_number = repo_rate_number.replace('–','-')
                        repo_rate_number = repo_rate_number.replace(',','.')
                        repo_rate_number = repo_rate_number.replace('âˆ’','-')
                        repo_rate_number = repo_rate_number.split()
                        link = repo_rate_number
                        # print(repo_rate_number)
                        for wrd in reversed(repo_rate_number):
                            # print(wrd)
                            try:
                                repo_rate_number = float(wrd)
                                if(repo_rate_number<1000):
                                    break
                            except:
                                pass
                            if('zero' in link):
                                repo_rate_number=0
                                break
                        break
            file_name = test_pdf.get()
            print(file_name)
            if(not file_name):
                prog.set('Test pdf cannot be empty in Test Mode')
            else:
                prog.set('Extracting data from pdf')
                start_mar = 'average'
                end_mar = 'Note'
                if(start_marker):
                    start_mar = start_marker
                if(end_marker):
                    end_mar = end_marker
                table = []
                years_in_pdf = []
                parsed = parser.from_file(file_name)
                text = parsed['content']
                # print(text)


                extracted = re.search('{}[0-9A-Za-z(),-\\.\\*\\n\\s]*{}'.format(start_mar, end_mar), text)
                start = len(start_mar)
                end = extracted[0].find(end_mar)
                text = extracted[0][start:end]

                # lines = text.replace(' ','').replace('(\n','(').replace('\n)',')').replace('−','-').replace(',','.').replace('âˆ’','-').replace('Œ','-').split('\n')
                lines = text.split('\n')
                lines = list(filter(('').__ne__, lines))
                yrs = ['2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030']
                for year in lines:
                    n = len(years_in_pdf)
                    for yr in yrs:
                        if yr in year:
                            years_in_pdf.append(yr)

                result = []
                for line in lines:
                    if 'Repo rate, per cent' in line:
                        full_re = '(–*−*-*[0-9]+\\.[0-9]+\\s*\\(\\s*–*−*-*[0-9]+\\.[0-9]+\\))|(–*−*-*[0-9]+\\.[0-9]+)'
                        extracted_num_list = [list(n) for n in re.findall(full_re, line)]
                        for num_list in extracted_num_list:
                            result.append(num_list[0].replace(' ','').replace('−','-')+num_list[1])
                        result.insert(0, "Repo rate, per cent")
                lines = result
                table=[lines]
                if(table!=[]):
                    table = [table[-1]]
                if(run_text):
                    text_rules_calculations(lines)
                for i in table:
                    calc(i)
                if(run_pdf):
                    pdf_rules_calculations()
                
def stop():
    global flag,thread,report_log
    flag=False
    # f = open('report'+str(datetime.now()).replace(' ','')+'.log','w')
    # f.write(report_log)
    # f.close() 
    report_log=''
    # thread.join()

def text_rules_calculations(lines):
    global repo_rate_number,report_log,text_logs
    dummy = []
    for i in lines:
        dummy.append(i.lower())
        text_logs+= i.lower() + '\n' 
    lines = dummy[:]
    dummy = []
    for r in qwe:
        rule = r[0][1].get()
        if(rule=='Repo Rate - number'):
            r[3][1].set(repo_rate_number)
            try:
                fore = float(r[4][1].get())
            except:
                fore=''
            if(repo_rate_number!=''):
                if(fore!=''):
                    r[2][1].set("{:.2f}".format(repo_rate_number-fore))
                else:
                    r[2][1].set(str(repo_rate_number))
            else:
                print('repo_rate_number not found')
                text_logs+='repo_rate_number not found'+'\n'
        if(rule!='Repo Rate - number' and rule!='Average'):
            stats = lines[:]
            rule = rule.lower()
            maxx = rule.split('max')[1]
            rule = rule[:-1*(len(maxx)+4)]
            if(rule[-1]=='+'):
                rule = rule[:-2]
            # print(rule)
            if('|' in maxx):
                maxx = int(maxx.split('|')[1])
            else:
                maxx = int(maxx.split('(')[1].split(')')[0])
            # print(stats)
            # print(maxx)
            dummy = []
            for i in stats:
                # print(len(i.split()))
                if(len(i.split()) <= maxx):
                    dummy.append(i)
            stats = dummy[:]
            # print(stats)
            dum1 = rule.split('^',1)[0]
            dum2 = rule.split('+',1)[0]
            if(len(dum1)>len(dum2)):         
                x = rule.split('+',1)[0]
                y = rule.split('+',1)[1]
            else:
                x = rule.split('^',1)[0]
                y = rule.split('^',1)[1]
            k=0
            flag=1
            inc=1
            while(flag):
                if(inc==1):
                    if(y[0]=='>' or y[1]=='>' or y[2]=='>'):
                        if(y[0]=='>'):
                            k=1
                        elif(y[1]=='>'):
                            k=2
                        else:
                            k=3
                        dum1 = rule.split('^',1)[0]
                        dum2 = rule.split('+',1)[0]
                        if(len(dum1)<len(dum2)):
                            inc=0
                        rule = rule[len(x)+k+1:]
                        # print(x.split('"')[0])
                        try:
                            mak = int(x.split('"')[0].split('(')[1].split(')')[0])
                            # print(mak,'mak')
                        except:
                            mak=-1
                        x = x.split('"')[1]
                        # print(x)
                        dummy = []
                        x = x.split(',')
                        for i in stats:
                            for j in x:
                                if(j in i):
                                    before = i.split(j,1)[0].split()
                                    if(mak==-1 or len(before)<=mak):
                                        i = i.split(j,1)[1]
                                        dummy.append(i)
                                        break
                        stats = dummy[:]
                        # print('exist after first word')
                    else:
                        # print(x)
                        x = x.split('"')[1]
                        # print(x)
                        dummy = []
                        x = x.split(',')
                        for i in stats:
                            for j in x:
                                if(j in i):
                                    dummy.append(i)
                                    break
                        stats = dummy[:]
                        dum1 = rule.split('^',1)[0]
                        dum2 = rule.split('+',1)[0]
                        if(len(dum1)<len(dum2)):
                            inc=0
                        rule = y
                        if(rule=='   '):
                            flag=0
                else:
                    if(y[0]=='>' or y[1]=='>' or y[2]=='>'):
                        if(y[0]=='>'):
                            k=1
                        elif(y[1]=='>'):
                            k=2
                        else:
                            k=3
                        dum1 = rule.split('^',1)[0]
                        dum2 = rule.split('+',1)[0]
                        if(len(dum1)>len(dum2)):
                            inc=1
                        rule = rule[len(x)+k+1:]
                        # print(x.split('"')[0])
                        try:
                            mak = int(x.split('"')[0].split('(')[1].split(')')[0])
                            # print(mak,'mak')
                        except:
                            mak=-1
                        x = x.split('"')[1]
                        # print(x)
                        dummy = []
                        x = x.split(',')
                        for i in stats:
                            for j in x:
                                if(j not in i):
                                        dummy.append(i)
                                        break
                        stats = dummy[:]
                        # print('exist after first word')
                    else:
                        # print(x)
                        x = x.split('"')[1]
                        # print(x)
                        dummy = []
                        x = x.split(',')
                        for i in stats:
                            for j in x:
                                if(j not in i):
                                    dummy.append(i)
                                    break
                        stats = dummy[:]
                        dum1 = rule.split('^',1)[0]
                        dum2 = rule.split('+',1)[0]
                        if(len(dum1)>len(dum2)):
                            inc=1
                        rule = y
                        if(rule=='   '):
                            flag=0
                    # print("exist in statement")
                # print(rule)
                # print(stats)
                dum1 = rule.split('^',1)[0]
                dum2 = rule.split('+',1)[0]
                if(len(dum2)<len(dum1)):
                    x = rule.split('+',1)[0]
                    try:
                        y = rule.split('+',1)[1]
                    except:
                        y = '   '
                else:
                    x = rule.split('^',1)[0]
                    try:
                        y = rule.split('^',1)[1]
                    except:
                        y='   '
            if(len(stats)==0):
                print(False)
                try:
                    fore = float(r[4][1].get())
                except:
                    fore=0
                r[3][1].set('0')
                r[2][1].set(str(0-fore))

            else:
                print(True)
                r[3][1].set('1')
                try:
                    fore = float(r[4][1].get())
                except:
                    fore=0
                r[2][1].set(str(1-fore))
            print('------------------------------------------------')
    reverse_grouping_text()

def reverse_grouping_text():
    global text_logs,report_log
    g1=[]
    g2=[]
    g1flag=0
    g2flag=0
    for r in qwe:
        rule = r[0][1].get()
        # print(rule)
        if(rule!='Average'):
            # print(rule)
            group1 = r[12][1].get()
            group2 = r[13][1].get()
            # print(group1,group2)
            try: 
                dev = float(r[2][1].get())
            except:
                dev=''
            try:
                maxx = float(r[14][1].get())
            except:
                maxx=''
            if(group1==1 and g1flag==0):
                if(dev==''):
                    print('dev for '+ rule +' not defined')
                    text_logs+='dev for '+ rule +' not defined'+'\n'
                    g1=[]
                    g1flag=1
                    continue
                if(maxx!='' and abs(dev)>maxx):
                    print('Max conflict in group 1')
                    text_logs+='Max conflict in group 1'+'\n'
                    g1=[]
                    g1flag=1
                    continue
                triggers = []
                for i in range(5,11):
                    try:
                        triggers.append(float(r[i][1].get()))
                    except:
                        triggers.append('')
                # print('len of triggers',len(triggers))
                # if(len(triggers)!=6):
                #     print('values for LT-UT not correctly defined in group 1')
                #     text_logs+='values for LT-UT not correctly defined in group 1'+'\n'
                #     g1=[]
                #     g1flag=1
                #     continue
                g1.append((r,triggers))
            if(group2==1 and g2flag==0):
                if(dev==''):
                    print('dev for '+ rule +' not defined')
                    text_logs+='dev for '+ rule +' not defined'+'\n'
                    g2=[]
                    g2flag=1
                    continue
                if(maxx!='' and abs(dev)>maxx):
                    print('Max conflict in group 2')
                    text_logs+='Max conflict in group 2'+'\n'
                    g2=[]
                    g2flag=1
                    continue
                triggers = []
                for i in range(5,11):
                    try:
                        triggers.append(float(r[i][1].get()))
                    except:
                        triggers.append('')
                # if(len(triggers)!=6):
                #     print('values for LT-UT not correctly defined in group 2')
                #     text_logs+='values for LT-UT not correctly defined in group 2'+'\n'
                #     g2=[]
                #     g2flag=1
                #     continue
                g2.append((r,triggers))
    if(g1==[]):
        g1signal = 0
    else:
        g1signal = get_signal(g1)
        if(g1signal==0):
            report_log+=str(datetime.now()) + ' - Conflict inside group g1\n'
        print(g1signal,'g1signal')
    if(g2==[]):
        g2signal = 0
    else:
        g2signal = get_signal(g2)
        if(g2signal==0):
            report_log+=str(datetime.now()) + ' - Conflict inside group g2\n'
    print(g1signal,'g1',g2signal,'g2')
    if(g1signal==0 and g2signal==0):
        print('NO SIGNAL')
        text_logs+='NO SIGNAL'+'\n'
        report_log+=str(datetime.now()) + ' - NT\n'
        qwe[-1][1][1].set('NT')
    elif(g1signal==0):
        if(g2signal[0]==0):
            print('BUY'+ str(g2signal[1]) + ' signal sent')
            text_logs+='BUY'+ str(g2signal[1]) + ' signal sent'+'\n'
            report_log+=str(datetime.now()) + ' - BUY'+ str(g2signal[1]) + ' signal sent\n'
            qwe[-1][1][1].set('BUY'+ str(g2signal[1]))
            send_signal('1|' + str(g2signal[1]))
        else:
            print('SELL'+ str(g2signal[1]) + ' signal sent')
            text_logs+='SELL'+ str(g2signal[1]) + ' signal sent'+'\n'
            report_log+=str(datetime.now()) + ' - SELL'+ str(g2signal[1]) + ' signal sent\n'
            qwe[-1][1][1].set('SELL'+ str(g2signal[1]))
            send_signal('1|-'+ str(g2signal[1]))
    elif(g2signal==0):
        if(g1signal[0]==0):
            print('BUY'+ str(g1signal[1]) + ' signal sent')
            text_logs+='BUY'+ str(g1signal[1]) + ' signal sent'+'\n'
            report_log+=str(datetime.now()) + ' - BUY'+ str(g1signal[1]) + ' signal sent\n'
            qwe[-1][1][1].set('BUY'+ str(g1signal[1]))
            send_signal('1|' + str(g1signal[1]))
        else:
            print('SELL'+ str(g1signal[1]) + ' signal sent')
            text_logs+='SELL'+ str(g1signal[1]) + ' signal sent'+'\n'
            report_log+=str(datetime.now()) + ' - SELL'+ str(g1signal[1]) + ' signal sent\n'
            qwe[-1][1][1].set('SELL'+ str(g1signal[1]))
            send_signal('1|-'+ str(g1signal[1]))
    else:
        if(g1signal[0]==0 and g2signal[0]==0):
            print('BUY' + str(max(g1signal[1],g2signal[1])) + ' signal sent')
            text_logs+='BUY' + str(max(g1signal[1],g2signal[1])) + ' signal sent'+'\n'
            report_log+=str(datetime.now()) + ' - BUY' + str(max(g1signal[1],g2signal[1])) + ' signal sent\n'
            qwe[-1][1][1].set('BUY' + str(max(g1signal[1],g2signal[1])))
            send_signal('1|' + str(max(g1signal[1],g2signal[1])))
        elif(g1signal[0]==1 and g2signal[0]==1):
            print('SELL' + str(max(g1signal[1],g2signal[1])) + ' signal sent')
            text_logs+='SELL' + str(max(g1signal[1],g2signal[1])) + ' signal sent'+'\n'
            report_log+=str(datetime.now()) + ' - SELL' + str(max(g1signal[1],g2signal[1])) + ' signal sent\n'
            qwe[-1][1][1].set('SELL' + str(max(g1signal[1],g2signal[1])))
            send_signal('1|-' + str(max(g1signal[1],g2signal[1])))
        else:
            print('NO SIGNAL SENT,conflict between g1 and g2')
            text_logs+='NO SIGNAL SENT,conflict between g1 and g2'+'\n'
            report_log+=str(datetime.now()) + ' - NO SIGNAL SENT,conflict between g1 and g2'+'\n'
            qwe[-1][1][1].set('NT')

def get_signal(g):
    global text_logs
    fsignal = ''
    for r in g:
        dev = float(r[0][2][1].get())
        triggers = r[1]
        if(triggers[0]!='' and dev<=triggers[0]):
            signal=(1,3)
        elif(triggers[1]!='' and dev<=triggers[1]):
            signal=(1,2)
        elif(triggers[2]!='' and dev<=triggers[2]):
            signal=(1,1)
        elif(triggers[5]!='' and dev>=triggers[5]):
            signal=(0,3)
        elif(triggers[4]!='' and dev>=triggers[4]):
            signal=(0,2)
        elif(triggers[3]!='' and dev>=triggers[3]):
            signal=(0,1)
        else:
            signal=0
        # if(signal==0):
        #     print('Conflict')
        #     text_logs+='Conflict in triggers'+'\n'
        #     return 0
        # print('tuple length',len(r[11]))
        print('this is a signal ........ ',signal)
        if(signal!=0):
            if(r[0][11][1].get()==1):
                signal = (1-signal[0],signal[1]) 
            if(fsignal==''):
                fsignal=signal
            elif(fsignal[0]==0 and signal[0]==0):
                fsignal = (0,max(fsignal[1],signal[1]))
            elif(fsignal[0]==1 and signal[0]==1):
                fsignal = (1,max(fsignal[1],signal[1]))
            else:
                print('Conflict')
                print('this is a conflict')
                text_logs+='Conflict inside group'+'\n'
                return 0
    if(fsignal==''):
        return 0
    return fsignal


def calc(lst):
    # print(lst)
    global years_in_pdf,repo_rate_data
    repo_rate_data = {}
    # print(lst[0])
    k=0
    avg=0
    # print(years_in_pdf)
    yr=0
    for i in lst[1:len(years_in_pdf)+1]:
        val = i.replace('–','-')
        val = val.split('(')
        ini = float(val[0])
        if(len(val)==1):
            fin  = ini
        else:
            fin = float(val[1].split(')')[0])
        if(lst[0]=='Repo rate, per cent'):
            repo_rate_data[str(years_in_pdf[yr])] = (ini,fin)
            yr+=1
        if(ini!=fin):
            k+=1
        avg+=(ini-fin)
    if k==0:
        print('average','undefined')
    else:
        print('average',"{:.2f}".format(avg/k))


def pdf_rules_calculations():
    global signal_p,pdf_logs,report_log
    signal_p=''
    forecasts = {}
    maxx = {}
    for i,yr in enumerate(years):
        try:
            forecasts[yr] = float(qwe_pdf[4][i][1].get())
        except Exception as e:
            print(e)
            forecasts[yr] = '-'
        try:
            maxx[yr] = float(qwe_pdf[11][i][1].get())
        except Exception as e:
            print(e)
            maxx[yr] = '-'

    k=0
    dev = []
    summ=0
    j=0
    minusflag=0
    plusflag=0
    print(repo_rate_data)
    if(repo_rate_data=={}):
        pdf_logs+='Repo rate data not found in press release table.'
        # report_log+='Repo rate data not found in press release table.'
        return
    for i in years:
        if i in years_in_pdf:
            qwe_pdf[3][k][1].set(repo_rate_data[i][0])
            qwe_pdf[2][k][1].set("{:.2f}".format(repo_rate_data[i][0]-repo_rate_data[i][1]))
            devv = float("{:.2f}".format(repo_rate_data[i][0]-repo_rate_data[i][1]))
            devvv =(repo_rate_data[i][0]-repo_rate_data[i][1]) 
            summ+=devvv
            if(devvv!=0):
                j+=1
            if(devvv>0):
                plusflag=1
                dev.append(1)
            elif(devvv<0):
                minusflag=1
                dev.append(-1)
            else:
                dev.append(devvv)
            if(forecasts[i]=='-'):
                signal_p+= 'No signal, forecast not given for year ' + str(i) + "\n"
                pdf_logs+= 'No signal, forecast not given for year ' + str(i) + "\n"
            if(forecasts[i]!='-' and forecasts[i]!=repo_rate_data[i][1]):
                signal_p += "No signal, forecasts didn't match in pdf rules "
                pdf_logs+="No signal, forecasts didn't match in pdf rules"+'\n' 
            if(maxx[i]!='-' and abs(devv)>=maxx[i]):
                signal_p += "No signal, dev greater than max in pdf rules "
                pdf_logs+='No signal, dev greater than max in pdf rules '+'\n'
            k+=1
        else:
            k+=1
    if(minusflag==1 and plusflag==1):
        signal_p+='Sides not sorted in pdf rules '
        pdf_logs+='Sides not sorted in pdf rules '+'\n'
    sorted_list = dev[:]
    sorted_list.sort()
    reversed_list = sorted_list[:]
    reversed_list.reverse()
    # print(dev)
    # print(sorted_list)
    if(sorted_list!=dev and reversed_list!=dev):
        signal_p+='Sides not sorted in pdf rules. '
        pdf_logs+='Sides not sorted in pdf rules. '+'\n'
    # if(signal==''):
    #     signal='Buy or Sell'
    if(j!=0):
        qwe_pdf[2][5][1].set("{:.2f}".format(summ/j))
        avg=summ/j
    else:
        qwe_pdf[2][5][1].set('0')
        avg=0
    max_avg = qwe_pdf[11][5][1].get()
    try:
        max_avg = float(max_avg)
        if(abs(avg)>max_avg):
            signal_p='NT'
            print('max safety for average not met')
            pdf_logs+='max safety for average not met'+'\n'
    except:
        print('No max safety assigned for average.')
        pdf_logs+='No max safety assigned for average.'+'\n'
    triggers = []
    for i in range(5,11):
        try:
            triggers.append(float(qwe_pdf[i][5][1].get()))
        except:
            triggers.append('')
    if(signal_p==''):  
        # if(len(triggers)==6):
            if(triggers[0]!='' and avg<=triggers[0]):
                signal_p='SELL3'
                send_signal('1|-3')
            elif(triggers[1]!='' and avg<=triggers[1]):
                signal_p='SELL2'
                send_signal('1|-2')
            elif(triggers[2]!='' and avg<=triggers[2]):
                signal_p='SELL1'
                send_signal('1|-1')
            elif(triggers[5]!='' and avg>=triggers[5]):
                signal_p='BUY3'
                send_signal('1|3')
            elif(triggers[4]!='' and avg>=triggers[4]):
                signal_p='BUY2'
                send_signal('1|2')
            elif(triggers[3]!='' and avg>=triggers[3]):
                signal_p='BUY1'
                send_signal('1|1')
            else:
                signal_p='NT'
        # else:
        #     print('There is some problem with UT/LT values,please check them in pdf rules.')
        #     pdf_logs+='There is some problem with UT/LT values,please check them in pdf rules.'+'\n'
        #     signal='NT'
    else:
        signal_p='NT'
    pdf_logs+='Signal: ' + signal_p +'\n'
    report_log += str(datetime.now()) + ' - ' + signal_p + ' sent.\n'

    qwe_pdf[1][5][1].set(signal_p)


def display_logs():
    global current_view,logs,rules_headers,text_logs,text_state,qwe,text_rules_logs
    text_state = []
    if(current_view!='logs'):
        text_rules_table.grid_forget()
        text_rules_logs.grid()
        lines = text_logs.split('\n')
        logs.delete(0,tk.END)
        for l in lines:
            logs.insert(tk.END,l)
        
    current_view='logs'

def display_logs_pdf():
    global current_view_pdf,logs_pdf,rules_headers_pdf,pdf_logs,scrollbar
    if(current_view_pdf!='logs'):
        pdf_rules_logs.grid()
        pdf_rules_table.grid_forget()
        lines = pdf_logs.split('\n')
        logs_pdf.delete(0,tk.END)
        for l in lines:
            logs_pdf.insert(tk.END,l)
        current_view_pdf='logs'


def display_trade_setup():
    global current_view,logs,text_rules_table
    if(current_view!='setup'):
        text_rules_logs.grid_forget()
        text_rules_table.grid()
    current_view='setup'
import time
def display_trade_setup_pdf():
    global current_view_pdf,logs_pdf,scrollbar
    if(current_view_pdf!='setup'):
        pdf_rules_logs.grid_forget()
        pdf_rules_table.grid()
    current_view_pdf='setup'


def display_rule_headers_pdf():
    global rules_headers_pdf
    for idx,head in enumerate(headings2):
        width=8
        if(head=='Repo Rate'):
            width=30
        header = tk.Label(pdf_rules_table,text=head,relief='raised',height=2,width=width)
        rules_headers_pdf.append(header)
        # print(header)
        header.grid(row=2,column=idx)


def display_rule_headers():
    global rules_headers,text_rules_table
    for idx,head in enumerate(headings):
        width = 8
        if(head=='Name'):
            width=65
        elif(head=='R' or head=='G1' or head=='G2'):
            width=3
        header = tk.Label(text_rules_table,text=head,relief="raised",highlightbackground='black',height=2,width=width)
        rules_headers.append(header)
        # print(header)
        header.grid(row=0,column=idx)

def display_rules_pdf():
    global qwe_pdf
    qwe_pdf = []
    for idx,head in enumerate(headings2):
        width=8
        if(head=='Repo Rate'):
            width=30
        items = []
        for j in range(6):
            var  = tk.StringVar()
            text = tk.Entry(pdf_rules_table,width=width,bg=greens[idx],text=var,highlightcolor='black')
            items.append((text,var))
            text.grid(row=j+3,column=idx)
        qwe_pdf.append(items)
    change_years()

def display_rules():
    global num_rows,qwe,text_rules_table
    qwe=[]
    num_rows=0
    for idx,i in enumerate(rules):
        add_row(text_rules_table,i,num_rows+1,1)
        num_rows+=1
    fixed_rows_val = ['Repo Rate - number','Average']
    for idx,head  in enumerate(fixed_rows_val):
        add_row(text_rules_table,head,idx+100,0)


def select_file(var):
    # print(var)
    filename = askopenfilename()
    if(filename==() or filename==''):
        print("file not selected")
    else:
        print(filename)
        var.set(filename)


def add_new_rule():
    global num_rows
    # print("add rule")
    rule = wording.get()
    # print(rule)
    
    if(rule!=''):
        rules.append(rule)
        add_row(text_rules_table,rule,num_rows+1,1)
        num_rows+=1

def delete_row(event):
    global del_row
    del_row.destroy()
    print("removing rule")
    for row_num,row in enumerate(qwe):
        # print(row_num,row)
        if(row[15][0]==event.widget):
            rule = row[0][1].get()
            # print(rule)
            for item in row:
                item[0].destroy()
                try:
                    item[1].destroy()
                except:
                    pass
            qwe.pop(row_num)
            
            # print(rule)
            rules.remove(rule)


def delete_row_pop(event):
    global master,del_row
    del_row = tk.Toplevel(master)
    del_row.geometry('350x75')
    del_row.configure(bg='white')
    top_frame = tk.Frame(del_row,bd=1,padx=2,pady=2,bg='white',width=350)
    top_frame.grid(row=0,sticky='w')
    tk.Label(top_frame, text='Are you sure that you want to delete this rule.',padx=2,bg='white').grid(row=0,column=0,columnspan=2)
    tk.Button(top_frame,text='Yes', command= lambda: delete_row(event)).grid(row=2,column=0)
    tk.Button(top_frame,text='No', command=del_row.destroy).grid(row=2,column=1)
    

def change_start_year(*args):
    global years
    years = []
    # print('start year')
    # print(start_year.get())
    try:
        end = year_end.get()
    except:
        return
    for i in range(int(start_year.get()),int(end)+1):
        years.append(str(i))
    # print(years)
    if(len(years)>5):
        years = years[0:5]
    try:
        change_years()
    except:
        pass


def change_year_end(*args):
    global years
    years = []
    # print('year end')
    # print(year_end.get())
    for i in range(int(start_year.get()),int(year_end.get())+1):
        years.append(str(i))
    # print(years)
    if(len(years)>5):
        years = years[0:5]
    try:
        change_years()
    except:
        pass

def change_years():
    global years
    n = len(years)
    # print(years)
    for idx,year in enumerate(years):
        if(idx<=4):
            qwe_pdf[0][idx][1].set(year)
    for i in range(5-n):
        if(n+i<=4):
            qwe_pdf[0][n+i][1].set('')
    qwe_pdf[0][5][1].set('Average')

def changecolor():
    print('changing colors')
    ori = ['red2','firebrick1','IndianRed1','SeaGreen2','SpringGreen2','green2']
    rev = ['green2','SpringGreen2','SeaGreen2','IndianRed1','firebrick1','red2']
    for row in qwe:
        # print(row[11][1].get())
        if(row[11][1].get()==1):
            for i in range(5,11):
                row[i][0].configure(bg=rev[i-5])
        else:
            for i in range(5,11):
                row[i][0].configure(bg=ori[i-5])


def add_row(base,entry,row,dell):
    global qwe
    items = []
    for idx,head in enumerate(headings):
        width = 8
        if(head=='Name'):
            width=65
        elif(head=='R' or head=='G1' or head=='G2'):
            width=3
        if(head=='R' or head=='G1' or head=='G2'):
            var = tk.IntVar()
            c = tk.Checkbutton(base,variable=var,command=changecolor)
            # c.bind("<Button-1>", changecolor)
            c.val=var
            items.append((c,var))
            c.grid(row=row,column=idx)
        elif(head=='Action' and dell==1):
            bot = tk.Label(base,text='Delete',width=width,bg='grey')
            bot.bind("<Button-1>", delete_row_pop)
            items.append((bot,0))
            bot.grid(row=row,column=idx)
        else:
            var = tk.StringVar()
            text = tk.Entry(base,width=width,highlightcolor='black',bg=greens[idx],text=var)
            if(head=='Name'):
                var.set(entry)
            items.append((text,var))
            text.grid(row=row,column=idx)
            
    n = len(qwe)
    if(dell==0):
        qwe.append(items)
    else:
        qwe.insert(n-2,items)

def reset_text_rules():
    for ro in qwe:
        ro[1][1].set('')
        ro[2][1].set('')
        ro[3][1].set('')

def reset_pdf_rules():
    for i in range(6):
        qwe_pdf[1][i][1].set('')
        qwe_pdf[2][i][1].set('')
        qwe_pdf[3][i][1].set('')

# def save_setup_gui():
#     global master
#     save_gui = tk.Toplevel(master)
#     save_gui.geometry('300x100')
#     save_gui.configure(bg='white')
#     top_frame = tk.Frame(save_gui,bd=1,padx=2,pady=2,bg='white',width=300)
#     top_frame.grid(row=0,sticky='w')
#     tk.Label(top_frame, text='File name',padx=2,bg='white').grid(row=0)
#     var = tk.StringVar()
#     tk.Entry(top_frame, text=var).grid(row=0,column=1,padx=(0,6))
#     tk.Button(top_frame,text='OK', command= lambda: save_setup(save_gui,var)).grid(row=2,column=0,columnspan=2)

# def load_gui():
#     global master
#     load_gui = tk.Toplevel(master)
#     load_gui.geometry('300x100')
#     load_gui.configure(bg='white')
#     top_frame = tk.Frame(load_gui,bd=1,padx=2,pady=2,bg='white',width=300)
#     top_frame.grid(row=0,sticky='w')
#     tk.Label(top_frame, text='File name',padx=2,bg='white').grid(row=0)
#     var = tk.StringVar()
#     tk.Entry(top_frame, text=var).grid(row=0,column=1,padx=(0,6))
#     tk.Button(top_frame,text='OK', command= lambda: load_setup(load_gui,var)).grid(row=2,column=0,columnspan=2)

def save_setup():
    # file_name = arg2.get()
    file_name = asksaveasfilename()
    if(file_name==() or file_name==''):
        print('file not selected')
        return
    # arg1.destroy()
    global interval,mode,port,test_html,test_pdf,live_url,enable_check_pdf,enable_check_text,years,timeout,rules
    inter = interval.get()
    time_out = timeout.get() 
    f_open = open(file_name,'w')
    run_type = mode.get()
    url  = live_url.get()
    html_file_name = test_html.get()
    pdf_file_name = test_pdf.get()
    udp_port = port.get()
    run_pdf = enable_check_pdf.get()
    run_text = enable_check_text.get()
    f_open.write('start;'+inter+';'+time_out+';'+run_type+';'+url+';'+html_file_name+';'+pdf_file_name+'\n')
    f_open.write(udp_port+';'+str(run_text)+';'+str(run_pdf)+'\n')
    
    f_open.write(years[0]+';'+years[-1]+'\n')
    for r in qwe:
        # rule = r[0][1].get()
        # if(rule!='Average'):
        f_open.write('text;')
        for idx,i in enumerate(r):
            if(headings[idx]!='Act1' and headings[idx]!='Dev' and headings[idx]!='Actual' and headings[idx]!='Action'):
                f_open.write(str(r[idx][1].get())+';')
            else:
                f_open.write(';')
        f_open.write('\n')
    
    
    for i in range(6):
        f_open.write('pdf;'+qwe_pdf[0][i][1].get()+';;;;'+qwe_pdf[4][i][1].get()+';'+qwe_pdf[5][i][1].get()+';'+qwe_pdf[6][i][1].get()+';'+qwe_pdf[7][i][1].get()+';'+qwe_pdf[8][i][1].get()+';'+qwe_pdf[9][i][1].get()+';'+qwe_pdf[10][i][1].get()+';'+qwe_pdf[11][i][1].get()+'\n')
    
    f_open.close()
def load_setup():
    # file_name = arg2.get()
    file_name = askopenfilename()
    if(file_name==() or file_name==''):
        print('file not selected')
        return
    # arg1.destroy()
    global num_rows,rules,interval,mode,port,test_html,test_pdf,live_url,enable_check_pdf,enable_check_text,years,start_year,year_end,timeout
    try:
        f_open = open(file_name,'r')
    except:
        print('file not found')
        return
    lines = f_open.readlines()
    pdf_row=0
    text_row=0
    for idx,line in enumerate(lines):
        r = line.replace('\n','')
        r = r.split(';')
        if(idx==0):
            interval.set(r[1])
            timeout.set(r[2])
            mode.set(r[3])
            live_url.set(r[4])
            test_html.set(r[5])
            test_pdf.set(r[6])
        elif(idx==1):
            port.set(r[0])
            enable_check_text.set(int(r[1]))
            enable_check_pdf.set(int(r[2]))
        elif(idx==2):
            start_year.set(r[0])
            year_end.set(r[1])
        else:
            if(r[0]=='text'):
                if(r[1]!='Repo Rate - number' and qwe[text_row][0][1].get()=='Repo Rate - number'):
                    add_row(text_rules_table,r[1],num_rows+1,1)
                    num_rows+=1
                    rules.append(r[1])
                for i,j in enumerate(r[1:]):
                    # print(i,j)
                    
                    # if i==0:
                    #     qwe[text_row][i][1].set("asdfasdfa")
                    #     print(qwe[text_row][i][1],qwe[text_row][i][1].get())
                    #     print("qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
                    if(i==11 or i==12 or i==13):
                        qwe[text_row][i][1].set(int(j))
                    elif(i<=14):
                        qwe[text_row][i][1].set(j)
                text_row+=1
            else:
                for i,j in enumerate(r[1:]):
                    qwe_pdf[i][pdf_row][1].set(j)
                pdf_row+=1

def markers_window():
    print("new window")
    global master
    marker = tk.Toplevel(master)
    marker.geometry('300x100')
    marker.configure(bg='white')
    top_frame = tk.Frame(marker,bd=1,padx=2,pady=2,bg='white',width=300)
    top_frame.grid(row=0,sticky='w')
    tk.Label(top_frame, text='Start Keyword',padx=2,bg='white').grid(row=0)
    tk.Label(top_frame, text='End Keyword',padx=2,bg='white').grid(row=1)
    var1 = tk.StringVar()
    var2 = tk.StringVar()
    tk.Entry(top_frame, text=var1).grid(row=0,column=1,padx=(0,6))
    tk.Entry(top_frame, text=var2).grid(row=1,column=1,padx=(0,6))
    tk.Button(top_frame,text='OK', command=lambda : markerdestroy(marker,var1,var2)).grid(row=2,column=0,columnspan=2)

def markerdestroy(marker,var1,var2):
    global start_marker,end_marker
    start_marker = var1.get()
    end_marker = var2.get()
    marker.destroy()
    print(start_marker,end_marker)

rules = ['"activity"+"economy,economic" + >"high,strong"+max(20)','"Executive Board"+ >"decided"+ >"repo rate unchanged" + >"-0.25" +max(20)','"repo rate"+ >"raised,raise,increase,increased" + >(3)"end of the year" - > "faster pace"+ max(40)']

button_width=8
master = tk.Tk(className='Riskbank Report Analyze Tools')
master.geometry('2000x1000')
master.configure(bg='white')


top_frame = tk.Frame(master,bd=1,padx=2,pady=2,bg='white',width=2000)
top_frame.grid(row=0,sticky='w')

tk.Label(top_frame, text='REQUEST INTERVAL (MS)',padx=2,bg='white').grid(row=0)
tk.Label(top_frame, text='TIMEOUT (SEC)',padx=2,bg='white').grid(row=1)
interval = tk.StringVar() 
tk.Entry(top_frame, text=interval).grid(row=0,column=1,padx=(0,6))
timeout = tk.StringVar() 
tk.Entry(top_frame, text=timeout).grid(row=1,column=1,padx=(0,6))

startstop = tk.Frame(top_frame)
startstop.grid(row=2,column=0,rowspan=2,columnspan=2)
start = tk.Button(startstop, text='Start',width=button_width, command=startt).grid(row=0)
stop = tk.Button(startstop, text='Stop',width=button_width,command=stop).grid(row=0,column=1)

tk.Label(top_frame, text='Run Mode',padx=2,pady=0,bg='white').grid(row=0, column=2)
tk.Label(top_frame, text='Live URL',padx=2,pady=0,bg='white').grid(row=1, column=2)
tk.Label(top_frame, text='Test PDF',padx=2,pady=0,bg='white').grid(row=2, column=2)
tk.Label(top_frame, text='Test HTML',padx=2,pady=0,bg='white').grid(row=3, column=2)

mode = tk.StringVar(top_frame)
mode.set('Live Mode')
tk.OptionMenu(top_frame, mode, 'Live Mode','Test Mode').grid(row=0,column=3,sticky='w')
live_url = tk.StringVar()
tk.Entry(top_frame, width=60, textvariable=live_url).grid(row=1,column=3)
test_pdf = tk.StringVar()
tk.Entry(top_frame, width=60, textvariable=test_pdf).grid(row=2,column=3)
test_html = tk.StringVar()
tk.Entry(top_frame, width=60, textvariable=test_html).grid(row=3,column=3)

browse_pdf = tk.Button(top_frame, text='Browse...',padx=2, width=button_width,command= lambda: select_file(test_pdf)).grid(row=2,column=4,padx=(10,10))
browse_html = tk.Button(top_frame, text='Browse...',padx=2, width=button_width, command= lambda: select_file(test_html)).grid(row=3,column=4,padx=(10,10))

Add_wording_frame = tk.LabelFrame(top_frame,text='Add Wordings',padx=2,bg='white')
Add_wording_frame.grid(row=0,column=5,rowspan=4,padx=(40,40))
wording  = tk.StringVar()
tk.Entry(Add_wording_frame, textvariable=wording).grid(row=0,pady=(4,4))
add_wording = tk.Button(Add_wording_frame, text='Add',width=button_width, command=add_new_rule).grid(row=1,padx=(2,2))

UDP_frame = tk.LabelFrame(top_frame,text='UDP Port',padx=2,bg='white')
UDP_frame.grid(row=0,column=6,rowspan=4)
port = tk.StringVar()
tk.Entry(UDP_frame, text=port).grid(row=0,pady=(2,2))

tk.Button(top_frame, text='MARKERS',width=button_width,command=markers_window).grid(row=0,column=7,padx=(2,2))
tk.Button(top_frame, text='Save',width=button_width,command=save_setup).grid(row=2,column=7,padx=(2,2))
load = tk.Button(top_frame, text='Load',width=button_width,command=load_setup).grid(row=2,column=8,padx=(2,2))

progress = tk.LabelFrame(master,text='Progress',bg='white')
progress.grid(row=1,sticky='w',pady=(2,2))
prog = tk.StringVar()
prog.set('')
tk.Label(progress,textvariable=prog,width=200,bg='white',height=2).grid(row=0,sticky='w')


text_rules = tk.LabelFrame(master,text='Text Rules', bg='white',width=4000)
text_rules.grid(row=2,sticky='w',pady=(0,0),padx=(0,0))

bots = tk.Frame(text_rules,bg='white')
bots.grid(row=0,columnspan=2,sticky='w')
tk.Button(bots,text='Trade Setup',width=button_width,command=display_trade_setup).grid(row=0,pady=(2,0))
tk.Button(bots, text='Log',width=button_width, command=display_logs).grid(row=0,column=1,pady=(2,0))

tk.Button(bots,text='Reset',width=button_width, command=reset_text_rules).grid(row=0,column=4,padx=(4,0))
enable_check_text = tk.IntVar()
tk.Checkbutton(bots,text='Enable',bg='white', variable=enable_check_text).grid(row=0,column=5)
text_rules_table = tk.Frame(text_rules)
text_rules_logs = tk.Frame(text_rules)
text_rules_logs.grid(row=1,sticky='w')
text_rules_table.grid(row=1,sticky='w')
scrollbar = tk.Scrollbar(text_rules_logs,orient="vertical")
scrollbar.grid(row=0,column=1)
logs = tk.Listbox(text_rules_logs, yscrollcommand = scrollbar.set,width=179,height=9 )
logs.grid(row=0,column=0,sticky='w')
scrollbar.config( command = logs.yview )
display_rule_headers()

display_rules()
text_rules_logs.grid_forget()


pdf_rules = tk.LabelFrame(master,bg='white',text='Pdf Rules')
pdf_rules.grid(row=4,sticky='w',pady=(4,0),padx=(2,2))

headers  = tk.Frame(pdf_rules,bg='white')
headers.grid(row=0,columnspan=10,sticky='w') 
tk.Label(headers,text='Report Year',bg='white').grid(row=0,column=0)
report_year = tk.Entry(headers).grid(row=0,column=1)
tk.Label(headers,text='Year Start',padx=2,bg='white').grid(row=0,column=2)
start_year = tk.StringVar(pdf_rules)
start_year.trace('w',change_start_year)
start_year.set('2018')
tk.OptionMenu(headers,start_year,'2016','2017','2018','2019','2020','2021','2022','2023').grid(row=0,column=3)
tk.Label(headers,text='Year End',padx=2,bg='white').grid(row=0,column=4)
year_end = tk.StringVar(pdf_rules)
year_end.trace('w',change_year_end)
year_end.set('2023')
tk.OptionMenu(headers,year_end,'2016','2017','2018','2019','2020','2021','2022','2023').grid(row=0,column=5)

bots = tk.Frame(pdf_rules,bg='white')
bots.grid(row=1,columnspan=2,sticky='w')
tk.Button(bots,text='Trade Setup',width=button_width,command=display_trade_setup_pdf).grid(row=0,pady=(2,0))
tk.Button(bots, text='Log',width=button_width, command=display_logs_pdf).grid(row=0,column=1,pady=(2,0))

tk.Button(headers,text='Reset',width=button_width, command=reset_pdf_rules).grid(column=6,row=0,columnspan=5,padx=(4,0))
enable_check_pdf = tk.IntVar() 
tk.Checkbutton(headers,text='Enable',bg='white',variable=enable_check_pdf).grid(row=0,column=11)

pdf_rules_table = tk.Frame(pdf_rules)
pdf_rules_logs = tk.Frame(pdf_rules)
pdf_rules_logs.grid(row=2,sticky='w')
pdf_rules_table.grid(row=2,sticky='w')
scrollbar_pdf = tk.Scrollbar(pdf_rules_logs,orient="vertical")
scrollbar_pdf.grid(row=0,column=1)
logs_pdf = tk.Listbox(pdf_rules_logs, yscrollcommand = scrollbar.set,width=179,height=9 )
logs_pdf.grid(row=0,column=0,sticky='w')
scrollbar_pdf.config( command = logs_pdf.yview )

display_rule_headers_pdf()
display_rules_pdf()
pdf_rules_logs.grid_forget()
master.mainloop()