import numpy as np
from bokeh.plotting import figure, show, output_file, output_notebook
from bokeh.models import HoverTool
from bokeh.resources import CDN
from bokeh.embed import file_html


def heatmap(xnames, ynames, counts, percs, maxcount, clr, title, maintitle):
    xname,yname,color,alpha = [],[],[],[]
    for i,orgn in enumerate(xnames):
        for j,dstn in enumerate(ynames):
            xname.append(orgn)
            yname.append(dstn)
            color.append(clr)
            alpha.append(min(np.log(counts[i,j] + 1)/(abs(maxcount) + 1), 0.9) + 0.1)
        
    data = dict(xname = xname, 
                yname = yname,
                colors = color,
                alphas = alpha,
                count = counts.flatten(),
                perc = percs.flatten(),)

    p = figure(title=title,
               y_axis_location = "right",
               tools="hover,save",
               x_range=list(reversed(xnames)), y_range=ynames)

    p.plot_width = 800
    p.plot_height = 600
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "5pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = np.pi/3

    p.rect('xname', 'yname', 0.9, 0.9, source=data,
           alpha='alphas', line_color=None,
           color='colors',
           hover_line_color='black', hover_color='colors')
    p.select_one(HoverTool).tooltips = [('OD:', '@xname-@yname'),('cancelled', '@count (@perc %)'),]
    p.axis.major_label_text_font_size = "9pt"

    html = file_html(p, CDN, maintitle)
    return html


def heatmapfg(xnames, ynames, ds, bkgs, lpcds, ms, fs, ubs, maxcount, title):
    '''
    Heatmap for future groups.
    '''
    xname,yname,color,alpha = [],[],[],[]
    for i,orgn in enumerate(xnames):
        for j,dstn in enumerate(ynames):
            xname.append(orgn)
            yname.append(dstn)
            if ms[i,j] > 0:
                color.append('green')
            elif ms[i,j] < 0:
                color.append('red')
            else:
                color.append('white')
            alpha.append(min(np.log(abs(ds[i,j]) + 1)/(abs(maxcount) + 1), 0.9) + 0.1)
        
    data = dict(xname = xname, 
                yname = yname,
                colors = color,
                alphas = alpha,
                d = ds.flatten(),
                bkg = bkgs.flatten(),
                lpcd = lpcds.flatten(),
                m = ms.flatten(),
                f = fs.flatten(),
                ub = ubs.flatten(),)

    p = figure(title = title,
               y_axis_location = "right",
               tools = "hover,save",
               x_range = list(reversed(xnames)), y_range=ynames)

    p.plot_width = 800
    p.plot_height = 600
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "7pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = np.pi/3

    p.rect('xname', 'yname', 0.9, 0.9, source=data,
           alpha='alphas', line_color=None,
           color='colors',
           hover_line_color='black', hover_color='colors')
    p.select_one(HoverTool).tooltips = [('OD:', '@xname-@yname'),\
                                        ('rem dmd', '@d'),\
                                        ('cur bkg','@bkg'),\
                                        ('coming dmd', '@lpcd'),\
                                        ('mrgnl rev', '@m'),\
                                        ('yield', '@f'),\
                                        ('upper bound', '@ub')]
    p.axis.major_label_text_font_size = "7pt"

    html = file_html(p, CDN, title)
    return html


