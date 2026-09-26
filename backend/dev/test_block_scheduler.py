import block_scheduler as bs

result = bs.find_station_specific_gaps('TMS-042', 'hwh_bwn_main', 60, 'monday')
print('Fault:', result['fault_id'], 'at', result['fault_location'])
print('Trains in section:', result['train_count_in_section'])
print('Total gaps:', len(result['all_gaps']))
print('Feasible gaps:', len(result['feasible_gaps']))
if result['feasible_gaps']:
    g = result['feasible_gaps'][0]
    print('Best gap:', g['gap_start'], '->', g['gap_end'], 'Headroom:', g['headroom_min'], 'min')

week = bs.find_free_windows_all_days('hwh_bwn_main', 90)
print('\nGeneric week view for hwh_bwn_main (90min block):')
for day, d in week['week'].items():
    feasible = len(d['feasible_gaps'])
    cnt = d['active_train_count']
    print(f'  {day}: {cnt} trains | {feasible} feasible gaps')

impact = bs.score_window_impact('hwh_bwn_main', 'monday', 120, 210)
print('\nImpact 02:00-03:30 hwh_bwn_main monday:')
print('  Affected:', impact['affected_train_count'])
print('  Penalty:', impact['total_penalty_score'])
print('  High prio:', impact['high_priority_affected'])
