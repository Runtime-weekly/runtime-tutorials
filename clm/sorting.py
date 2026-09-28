"""Small deterministic sorting environment. Models receive observations, never truth labels."""
import copy

CRITERIA = {
    'red': 'Put this item into the red bin.',
    'green': 'Put this item into the green bin.',
    'blue': 'Put this item into the blue bin.',
    'reject': 'Send this damaged item to the reject tray.',
    'inspect': 'Inspect this item to reveal its uncertain color.',
    'hold': 'Hold this item because its matching bin is full.',
}
RULES = ('Choose the next action for the current item. First reject damaged items, regardless of color. '
         'For an undamaged item, inspect if its observed color is unknown. Otherwise use the bin matching '
         'its color if that bin has a free slot. If the matching bin is full, hold the item. '
         'Never substitute another color bin. Inspection reveals color and keeps the item for another action.')
SCENARIOS = [
    {'id':'01','title':'A clean red item','color':'red','observed':'red','damaged':False,'bins':{'red':0,'green':0,'blue':0}},
    {'id':'02','title':'Damage takes priority','color':'green','observed':'green','damaged':True,'bins':{'red':0,'green':0,'blue':0}},
    {'id':'03','title':'Look again, then sort','color':'blue','observed':'unknown','damaged':False,'bins':{'red':0,'green':0,'blue':0}},
    {'id':'04','title':'The matching bin is full','color':'red','observed':'red','damaged':False,'bins':{'red':2,'green':0,'blue':0}},
    {'id':'05','title':'A different bin is full','color':'green','observed':'green','damaged':False,'bins':{'red':2,'green':0,'blue':0}},
    {'id':'06','title':'Unknown color, visible damage','color':'blue','observed':'unknown','damaged':True,'bins':{'red':0,'green':0,'blue':0}},
]

def initial(scenario):
    return {'observed_color':scenario['observed'],'damaged':scenario['damaged'],
            'bins':copy.deepcopy(scenario['bins']),'capacity_per_bin':2,'terminal':False,'disposition':None}

def observe(state):
    return {k:copy.deepcopy(state[k]) for k in ('observed_color','damaged','bins','capacity_per_bin')}

def expected(state):
    if state['damaged']:return 'reject'
    color=state['observed_color']
    if color=='unknown':return 'inspect'
    return 'hold' if state['bins'][color]>=state['capacity_per_bin'] else color

def execute(state, action, truth):
    state=copy.deepcopy(state)
    if action not in CRITERIA:raise ValueError('Unknown action; no execution')
    if state['terminal']:raise ValueError('Cannot execute after terminal disposition')
    if action=='inspect':
        state['observed_color']=truth['color']
        return state,'inspection revealed '+truth['color']
    state['terminal']=True
    state['disposition']=action
    if action in ('red','green','blue'):
        if state['bins'][action]>=state['capacity_per_bin']:
            state['disposition']='blocked';return state,'blocked: selected bin is full'
        state['bins'][action]+=1
        return state,'placed in '+action+' bin'
    return state,'sent to reject tray' if action=='reject' else 'placed on hold'

def checks():
    for s in SCENARIOS:
        state=initial(s)
        for _ in range(2):
            state,_=execute(state,expected(state),s)
            if state['terminal']:break
        assert state['terminal'],s['id']
    s=SCENARIOS[2];state=initial(s)
    assert expected(state)=='inspect' and observe(state)['observed_color']=='unknown'
    state,_=execute(state,'inspect',s)
    assert not state['terminal'] and expected(state)=='blue'
    state,_=execute(state,'blue',s)
    assert state['terminal'] and state['bins']['blue']==1
    state,event=execute(initial(SCENARIOS[3]),'red',SCENARIOS[3])
    assert state['bins']['red']==2 and state['disposition']=='blocked'
    assert expected(initial(SCENARIOS[5]))=='reject'
    print('simulation checks passed')

if __name__=='__main__':checks()
