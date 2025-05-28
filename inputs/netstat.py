import time
import socket
import os
from core.metric import Metric
from utils.metrics import calculate_rate, create_key
from utils.debug import debug_log

def collect(config=None):
    """Collect TCP connection state metrics and TCP statistics."""
    timestamp = int(time.time() * 1000)
    hostname = socket.gethostname()
    metrics = []
    
    # TCP connection states
    tcp_states = {
        '01': 'established',
        '02': 'syn_sent',
        '03': 'syn_recv',
        '04': 'fin_wait1',
        '05': 'fin_wait2',
        '06': 'time_wait',
        '07': 'close',
        '08': 'close_wait',
        '09': 'last_ack',
        '0A': 'listen',
        '0B': 'closing'
    }
    
    # Initialize counters for each state
    state_counts = {state: 0 for state in tcp_states.values()}
    
    # Read IPv4 TCP connections
    try:
        with open('/proc/net/tcp', 'r') as f:
            # Skip header line
            next(f)
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4:
                    state = parts[3].lower()
                    if state in tcp_states:
                        state_name = tcp_states[state]
                        state_counts[state_name] += 1
    except Exception as e:
        print(f"[netstat] Error reading IPv4 TCP stats: {e}")
    
    # Read IPv6 TCP connections
    try:
        if os.path.exists('/proc/net/tcp6'):
            with open('/proc/net/tcp6', 'r') as f:
                # Skip header line
                next(f)
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        state = parts[3].lower()
                        if state in tcp_states:
                            state_name = tcp_states[state]
                            state_counts[state_name] += 1
    except Exception as e:
        print(f"[netstat] Error reading IPv6 TCP stats: {e}")
    
    # Create metrics for each state
    labels = {"host": hostname}
    for state, count in state_counts.items():
        metrics.append(Metric(
            name=f"tcp_{state}",
            value=count,
            timestamp=timestamp,
            labels=labels
        ))
    
    # Collect TCP handshake metrics from /proc/net/netstat
    try:
        
        tcp_ext_metrics = {}
        with open('/proc/net/netstat', 'r') as f:
            lines = f.readlines()
            for i in range(0, len(lines), 2):
                if i+1 < len(lines):
                    header = lines[i].strip().split()
                    values = lines[i+1].strip().split()
                    
                    if header[0] == 'TcpExt:':
                        for j in range(1, len(header)):
                            if j < len(values):
                                tcp_ext_metrics[header[j]] = int(values[j])
        
        # Map specific metrics we're interested in
        tcp_handshake_metrics = {
            'SyncookiesSent': 'syncookies_sent',
            'SyncookiesRecv': 'syncookies_recv',
            'SyncookiesFailed': 'syncookies_failed',
            'EmbryonicRsts': 'embryonic_rsts',
            'PruneCalled': 'prune_called',
            'RcvPruned': 'rcv_pruned',
            'OfoPruned': 'ofo_pruned',
            'OutOfWindowIcmps': 'out_of_window_icmps',
            'LockDroppedIcmps': 'lock_dropped_icmps',
            'ArpFilter': 'arp_filter',
            'TW': 'time_wait_sockets',
            'TWRecycled': 'time_wait_recycled',
            'TWKilled': 'time_wait_killed',
            'PAWSPassive': 'paws_passive',
            'PAWSActive': 'paws_active',
            'PAWSEstab': 'paws_established',
            'DelayedACKs': 'delayed_acks',
            'DelayedACKLocked': 'delayed_ack_locked',
            'DelayedACKLost': 'delayed_ack_lost',
            'ListenOverflows': 'listen_overflows',
            'ListenDrops': 'listen_drops',
            'TCPPrequeued': 'tcp_prequeued',
            'TCPDirectCopyFromBacklog': 'tcp_direct_copy_from_backlog',
            'TCPDirectCopyFromPrequeue': 'tcp_direct_copy_from_prequeue',
            'TCPPrequeueDropped': 'tcp_prequeue_dropped',
            'TCPHPHits': 'tcp_hp_hits',
            'TCPHPHitsToUser': 'tcp_hp_hits_to_user',
            'TCPPureAcks': 'tcp_pure_acks',
            'TCPHPAcks': 'tcp_hp_acks',
            'TCPRenoRecovery': 'tcp_reno_recovery',
            'TCPSackRecovery': 'tcp_sack_recovery',
            'TCPSACKReneging': 'tcp_sack_reneging',
            'TCPFACKReorder': 'tcp_fack_reorder',
            'TCPSACKReorder': 'tcp_sack_reorder',
            'TCPRenoReorder': 'tcp_reno_reorder',
            'TCPTSReorder': 'tcp_ts_reorder',
            'TCPFullUndo': 'tcp_full_undo',
            'TCPPartialUndo': 'tcp_partial_undo',
            'TCPDSACKUndo': 'tcp_dsack_undo',
            'TCPLossUndo': 'tcp_loss_undo',
            'TCPLostRetransmit': 'tcp_lost_retransmit',
            'TCPRenoFailures': 'tcp_reno_failures',
            'TCPSackFailures': 'tcp_sack_failures',
            'TCPLossFailures': 'tcp_loss_failures',
            'TCPFastRetrans': 'tcp_fast_retrans',
            'TCPSlowStartRetrans': 'tcp_slow_start_retrans',
            'TCPTimeouts': 'tcp_timeouts',
            'TCPLossProbes': 'tcp_loss_probes',
            'TCPLossProbeRecovery': 'tcp_loss_probe_recovery',
            'TCPRenoRecoveryFail': 'tcp_reno_recovery_fail',
            'TCPSackRecoveryFail': 'tcp_sack_recovery_fail',
            'TCPRcvCollapsed': 'tcp_rcv_collapsed',
            'TCPBacklogCoalesce': 'tcp_backlog_coalesce',
            'TCPDSACKOldSent': 'tcp_dsack_old_sent',
            'TCPDSACKOfoSent': 'tcp_dsack_ofo_sent',
            'TCPDSACKRecv': 'tcp_dsack_recv',
            'TCPDSACKOfoRecv': 'tcp_dsack_ofo_recv',
            'TCPAbortOnData': 'tcp_abort_on_data',
            'TCPAbortOnClose': 'tcp_abort_on_close',
            'TCPAbortOnMemory': 'tcp_abort_on_memory',
            'TCPAbortOnTimeout': 'tcp_abort_on_timeout',
            'TCPAbortOnLinger': 'tcp_abort_on_linger',
            'TCPAbortFailed': 'tcp_abort_failed',
            'TCPMemoryPressures': 'tcp_memory_pressures',
            'TCPMemoryPressuresChrono': 'tcp_memory_pressures_chrono',
            'TCPSACKDiscard': 'tcp_sack_discard',
            'TCPDSACKIgnoredOld': 'tcp_dsack_ignored_old',
            'TCPDSACKIgnoredNoUndo': 'tcp_dsack_ignored_no_undo',
            'TCPSpuriousRTOs': 'tcp_spurious_rtos',
            'TCPMD5NotFound': 'tcp_md5_not_found',
            'TCPMD5Unexpected': 'tcp_md5_unexpected',
            'TCPMD5Failure': 'tcp_md5_failure',
            'TCPSackShifted': 'tcp_sack_shifted',
            'TCPSackMerged': 'tcp_sack_merged',
            'TCPSackShiftFallback': 'tcp_sack_shift_fallback',
            'TCPBacklogDrop': 'tcp_backlog_drop',
            'PFMemallocDrop': 'pf_memalloc_drop',
            'TCPMinTTLDrop': 'tcp_min_ttl_drop',
            'TCPDeferAcceptDrop': 'tcp_defer_accept_drop',
            'IPReversePathFilter': 'ip_reverse_path_filter',
            'TCPTimeWaitOverflow': 'tcp_time_wait_overflow',
            'TCPReqQFullDoCookies': 'tcp_req_q_full_do_cookies',
            'TCPReqQFullDrop': 'tcp_req_q_full_drop',
            'TCPRetransFail': 'tcp_retrans_fail',
            'TCPRcvCoalesce': 'tcp_rcv_coalesce',
            'TCPOFOQueue': 'tcp_ofo_queue',
            'TCPOFODrop': 'tcp_ofo_drop',
            'TCPOFOMerge': 'tcp_ofo_merge',
            'TCPChallengeACK': 'tcp_challenge_ack',
            'TCPSYNChallenge': 'tcp_syn_challenge',
            'TCPFastOpenActive': 'tcp_fast_open_active',
            'TCPFastOpenActiveFail': 'tcp_fast_open_active_fail',
            'TCPFastOpenPassive': 'tcp_fast_open_passive',
            'TCPFastOpenPassiveFail': 'tcp_fast_open_passive_fail',
            'TCPFastOpenListenOverflow': 'tcp_fast_open_listen_overflow',
            'TCPFastOpenCookieReqd': 'tcp_fast_open_cookie_reqd',
            'TCPFastOpenBlackhole': 'tcp_fast_open_blackhole',
            'TCPSpuriousRtxHostQueues': 'tcp_spurious_rtx_host_queues',
            'BusyPollRxPackets': 'busy_poll_rx_packets',
            'TCPAutoCorking': 'tcp_auto_corking',
            'TCPFromZeroWindowAdv': 'tcp_from_zero_window_adv',
            'TCPToZeroWindowAdv': 'tcp_to_zero_window_adv',
            'TCPWantZeroWindowAdv': 'tcp_want_zero_window_adv',
            'TCPSynRetrans': 'tcp_syn_retrans',
            'TCPOrigDataSent': 'tcp_orig_data_sent',
            'TCPHystartTrainDetect': 'tcp_hystart_train_detect',
            'TCPHystartTrainCwnd': 'tcp_hystart_train_cwnd',
            'TCPHystartDelayDetect': 'tcp_hystart_delay_detect',
            'TCPHystartDelayCwnd': 'tcp_hystart_delay_cwnd',
            'TCPACKSkippedSynRecv': 'tcp_ack_skipped_syn_recv',
            'TCPACKSkippedPAWS': 'tcp_ack_skipped_paws',
            'TCPACKSkippedSeq': 'tcp_ack_skipped_seq',
            'TCPACKSkippedFinWait2': 'tcp_ack_skipped_fin_wait2',
            'TCPACKSkippedTimeWait': 'tcp_ack_skipped_time_wait',
            'TCPACKSkippedChallenge': 'tcp_ack_skipped_challenge',
            'TCPWinProbe': 'tcp_win_probe',
            'TCPKeepAlive': 'tcp_keep_alive',
            'TCPMTUPFail': 'tcp_mtup_fail',
            'TCPMTUPSuccess': 'tcp_mtup_success',
            'TCPDelivered': 'tcp_delivered',
            'TCPDeliveredCE': 'tcp_delivered_ce',
            'TCPAckCompressed': 'tcp_ack_compressed',
            'TCPZeroWindowDrop': 'tcp_zero_window_drop',
            'TCPRcvQDrop': 'tcp_rcv_q_drop',
            'TCPWqueueTooBig': 'tcp_wqueue_too_big'
        }
        
        # Process each metric
        for key, metric_name in tcp_handshake_metrics.items():
            if key in tcp_ext_metrics:
                # Add raw counter metric
                raw_value = tcp_ext_metrics[key]
                metrics.append(Metric(
                    name=f"tcp_{metric_name}",
                    value=raw_value,
                    timestamp=timestamp,
                    labels=labels
                ))
                
                # Calculate rate using utility function
                metric_key = create_key(f"tcp_{metric_name}", labels)
                rate = calculate_rate(metric_key, raw_value, timestamp)
                
                if rate is not None:
                    metrics.append(Metric(
                        name=f"tcp_{metric_name}_rate",
                        value=rate,
                        timestamp=timestamp,
                        labels=labels
                    ))
    except Exception as e:
        print(f"[netstat] Error reading TCP handshake metrics: {e}")
    
    # Collect TCP stats from /proc/net/snmp
    try:
        
        tcp_stats = {}
        with open('/proc/net/snmp', 'r') as f:
            lines = f.readlines()
            for i in range(0, len(lines), 2):
                if i+1 < len(lines):
                    header = lines[i].strip().split()
                    values = lines[i+1].strip().split()
                    
                    if header[0] == 'Tcp:':
                        for j in range(1, len(header)):
                            if j < len(values):
                                tcp_stats[header[j]] = int(values[j])
        
        # Map specific metrics we're interested in
        tcp_metrics = {
            'ActiveOpens': 'active_opens',
            'PassiveOpens': 'passive_opens',
            'AttemptFails': 'attempt_fails',
            'EstabResets': 'estab_resets',
            'CurrEstab': 'curr_estab',
            'InSegs': 'in_segs',
            'OutSegs': 'out_segs',
            'RetransSegs': 'retrans_segs',
            'InErrs': 'in_errs',
            'OutRsts': 'out_rsts',
            'InCsumErrors': 'in_csum_errors'
        }
        
        # Process each metric
        for key, metric_name in tcp_metrics.items():
            if key in tcp_stats:
                # Add raw counter metric
                raw_value = tcp_stats[key]
                metrics.append(Metric(
                    name=f"tcp_{metric_name}",
                    value=raw_value,
                    timestamp=timestamp,
                    labels=labels
                ))
                
                # Skip rate calculation for non-counter metrics
                if key == 'CurrEstab':
                    continue
                
                # Calculate rate using utility function
                metric_key = create_key(f"tcp_{metric_name}", labels)
                rate = calculate_rate(metric_key, raw_value, timestamp)
                
                if rate is not None:
                    metrics.append(Metric(
                        name=f"tcp_{metric_name}_rate",
                        value=rate,
                        timestamp=timestamp,
                        labels=labels
                    ))
    except Exception as e:
        print(f"[netstat] Error reading TCP stats: {e}")
    
    # Debug logging removed for brevity
    return metrics