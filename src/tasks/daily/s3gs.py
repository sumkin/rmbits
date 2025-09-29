import os
import sys
import csv
import traceback
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta
from currency_converter import CurrencyConverter

from emailutils import *
from s3utils import *
from grpxlrdr import *
from groupseval import *

cc = CurrencyConverter()

def get_products(segs,pos,bc,paxcnt):
    fcstdt = datetime.now() - timedelta(days = 1)
    fcstdate = datetime.strftime(fcstdt, '%Y%m%d')

    outb = []
    # First two segments are outbound trip. 
    for seg in segs[:2]:
        # seg = [depdt,orgn,dstn,fltnum]
        if seg[0] is None or seg[1] is None or seg[2] is None or seg[3] is None:
            continue    
        depdate = datetime.strftime(seg[0],'%Y%m%d')
        fcstdateout, depdateout = LPReaderFDC.determine_dates(fcstdate, depdate)
        if fcstdateout is None:
            return [],[],[]
        outb.append(seg[1])
        outb.append(seg[2])
        outb.append(depdate)
        outb.append(fcstdateout)
        outb.append(depdateout)
        outb.append(seg[3])
    outb.append(pos)
    outb.append(bc)
    outb.append(paxcnt)
    if depdate == depdateout:
        outb.append('remaining')
    else:
        outb.append('final')

    inb = []
    # Third and fourth segments are inbound trip.
    if len(segs) > 2:
        for seg in segs[2:4]:
            # seg = [depdt,dow,orgn,dstn,fltnum]
            if seg[0] is None or seg[1] is None or seg[2] is None or seg[3] is None:
                continue
            depdate = datetime.strftime(seg[0], '%Y%m%d')
            fcstdatein, depdatein = LPReaderFDC.determine_dates(fcstdate, depdate)
            if fcstdatein is None:
                return [],[],[]
            inb.append(seg[1])
            inb.append(seg[2])
            inb.append(depdate)
            inb.append(fcstdatein)
            inb.append(depdatein)
            inb.append(seg[3])
        inb.append(pos)
        inb.append(bc)
        inb.append(paxcnt)
        if depdate == depdatein:
            inb.append('remaining')
        else:
            inb.append('final')

    # Fourth and fifth segments are additional trips.
    seg5 = []
    if len(segs) > 4:
        if segs[4][0] is not None or segs[4][1] is not None or segs[4][2] is not None or segs[4][3] is not None:
            # seg = [depdt,dow,orgn,dstn,fltnum]
            seg = segs[4]
            depdate = datetime.strftime(seg[0], '%Y%m%d')
            fcstdatea, depdatea = LPReaderFDC.determine_dates(fcstdate, depdate)
            if fcstdatea is None:
                return [],[],[],[]
            seg5.append(seg[1])
            seg5.append(seg[2])
            seg5.append(depdate)
            seg5.append(fcstdatea)
            seg5.append(depdatea)
            seg5.append(seg[3])
            seg5.append(pos)
            seg5.append(bc)
            seg5.append(paxcnt)
            if depdate == depdatea:
                seg5.append('remaining')
            else:
                seg5.append('final')   
 
    seg6 = []
    if len(segs) > 5:
        if segs[5][0] is not None or segs[5][1] is not None or segs[5][2] is not None or segs[5][3] is not None:
            # seg = [depdt,dow,orgn,dstn,fltnum]
            seg = segs[5]
            depdate = datetime.strftime(seg[0], '%Y%m%d')
            fcstdatea, depdatea = LPReaderFDC.determine_dates(fcstdate, depdate)
            if fcstdatea is None:
                return [],[],[],[]
            seg6.append(seg[1])
            seg6.append(seg[2])
            seg6.append(depdate)
            seg6.append(fcstdatea)
            seg6.append(depdatea)
            seg6.append(seg[3])
            seg6.append(pos)
            seg6.append(bc)
            seg6.append(paxcnt)
            if depdate == depdatea:
                seg6.append('remaining')
            else:
                seg6.append('final')

    return outb, inb, seg5, seg6


def process(fname, parallel = True):
    print("Copying to local file...")
    fname_p = fname + '.processed'
    fnames = fname.split('/')
    origfname = fnames[1]
    lfname = '/mnt/data/tmp/' + fnames[1]
    subprocess.check_output(['aws','s3','cp','s3://ay-emr-job/'+fname,lfname])

    print("Generating csv...")
    csv_fname = 'GS_' + fnames[1].split('.')[0] + '.csv'
    csv_fname_fp = '/mnt/data/tmp/' + csv_fname
    with open(csv_fname_fp, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['POS','AGENT','AGENT_ID','TIER','PRODUCT','BC','CUSTOMER_TYPE',\
                            'GROUP_SIZE','INBOUND','OUTBOUND','SEG5','SEG6',\
                            'FCST_DATE_OUTBOUND','DEPARTURE_DATE_OUTBOUND',\
                            'FCST_DATE_INBOUND','DEPARTURE_DATE_INBOUND',\
                            'FCST_DATE_SEG5','DEPARTURE_DATE_SEG5',\
                            'FCST_DATE_SEG6','DEPARTURE_DATE_SEG6',\
                            'DEMAND_OUTBOUND','TAKEN_OUTBOUND','FARE_OUTBOUND','BE_FARE_OUTBOUND','MSPLGOUT','MSPLGSOUT',\
                            'DEMAND_INBOUND','TAKEN_INBOUND','FARE_INBOUND','BE_FARE_INBOUND','MSPLGIN','MSPLGSIN',\
                            'DEMAND_SEG5','TAKEN_SEG5','FARE_SEG5','BE_FARE_SEG5','MSPLG5','MSPLGS5',\
                            'DEMAND_SEG6','TAKEN_SEG6','FARE_SEG6','BE_FARE_SEG6','MSPLG6','MSPLGS6',\
                            'NET_FARE_LC','YR_LC','CURRENCY','NET_FARE_EUR','YR_EUR','ERROR'])
        print('Reading Excel file ', origfname, '...')
        gxr = GroupExcelReader(lfname, origfname)

        def calc(r, outb, inb, seg5, seg6):
            res = [r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]]
            try:
                print('Evaluating outbound...')
                print('outb = ', outb)
                geout = GroupsEvaluator(outb[3], outb[4], outb[len(outb)-1])
                dmdout, solout, fareout, be_fareout, msplgout, msplgsout, error = geout.evaluate(outb)
                print('dmdout, solout, fareout, be_fareout, msplgout, msplgsout, error = ',\
                      dmdout, solout, fareout, be_fareout, msplgout, msplgsout, error)

                print('Evaluating inbound...')
                gein = GroupsEvaluator(inb[3], inb[4], inb[len(inb)-1])
                dmdin, solin, farein, be_farein, msplgin, msplgsin, error = gein.evaluate(inb)
                print('dmdin, solin, farein, be_farein, msplgin, msplgsin, error = ',\
                      dmdin, solin, farein, be_farein, msplgin, msplgsin, error)

                dmd5, sol5, fare5, be_fare5, msplg5, msplgs5 = 0, 0, 0, 0, 999, ''
                if len(seg5) > 0:
                    print('Evaluating segment 5...')
                    ge5 = GroupsEvaluator(seg5[3], seg5[4], seg5[len(seg5)-1])
                    dmd5, sol5, fare5, be_fare5, msplg5, msplgs5, error = ge5.evaluate(seg5)
                    print('dmd5, sol5, fare5, be_fare5, msplg5, msplgs5, error = ',\
                          dmd5, sol5, fare5, be_fare5, msplg5, msplgs5, error)

                dmd6, sol6, fare6, be_fare6, msplg6, msplgs6 = 0, 0, 0, 0, 999, ''
                if len(seg6) > 0:
                    print('Evaluating segment 6...')
                    ge6 = GroupsEvaluator(seg6[3], seg6[4], seg6[len(seg6)-1])
                    dmd6, sol6, fare6, be_fare6, msplg6, msplgs6, error = ge6.evaluate(seg6)
                    print('dmd6, sol6, fare6, be_fare6, msplg6, msplgs6, error = ',\
                          dmd6, sol6, fare6, be_fare6, msplg6, msplgs6, error)
            except Exception as e:
                print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_fname.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                dmdout, solout, fareout, be_fareout, msplgout, msplgsout, error = 0, 0, 0, 0, 999, '', 0
                dmdin, solin, farein, be_farein, msplgin, msplgsin, error = 0, 0, 0, 0, 999, '', 0
                dmd5, sol5, fare5, be_fare5, msplg5, msplgs5, error = 0, 0, 0, 0, 999, '', 0
                dmd6, sol6, fare6, be_fare6, msplg6, msplgs6, error = 0, 0, 0, 0, 999, '', 0
            try:
                outb = [str(e) for e in outb]
                inb = [str(e) for e in inb]
                res += ['-'.join(outb), '-'.join(inb), '-'.join(seg5), '-'.join(seg6)]
                res += [outb[3],outb[4]] 
                res += [inb[3],inb[4]]
                try:
                    res += [seg5[3], seg5[4]]
                except:
                    res += ['','']
                try:
                    res += [seg6[3], seg6[4]]
                except:
                    res += ['','']
                res += [dmdout, solout, fareout, be_fareout, msplgout, msplgsout]
                res += [dmdin, solin, farein, be_farein, msplgin, msplgsin]
                res += [dmd5, sol5, fare5, be_fare5, msplg5, msplgs5]
                res += [dmd6, sol6, fare6, be_fare6, msplg6, msplgs6]
                res += [r[9],r[10],r[11]]
                net_fare_eur, yr_eur = '',''
                if r[9] is not None and r[11] is not None:
                    net_fare_eur = cc.convert(float(r[9]),r[11],'EUR')
                if r[10] is not None and r[11] is not None:
                    yr_eur = cc.convert(float(r[10]),r[11],'EUR')
                res += [net_fare_eur,yr_eur]
                res[4] = ''.join([i if ord(i) < 128 else ' ' for i in res[4]]) # Product name could include non-ascii.
                res += [error]
                return res
            except:
                traceback.print_exc()
                print(e)
                return None

        def outinb(r):
            if r[13] is None or r[13] == 'new':
                pos,bc,paxcnt = r[0],r[5],r[7]
                assert r[8][0][0] > datetime.now()
                # Outbound, inbound, seg5, seg6.
                outb,inb,seg5,seg6 = get_products(r[8],pos,bc,paxcnt)
                print('outb = ', outb)
                print('inb = ', inb)
                if outb is None or inb is None:
                    return None
                return [r,outb,inb,seg5,seg6]
            elif r[13] == 'pending':
                return None
            else:
                print('r = ', r)
                assert False         

        print('Generating tasks...')
        if parallel:
            num_cores = multiprocessing.cpu_count()
            tasks = Parallel(n_jobs = 2)(delayed(outinb)(r) for rownum,r in gxr.read())
            tasks = [t for t in tasks if t is not None]       
        else:
            tasks = []
            for rownum,r in gxr.read():
                task = outinb(r)
                if task is not None:
                    tasks.append(task)

        tasks = tasks[:1]
        print('Calculating tasks...')
        if parallel:
            num_cores = multiprocessing.cpu_count()
            results = Parallel(n_jobs = 2)(delayed(calc)(t[0],t[1],t[2],t[3],t[4]) for t in tasks)
        else:
            results = []
            for t in tasks:
                result = calc(t[0],t[1],t[2],t[3],t[4])
                results.append(result)

        for res in results:
            if res is None:
                continue
            csvwriter.writerow(res)

    print("Zipping file...")
    try:
        subprocess.check_output(['gzip', csv_fname_fp])
    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        traceback.print_tb(exc_tb)
        subprocess.check_output(['rm', csv_fname_fp])
        return

    print("Copying csv file to s3...")
    s3fname = 's3://ay-emr-job/gs/' + csv_fname + '.gz'
    subprocess.check_output(['aws','s3','cp',csv_fname_fp+'.gz',s3fname])

    print("Copying Excel file back...")
    subprocess.check_output(['aws','s3','cp',lfname,'s3://ay-emr-job/' + fname_p])

    subprocess.check_output(['rm',lfname])
    subprocess.check_output(['rm',csv_fname_fp + '.gz'])
    subprocess.check_output(['aws','s3','rm','s3://ay-emr-job/' + fname])


if __name__ == "__main__":
    # Get files in folder.
    fnames = gets3files('ay-emr-job/gs')

    # Filter out processed files.
    fnames = filter(lambda s: 'processed' not in s, fnames)
    fnames = filter(lambda s: 'xlsx' in s, fnames)   

    # Go over files and process them.
    for fname in fnames:
        try:
            print(fname + ' processing...')
            dt_s = datetime.now()
            process(fname, False)
            dt_e = datetime.now()

            seconds = int((dt_e - dt_s).seconds)
            hours = seconds / 3600
            minutes = (seconds - hours * 3600) / 60
            seconds = (seconds - hours * 3600 - minutes * 60)

            sbj = fname + ' has been processed.'
            body = 'Processed in ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds'
            send_quick('fedor.nikitin@finnair.com', 'fedor.nikitin@finnair.com', sbj, body)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            traceback.print_tb(exc_tb)

    print("Done.")

