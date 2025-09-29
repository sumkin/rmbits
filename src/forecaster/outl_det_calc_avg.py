import os
import csv
import glob
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

low_l = []
high_l = []

for infile in glob.glob(os.path.join('./pb_files_lv','*.csv')):

     #print infile
     csv_reader = csv.reader(open(infile, 'r'), delimiter=',')
     mrkt_num = 0
     mrkt_low_sum = 0
     mrkt_high_sum = 0
     for row in csv_reader:
         if row[1] != 'nan' and row[2] != 'nan':
             mrkt_num = mrkt_num + 1
             mrkt_low_sum = mrkt_low_sum + float(row[1])
             mrkt_high_sum = mrkt_high_sum + float(row[2])
     if mrkt_num != 0:
         mrkt_low_avg = float(mrkt_low_sum)/mrkt_num
         mrkt_high_avg = float(mrkt_high_sum)/mrkt_num
         low_l.append(mrkt_low_avg)
         high_l.append(mrkt_high_avg)

# Remove 5% of maximal values
low_l.sort()
high_l.sort()

num_low_to_rmv = int(0.1 * len(low_l))
num_high_to_rmv = int(0.1 * len(high_l))

for i in range(0,num_low_to_rmv):
   low_l.pop()
for i in range(0,num_high_to_rmv):
   high_l.pop()

num = 0
low_l_sum = 0
for e in low_l:
    num = num + 1
    low_l_sum = low_l_sum + e
print 'Low: ' + str(float(low_l_sum)/num)

num = 0
high_l_sum = 0
for e in high_l:
    num = num + 1
    high_l_sum = high_l_sum + e
print 'High: ' + str(float(high_l_sum)/num)

fig = plt.figure()
ax = fig.add_subplot(111)
n,bins,patches = ax.hist(low_l,50)
plt.show()


