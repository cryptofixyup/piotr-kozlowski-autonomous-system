Python

import time
from logi_agent_api import fetch_orders, assign_vehicle, assign_carrier, calculate_margin, check_backhaul, check_consolidation, update_dashboard

SLEEP_INTERVAL = 300  # 5 min

def run_pipeline():
    orders = fetch_orders(status='new')
    vehicles = fetch_vehicles()
    carriers = fetch_carriers()
    
    for order in orders:
        vehicle = assign_vehicle(order, vehicles)
        carrier = assign_carrier(order, carriers)
        margin = calculate_margin(order, vehicle, carrier)
        backhaul = check_backhaul(order)
        consolidation = check_consolidation(order)
        
        update_dashboard(order.id, vehicle, carrier, margin, backhaul, consolidation)

if __name__ == "__main__":
    while True:
        run_pipeline()
        time.sleep(SLEEP_INTERVAL)
