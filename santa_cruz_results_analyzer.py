import matplotlib.pyplot as plt
import numpy as np
cycle_colors = (list(plt.rcParams['axes.prop_cycle'].by_key()['color'])+ ["red", "indigo",'blue','gold','magenta'])*4

def read_results(filename):
    with open(filename,'r') as f:
        text = f.read()
    results = text.split('--Select Contest or Back to Top--')[1].split('Terms Of Use')[0]
    line_results = results.split('\n')
    return line_results

def result_from_str(s,line_results):
    for i,line in enumerate(line_results):
        if line.startswith(s):
            return int(line.split(s)[1].split(' ')[0])
            
def turnout(line_results):
    total_in_person = result_from_str("Total In Person: ",line_results)
    total_vbm = result_from_str("Total Vote by Mail: ",line_results)
    total_votes = result_from_str("Total Votes: ",line_results)
    total_registered = result_from_str("Total Registered Voters: ",line_results)
    return [('Total In Person',total_in_person),\
            ('Total Vote by Mail',total_vbm),\
            ('Total Votes',total_votes),\
            ('Total Registered Voters',total_registered)]
    
def register_election_ids(line_results,check_lines = 0,print_lines = False):
    to_return = []
    for i,line in enumerate(line_results):
        if line == 'Candidate':
            to_return.append((i,line_results[i+3:i+3+check_lines]))
            if print_lines:
                print(i,line_results[i+3:i+3+check_lines])
    return to_return

def check_results_match(id_results1,id_results2):
    assert len(id_results1) == len(id_results2)
    for i in range(len(id_results1)):
        assert id_results1[i][0] == id_results2[i][0]
        for j in range(len(id_results1[i][1])):
            if '(' in id_results1[i][1][j]:
                continue
            try:
                int(id_results1[i][1][j])
                continue
            except:
                pass
            try:
                assert id_results1[i][1][j] == id_results2[i][1][j]
            except:
                print(f'{id_results1[i]} and {id_results2[i]} were not compatible!')
                assert False
    print('clear!')

def election_results(lines,election_name,election_ids):
    i = election_ids[election_name]+1
    string = lines[i]
    ignore_text = ['Party', 'Total', 'REP', 'DEM', 
                   'Total', 'Write In Candidate', 'Write In', 'Total']
    name = None
    names = []
    results = []
    while string != 'Candidate':
        if string not in ignore_text:
            if name == None:
                name = string
            else:
                votes = int(string.split(' ')[0])
                names.append(name)
                results.append(votes)
                name = None
        i+=1
        string = lines[i]
    return names,results

def election_results_tracker(filenames,election_name,election_ids):
    names = None
    dates = []
    for j,fname in enumerate(filenames):
        date = int(fname.split('.txt')[0].split('_')[-1])
        dates.append(date)
        lines = read_results(fname)
        ret_names,ret_results = election_results(lines,election_name,election_ids)
        if names is None:
            names = ret_names
            results = np.zeros((len(names),len(filenames)),dtype = int)
        else:
            for i in range(len(names)):
                assert names[i]==ret_names[i]
        for i,count in enumerate(ret_results):
            results[i,j] = count
    return names,results,np.array(dates)

def values_to_plot(names,results,keep):
    ignore = ['Total Votes:', 'Undervotes', 'Overvotes', 'WRITE-IN']
    final_results_so_far = np.copy(results[:,-1])
    for v in ignore:
        try:
            ignore_id = names.index(v)
            final_results_so_far[ignore_id] = -1
        except:
            pass
    to_keep = []
    if isinstance(keep,int):
        for i in range(keep):
            highest_id = np.argmax(final_results_so_far)
            if np.amax(final_results_so_far)==-1:
                break
            elif names[highest_id] in ignore:
                final_results_so_far[highest_id] = -1
                i-=1
                continue
            to_keep.append(names[highest_id])
            final_results_so_far[highest_id] = -1
    return to_keep

def reorder_results(names,ordered_names,ys):
    reordered_results = np.zeros((len(ordered_names),len(ys[0])))
    for i,name in enumerate(ordered_names):
        name_id = names.index(name)
        reordered_results[i] = ys[name_id]
    return reordered_results

def get_totals(names,results):
    tot_id = names.index('Total Votes:')
    under_id = names.index('Undervotes')
    over_id = names.index('Overvotes')
    return results[tot_id]-results[under_id]-results[over_id]

def get_color(name,election_name,color_dict):
    name_and_election = (name,election_name)
    comrades = color_dict['comrades']
    friends = color_dict['friends']
    enemies = color_dict['enemies']
    if name_and_election in comrades:
        return 'red'
    if name_and_election in friends:
        return 'blue'
    if name_and_election in enemies:
        return 'black'
    return None

def plot_results(election_name,names,results,dates,
                 percentages = False,diffs = False,
                 use_dates = False,fmt = '-',keep = 2,
                 ylims = 'default',ax = None,color_dict = None):
    if ax is None:
        _,ax = plt.subplots(1)
    if use_dates:
        xs = dates
        xlabel = 'date'
    else:
        xs = np.arange(len(dates))+1
        xlabel = 'update number'
    ys=np.copy(results)
    totals = get_totals(names,results)
    if not percentages and not diffs:
        pass
    elif percentages and not diffs:
        ys=ys/totals*100
    elif not percentages and diffs:
        ys = np.diff(np.append(np.zeros((len(names),1)),ys,axis = 1))
    elif percentages and diffs:
        diff_results = np.diff(np.append(np.zeros((len(names),1)),ys,axis = 1))
        diff_tots = np.diff(np.append(np.zeros(1),totals))
        ys=diff_results/diff_tots*100
    ordered_names = values_to_plot(names,results,keep)
    ordered_results = reorder_results(names,ordered_names,ys)
    ordered_totals = reorder_results(names,ordered_names,results)
    for i,name in enumerate(ordered_names):
        color = get_color(name,election_name,color_dict)
        if color is None:
            color = cycle_colors[i]
        ax.plot(xs,ordered_results[i],fmt,label = name,color = color)
    if percentages:
        ax.legend(loc = 'upper right')
    else:
        ax.legend(loc = 'upper left')
    ax.set_xlabel(xlabel)
    if not percentages and not diffs:
        ax.set_ylabel('total votes')
    elif not percentages and diffs:
        ax.set_ylabel('new votes')
    elif percentages and diffs:
        ax.set_ylabel('votes (percent of new)')
    elif percentages and not diffs:
        ax.set_ylabel('votes (percent of tot)')
    highest_point = np.amax(ordered_results[0])
    if ylims == 'default' and percentages:
        ax.set_ylim(0,100)
    elif ylims == 'default' and not percentages:            
        ax.set_ylim(0,highest_point*1.5)
    gap = ordered_results[0][-1]-ordered_results[1][-1]    
    if not percentages and not diffs:
        ax.text(xs[0]+(xs[-1]-xs[0])*.1, highest_point*1.1,f'gap = {gap:.0f} votes')
    elif not percentages and diffs:
        if ordered_totals[0,-2]<ordered_totals[1,-2]:
            ax.text(xs[0]+(xs[-1]-xs[0])*.1, highest_point*1.1,f'Flipped! With {gap:.0f} net new votes')
        elif gap>=0:
            ax.text(xs[0]+(xs[-1]-xs[0])*.1, highest_point*1.1,f'gap widens by {gap:.0f} votes')
        elif gap<0:
            ax.text(xs[0]+(xs[-1]-xs[0])*.1, highest_point*1.1,f'gap shrinks by {-gap:.0f} votes')
    elif percentages and not diffs:
        ax.text(xs[0]+(xs[-1]-xs[0])*.1, 80,f'gap = {gap:.2f} percent')
    elif percentages and diffs:
        if gap>=0:
            ax.text(xs[0]+(xs[-1]-xs[0])*.1, 70,f'latest returns have\n {ordered_names[0]} \n ahead by {gap:.2f} percent')
        if gap<0:
            ax.text(xs[0]+(xs[-1]-xs[0])*.1, 70,f'latest returns have\n {ordered_names[1]} \n ahead by {-gap:.2f} percent')
    if percentages:
        ax.plot(xs,xs*0.0+50,'--',label = name,color = 'grey')
    ax.set_title(f'returns for election {election_name}')