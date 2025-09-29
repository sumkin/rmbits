import glob
import pandas as pd
import csv


def create_file_from_list(fname,fldr,l):
    with open(fldr+'/'+fname,'wb') as csvfile:
        writer = csv.writer(csvfile) 
        for e in l:
            writer.writerow(e)
    return fldr+'/'+fname 


def merge_files(path, fname_out):
    '''
    Reads all CSV files in <path> and 
    creates one CSV file. It is assumed
    that all files have identical schema.
    '''
    filenames = glob.glob(path + "/*.csv")
    dfs = []
    for filename in filenames:
        dfs.append(pd.read_csv(filename))
    frame = pd.DataFrame()
    frame = pd.concat(dfs)
    frame.to_csv(fname_out)

