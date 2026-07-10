import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# --- CONFIGURATION ---
START_DATE = datetime(2026, 5, 1, 0, 0, 0)
DAYS_TO_GENERATE = 20
HUBS = ['WAW15', 'KRK07', 'WRO05', 'POZ02', 'GDA03', 'KTW11', 'LUB04', 'SZC08']
EMPLOYEES = [f"EMP-{i:05d}" for i in range(1, 31)]

ERROR_MAP = {
    'Scanner': ['LOW_CONTRAST_LABEL', 'QR_CODE_DAMAGED', 'BLURRY_IMAGE', 'WRONG_HUB_ROUTING'],
    'Dimensioner': ['CALIBRATION_LOSS', 'OBJECT_OUT_OF_BOUNDS', 'SENSOR_BLOCK'],
    'Sorter': ['MECHANICAL_JAM', 'TRAY_MALFUNCTION', 'DIVERTER_ERROR'],
    'Telescopic Conveyor': ['BELT_STOP', 'OVERLOAD_TRIGGER']
}


PROCESS_TIME_RANGES = {
    'PRIORITY': {
        'inbound_minutes': (3, 12),
        'dimensioning_seconds': (10, 60),
        'destination_minutes': (1, 6),
        'sorting_seconds': (5, 40),
        'dock_minutes': (3, 18),
        'loaded_minutes': (5, 35)
    },
    'COURIER_STD': {
        'inbound_minutes': (5, 18),
        'dimensioning_seconds': (15, 90),
        'destination_minutes': (2, 10),
        'sorting_seconds': (10, 60),
        'dock_minutes': (5, 30),
        'loaded_minutes': (10, 60)
    },
    'LOCKER_24H': {
        'inbound_minutes': (8, 25),
        'dimensioning_seconds': (20, 120),
        'destination_minutes': (4, 15),
        'sorting_seconds': (15, 90),
        'dock_minutes': (10, 45),
        'loaded_minutes': (20, 90)
    }
}

# --- GLOBAL TRACKERS (Ensure uniqueness across all 20 days) ---
generated_parcel_ids = set()

global_counters = {
    'DLV': 1, 'LOD': 1, 'ST': 1, 'SCN': 1, 'EXC': 1, 'SRT': 1, 'EMP': 1
}

def get_unique_parcel_id():
    while True:
        p_id = str(random.randint(10**23, 10**24 - 1))
        if p_id not in generated_parcel_ids:
            generated_parcel_ids.add(p_id)
            return p_id

def get_next_id(prefix):
    val = global_counters[prefix]
    global_counters[prefix] += 1
    return f"{prefix}-{val:07d}" # Increased to 7 digits for larger scale


def get_service_type(service_weights):
    return random.choices(
        ['LOCKER_24H', 'COURIER_STD', 'PRIORITY'],
        weights=[
            service_weights['LOCKER_24H'],
            service_weights['COURIER_STD'],
            service_weights['PRIORITY']
        ],
        k=1
    )[0]

def get_timing_range(service_type, timing_name):
    return PROCESS_TIME_RANGES[service_type][timing_name]

def generate_multi_day_data():
    print(f"🚀 Starting 20-day generation (from {START_DATE.strftime('%Y-%m-%d')})...")
    print("⏳ Devices table generating (One-time setup)...")

    # --- 1. DEVICES (Persist across all 20 days) ---
    device_types = ['Scanner', 'Sorter', 'Dimensioner', 'Telescopic Conveyor']
    devices = [{
        'device_id': f"DEV-{i:05d}",
        'type': random.choice(device_types),
        'zone': random.choice(['Inbound', 'Sort_Area', 'Outbound']),
        'status': random.choice(['ACTIVE', 'ACTIVE', 'MAINTENANCE'])
    } for i in range(1, 80)]
    
    df_devices = pd.DataFrame(devices)
    df_devices.to_csv('devices_master.csv', index=False)
    print("✅ Saved devices_master.csv")
    
    scanners = [d for d in devices if d['type'] in ['Scanner', 'Dimensioner']]
    inbound_scanners = [d for d in scanners if d['zone'] == 'Inbound'] or scanners
    sort_scanners = [d for d in scanners if d['zone'] == 'Sort_Area'] or scanners
    outbound_scanners = [d for d in scanners if d['zone'] == 'Outbound'] or scanners
    sorters = [d for d in devices if d['type'] == 'Sorter'] or [{'device_id': 'DEV-99999', 'type': 'Sorter'}]

    # --- MAIN DAY LOOP ---
    for day_offset in range(DAYS_TO_GENERATE):
        current_date = START_DATE + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Determine daily volume
        num_parcels_today = 100_000 if day_offset == 0 else random.randint(85000, 115000)
        priority_share = random.uniform(0.20, 0.28)
        courier_share = random.uniform(0.30, 0.38)
        service_weights = {
            'PRIORITY': priority_share,
            'COURIER_STD': courier_share,
            'LOCKER_24H': 1 - priority_share - courier_share
        }
        print(f"\n⚙️ Generating Day {day_offset + 1}/20 ({date_str}) - Target: {num_parcels_today} parcels...")

        # Daily Data Containers
        intakes, loading_docks = [], []
        parcels, status_history, scans, exceptions, sorting = [], [], [], [], []
        deliveries_cache = []
        parcels_created = 0

        # --- 2. INTAKE (DYNAMIC TRUCKS) ---
        while parcels_created < num_parcels_today:
            count = random.randint(2100, 4932) # Linehaul trucks
            if parcels_created + count > num_parcels_today:
                count = num_parcels_today - parcels_created
                
            arrival = current_date + timedelta(minutes=random.randint(0, 720))
            source_hub = random.choice(HUBS)
            delivery_id = get_next_id('DLV')
            
            intakes.append({
                'delivery_id': delivery_id,
                'dock_id': f"IN-DOCK-{random.randint(1, 15)}",
                'arrival_time': arrival,
                'unload_start': arrival + timedelta(minutes=random.randint(5, 15)),
                'unload_end': arrival + timedelta(minutes=random.randint(60, 180)),
                'parcel_count': count,
                'truck_plate': f"WA{random.randint(10000, 99999)}",
                'source_hub_id': source_hub
            })
            deliveries_cache.append({'id': delivery_id, 'count': count, 'start': arrival, 'source': source_hub})
            parcels_created += count

        # --- SETUP LOADING DOCKS (OUTBOUND ROUTES) ---
        for i in range(80):
            loading_docks.append({
                'loading_id': get_next_id('LOD'),
                'route_id': random.choice(HUBS),
                'start_time': current_date + timedelta(hours=random.randint(13, 20)),
                'dock_id': f"OUT-DOCK-{random.randint(1, 20)}",
                'parcel_count': 0
            })

        # --- 3. MAIN LOGIC LOOP (Traceability) ---
        for dlv in deliveries_cache:
            for _ in range(dlv['count']):
                p_id = get_unique_parcel_id()
                dest_route = random.choice(loading_docks)
                received_time = dlv['start'] + timedelta(minutes=random.randint(15, 120))
                service_type = get_service_type(service_weights)
                
                parcel = {
                    'parcel_id': p_id,
                    'status': 'RECEIVED',
                    'weight_kg': round(random.uniform(0.2, 25.0), 2),
                    'length_cm': round(random.uniform(10, 60), 1),
                    'width_cm': round(random.uniform(10, 40), 1),
                    'height_cm': round(random.uniform(5, 40), 1),
                    'service_type': service_type,
                    'received_at': received_time,
                    'source_hub_id': dlv['source'],
                    'delivery_id': dlv['id'],
                    'destination_hub_id': dest_route['route_id'],
                    'loading_id': dest_route['loading_id']
                }
                
                status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'RECEIVED', 'change_timestamp': received_time})
                
                # --- SCAN 1: INBOUND ---
                inbound_time = received_time + timedelta(minutes=random.randint(*get_timing_range(service_type, 'inbound_minutes')))
                scanner = random.choice(inbound_scanners)
                is_fail = random.random() < 0.03
                
                scans.append({
                    'scan_id': get_next_id('SCN'), 'parcel_id': p_id, 'device_id': scanner['device_id'],
                    'scan_type': 'INBOUND', 'result': 'FAIL' if is_fail else 'OK', 'scan_timestamp': inbound_time,
                    'dynamic_weight': round(parcel['weight_kg'] + random.uniform(-0.1, 0.2), 2)
                })
                
                if is_fail:
                    exc_status = 'RESOLVED'
                    res_time = inbound_time + timedelta(minutes=random.randint(15, 240))
                    exceptions.append({
                        'exception_id': get_next_id('EXC'), 'parcel_id': p_id, 'device_id': scanner['device_id'], 
                        'error_code': random.choice(ERROR_MAP['Scanner']), 'status': exc_status, 
                        'reported_at': inbound_time, 'resolved_at': res_time, 'employee_id': random.choice(EMPLOYEES)
                    })
                    parcel['status'] = 'EXCEPTION'
                    status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'EXCEPTION', 'change_timestamp': inbound_time})
                    parcels.append(parcel)
                    continue
                    
                latest_time = inbound_time

                # --- SCAN 2: DIMENSIONING ---
                if random.random() < 0.95:
                    dim_time = latest_time + timedelta(seconds=random.randint(*get_timing_range(service_type, 'dimensioning_seconds')))
                    dim_device = random.choice([d for d in inbound_scanners if d['type'] == 'Dimensioner'] or inbound_scanners)
                    is_fail = random.random() < 0.01
                    
                    scans.append({
                        'scan_id': get_next_id('SCN'), 'parcel_id': p_id, 'device_id': dim_device['device_id'],
                        'scan_type': 'DIMENSIONING', 'result': 'FAIL' if is_fail else 'OK', 'scan_timestamp': dim_time,
                        'dynamic_weight': round(parcel['weight_kg'] + random.uniform(-0.05, 0.05), 2)
                    })
                    
                    if is_fail:
                        exc_status = 'RESOLVED'
                        res_time = dim_time + timedelta(minutes=random.randint(15, 240))
                        exceptions.append({
                            'exception_id': get_next_id('EXC'), 'parcel_id': p_id, 'device_id': dim_device['device_id'], 
                            'error_code': random.choice(ERROR_MAP['Dimensioner']), 'status': exc_status, 
                            'reported_at': dim_time, 'resolved_at': res_time, 'employee_id': random.choice(EMPLOYEES)
                        })
                        parcel['status'] = 'EXCEPTION'
                        status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'EXCEPTION', 'change_timestamp': dim_time})
                        parcels.append(parcel)
                        continue
                    latest_time = dim_time

                # --- SCAN 3: DESTINATION ---
                dest_time = latest_time + timedelta(minutes=random.randint(*get_timing_range(service_type, 'destination_minutes')))
                dest_scanner = random.choice(sort_scanners)
                is_fail = random.random() < 0.015
                
                scans.append({
                    'scan_id': get_next_id('SCN'), 'parcel_id': p_id, 'device_id': dest_scanner['device_id'],
                    'scan_type': 'DESTINATION', 'result': 'FAIL' if is_fail else 'OK', 'scan_timestamp': dest_time,
                    'dynamic_weight': round(parcel['weight_kg'], 2)
                })

                if is_fail:
                    exc_status = 'RESOLVED'
                    res_time = dest_time + timedelta(minutes=random.randint(15, 240))
                    exceptions.append({
                        'exception_id': get_next_id('EXC'), 'parcel_id': p_id, 'device_id': dest_scanner['device_id'], 
                        'error_code': random.choice(ERROR_MAP['Scanner']), 'status': exc_status, 
                        'reported_at': dest_time, 'resolved_at': res_time, 'employee_id': random.choice(EMPLOYEES)
                    })
                    parcel['status'] = 'EXCEPTION'
                    status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'EXCEPTION', 'change_timestamp': dest_time})
                    parcels.append(parcel)
                    continue

                # --- SORTING EVENT ---
                sort_time = dest_time + timedelta(seconds=random.randint(*get_timing_range(service_type, 'sorting_seconds')))
                sorter = random.choice(sorters)
                is_sort_fail = random.random() < 0.02
                
                sorting.append({
                    'event_id': get_next_id('SRT'), 'parcel_id': p_id, 'sorter_id': sorter['device_id'],
                    'chute_id': f"CHUTE-{random.randint(1, 80)}", 'entry_time': sort_time, 'result': 'REROUTED' if is_sort_fail else 'SUCCESS'
                })
                
                if is_sort_fail:
                    exc_status = 'RESOLVED'
                    res_time = sort_time + timedelta(minutes=random.randint(15, 240))
                    exceptions.append({
                        'exception_id': get_next_id('EXC'), 'parcel_id': p_id, 'device_id': sorter['device_id'], 
                        'error_code': random.choice(ERROR_MAP['Sorter']), 'status': exc_status, 
                        'reported_at': sort_time, 'resolved_at': res_time, 'employee_id': random.choice(EMPLOYEES)
                    })
                    parcel['status'] = 'EXCEPTION'
                    status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'EXCEPTION', 'change_timestamp': sort_time})
                    parcels.append(parcel)
                    continue
                    
                parcel['status'] = 'SORTED'
                status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'SORTED', 'change_timestamp': sort_time})
                
                # --- SCAN 4: LOADING DOCK ---
                dock_time = sort_time + timedelta(minutes=random.randint(*get_timing_range(service_type, 'dock_minutes')))
                dock_scanner = random.choice(outbound_scanners)
                is_fail = random.random() < 0.01

                scans.append({
                    'scan_id': get_next_id('SCN'), 'parcel_id': p_id, 'device_id': dock_scanner['device_id'],
                    'scan_type': 'LOADING_DOCK', 'result': 'FAIL' if is_fail else 'OK', 'scan_timestamp': dock_time,
                    'dynamic_weight': round(parcel['weight_kg'], 2)
                })

                if is_fail:
                    exc_status = 'RESOLVED'
                    res_time = dock_time + timedelta(minutes=random.randint(15, 240))
                    exceptions.append({
                        'exception_id': get_next_id('EXC'), 'parcel_id': p_id, 'device_id': dock_scanner['device_id'], 
                        'error_code': random.choice(ERROR_MAP['Scanner']), 'status': exc_status, 
                        'reported_at': dock_time, 'resolved_at': res_time, 'employee_id': random.choice(EMPLOYEES)
                    })
                    parcel['status'] = 'EXCEPTION'
                    status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'EXCEPTION', 'change_timestamp': dock_time})
                    parcels.append(parcel)
                    continue

                # --- SCAN 5: LOADED ---
                load_time = max(dock_time + timedelta(minutes=random.randint(*get_timing_range(service_type, 'loaded_minutes'))), dest_route['start_time'])
                load_scanner = random.choice(outbound_scanners)
                is_fail = random.random() < 0.005

                scans.append({
                    'scan_id': get_next_id('SCN'), 'parcel_id': p_id, 'device_id': load_scanner['device_id'],
                    'scan_type': 'LOADED', 'result': 'FAIL' if is_fail else 'OK', 'scan_timestamp': load_time,
                    'dynamic_weight': round(parcel['weight_kg'], 2)
                })

                if is_fail:
                    exc_status = 'RESOLVED'
                    res_time = load_time + timedelta(minutes=random.randint(15, 240))
                    exceptions.append({
                        'exception_id': get_next_id('EXC'), 'parcel_id': p_id, 'device_id': load_scanner['device_id'], 
                        'error_code': random.choice(ERROR_MAP['Scanner']), 'status': exc_status, 
                        'reported_at': load_time, 'resolved_at': res_time, 'employee_id': random.choice(EMPLOYEES)
                    })
                    parcel['status'] = 'EXCEPTION'
                    status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'EXCEPTION', 'change_timestamp': load_time})
                    parcels.append(parcel)
                    continue

                # SUCCESSFUL END OF JOURNEY
                dest_route['parcel_count'] += 1
                parcel['status'] = 'LOADED'
                status_history.append({'history_id': get_next_id('ST'), 'parcel_id': p_id, 'status_name': 'LOADED', 'change_timestamp': load_time})
                
                parcels.append(parcel)

        # --- COMPILE LOADING TABLE ---
        loading = []
        for dock in loading_docks:
            if dock['parcel_count'] > 0:
                loading.append({
                    'loading_id': dock['loading_id'],
                    'dock_id': dock['dock_id'],
                    'start_time': dock['start_time'],
                    'close_time': dock['start_time'] + timedelta(hours=2),
                    'parcel_count': dock['parcel_count'],
                    'route_id': dock['route_id'],
                    'employee_id': random.choice(EMPLOYEES)
                })

        # --- SAVE DAILY BATCH TO CSV ---
        pd.DataFrame(parcels).to_csv(f'{date_str}_parcels.csv', index=False)
        pd.DataFrame(status_history).to_csv(f'{date_str}_status_history.csv', index=False)
        pd.DataFrame(scans).to_csv(f'{date_str}_scans.csv', index=False)
        pd.DataFrame(sorting).to_csv(f'{date_str}_sorting.csv', index=False)
        pd.DataFrame(exceptions).to_csv(f'{date_str}_exceptions.csv', index=False)
        pd.DataFrame(intakes).to_csv(f'{date_str}_intake.csv', index=False)
        pd.DataFrame(loading).to_csv(f'{date_str}_loading.csv', index=False)
        
        print(f"✅ Saved 7 daily files for {date_str}")

# --- EXECUTION ---
generate_multi_day_data()
print("\n🎉 Massive Multi-Day Data Lake generated successfully!")