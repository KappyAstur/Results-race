import json
import re
from datetime import datetime

def parse_time_to_ms(time_str):
    """Convierte tiempo MM:SS.mmm a milisegundos"""
    if not time_str or time_str == '-' or time_str == '0':
        return 0
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            minutes = int(parts[0])
            seconds = float(parts[1])
            return int((minutes * 60 + seconds) * 1000)
        else:
            return int(float(time_str) * 1000)
    except:
        return 0

def convert_csv_to_json(csv_file, output_file, ronda_number):
    """Convierte CSV de Assetto Corsa a JSON"""
    
    print(f"\nProcesando {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Buscar sección de resultados
    result = []
    cars = []
    laps_data = []
    events = []
    
    in_race_result = False
    in_race_laps = False
    in_race_incidents = False
    current_driver = None
    current_car_id = -1
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Detectar sección de resultados
        if 'Race result' in line:
            in_race_result = True
            in_race_laps = False
            continue
        
        # Detectar sección de vueltas DE CARRERA (no Qualify)
        if 'Race laps' in line:
            in_race_result = False
            in_race_laps = True
            print(f"  Iniciando parseo de vueltas de carrera...")
            continue
        
        if 'Race best laps' in line or 'Race consistency' in line or 'Race sectors' in line:
            if in_race_laps:
                print(f"  Fin de sección de vueltas")
            in_race_laps = False
            # NO hacer break aquí, continuar para buscar incidentes
            continue
        
        # Detectar sección de incidentes
        if 'Race incidents' in line:
            in_race_result = False
            in_race_laps = False
            in_race_incidents = True
            print(f"  Iniciando parseo de incidentes...")
            continue
        
        if in_race_incidents and ('Race cuts' in line or line.startswith("'+++")):
            if in_race_incidents:
                print(f"  Fin de sección de incidentes")
            in_race_incidents = False
            break
        
        # Parsear resultados
        if in_race_result and line.startswith('"'):
            parts = [p.strip(' "') for p in line.split('",')]
            if len(parts) >= 10:
                try:
                    pos = parts[0].strip('"')
                    if not pos.isdigit():
                        continue
                    
                    team = parts[2]
                    vehicle = parts[3]
                    driver = parts[4]
                    num_laps_str = parts[5]
                    best_lap_str = parts[7]
                    
                    if not num_laps_str.isdigit():
                        continue
                    
                    num_laps = int(num_laps_str)
                    if num_laps == 0:
                        continue
                    
                    best_lap = parse_time_to_ms(best_lap_str)
                    total_time = best_lap * num_laps  # Aproximación
                    
                    car_id = len(result)
                    
                    result.append({
                        "BallastKG": 0,
                        "CarId": car_id,
                        "CarModel": vehicle,
                        "ClassID": "f06f18d6-77d5-4309-b17e-a9923583f6db",
                        "Disqualified": False,
                        "DriverGuid": f"driver_{car_id}",
                        "DriverName": driver,
                        "DriverNation": "",
                        "HasPenalty": False,
                        "LapPenalty": 0,
                        "Restrictor": 0,
                        "TotalTime": total_time,
                        "BestLap": best_lap,
                        "NumLaps": num_laps,
                        "Cuts": 0,
                        "Team": team
                    })
                    
                    cars.append({
                        "BallastKG": 0,
                        "CarId": car_id,
                        "Driver": {
                            "Guid": f"driver_{car_id}",
                            "GuidsList": [f"driver_{car_id}"],
                            "Name": driver,
                            "Nation": "",
                            "Team": team,
                            "ClassID": "f06f18d6-77d5-4309-b17e-a9923583f6db"
                        },
                        "Model": vehicle,
                        "Restrictor": 0,
                        "Skin": f"skin0{car_id % 8}",
                        "ClassID": "f06f18d6-77d5-4309-b17e-a9923583f6db",
                        "MinPing": 0,
                        "MaxPing": 0
                    })
                except Exception as e:
                    print(f"Error en resultado: {e}")
                    continue
        
        # Parsear vueltas
        if in_race_laps:
            # Detectar nombre de piloto (línea que empieza con comillas pero no es número de vuelta)
            if line.startswith('"') and not re.match(r'"[0-9]+ "', line):
                match = re.match(r'"([^"]+)"', line)
                if match:
                    current_driver = match.group(1)
                    # Buscar CarId
                    current_car_id = next((c["CarId"] for c in cars if c["Driver"]["Name"] == current_driver), -1)
                    if current_car_id >= 0:
                        print(f"    Parseando vueltas de: {current_driver}")
                    continue
            
            # Parsear línea de vuelta (formato: "1 ", chawaii_subaru...)
            if current_driver and current_car_id >= 0 and re.match(r'"[0-9]+ "', line):
                try:
                    # Extraer todos los valores separados por comas
                    parts = line.split(',')
                    if len(parts) >= 9:
                        # Extraer tiempos (están entre comillas)
                        lap_time_str = parts[4].strip(' "')
                        sector1_str = parts[5].strip(' "')
                        sector2_str = parts[6].strip(' "')
                        sector3_str = parts[7].strip(' "')
                        
                        lap_time = parse_time_to_ms(lap_time_str)
                        sector1 = parse_time_to_ms(sector1_str)
                        sector2 = parse_time_to_ms(sector2_str)
                        sector3 = parse_time_to_ms(sector3_str)
                        
                        if lap_time > 0:
                            laps_data.append({
                                "BallastKG": 0,
                                "CarId": current_car_id,
                                "CarModel": cars[current_car_id]["Model"],
                                "Cuts": 0,
                                "DriverGuid": f"driver_{current_car_id}",
                                "DriverName": current_driver,
                                "LapTime": lap_time,
                                "Restrictor": 0,
                                "Sectors": [sector1, sector2, sector3],
                                "Timestamp": int(datetime.now().timestamp()),
                                "Tyre": "M",
                                "ClassID": "f06f18d6-77d5-4309-b17e-a9923583f6db",
                                "ContributedToFastestLap": False,
                                "SpeedTrapHits": [],
                                "Conditions": {
                                    "Ambient": 25,
                                    "Road": 40,
                                    "Grip": 0.98,
                                    "WindSpeed": 5,
                                    "WindDirection": 45,
                                    "RainIntensity": 0,
                                    "RainWetness": 0,
                                    "RainWater": 0
                                }
                            })
                except Exception as e:
                    print(f"Error en vuelta: {e}")
                    continue
        
        # Parsear incidentes
        if in_race_incidents and line.startswith('"'):
            try:
                # Formato: "", "Driver1 reported contact with another vehicle Driver2. Impact speed: X.X",
                match = re.search(r'"([^"]+) reported contact with another vehicle ([^.]+)\. Impact speed: ([0-9.]+)"', line)
                if match:
                    driver1 = match.group(1)
                    driver2 = match.group(2)
                    impact_speed = float(match.group(3))
                    
                    # Buscar CarIds
                    car1_id = next((c["CarId"] for c in cars if c["Driver"]["Name"] == driver1), -1)
                    car2_id = next((c["CarId"] for c in cars if c["Driver"]["Name"] == driver2), -1)
                    
                    if car1_id >= 0 and car2_id >= 0:
                        events.append({
                            "Type": "COLLISION_WITH_CAR",
                            "CarId": car1_id,
                            "Driver": driver1,
                            "OtherCarId": car2_id,
                            "OtherDriver": driver2,
                            "ImpactSpeed": impact_speed,
                            "Timestamp": int(datetime.now().timestamp())
                        })
                        continue
                
                # Formato: "", "Driver reported contact with environment. Impact speed: X.X",
                match_env = re.search(r'"([^"]+) reported contact with environment\. Impact speed: ([0-9.]+)"', line)
                if match_env:
                    driver = match_env.group(1)
                    impact_speed = float(match_env.group(2))
                    
                    car_id = next((c["CarId"] for c in cars if c["Driver"]["Name"] == driver), -1)
                    
                    if car_id >= 0:
                        events.append({
                            "Type": "COLLISION_WITH_ENV",
                            "CarId": car_id,
                            "Driver": driver,
                            "ImpactSpeed": impact_speed,
                            "Timestamp": int(datetime.now().timestamp())
                        })
            except Exception as e:
                print(f"Error en incidente: {e}")
                continue
    
    # Crear JSON
    json_data = {
        "Version": 7,
        "EventName": f"Super GT - Ronda {ronda_number}",
        "Grip": 0.98,
        "Temperature": 25,
        "Humidity": 45,
        "Cars": cars,
        "Events": events,
        "Laps": laps_data,
        "Result": result,
        "TrackName": "autopolis",
        "TrackConfig": "international",
        "Type": "RACE",
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "SessionFile": f"ronda{ronda_number}.json",
        "ChampionshipID": "supergt",
        "RaceWeekendID": f"ronda{ronda_number}"
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Convertido: {output_file}")
    print(f"  - {len(result)} pilotos")
    print(f"  - {len(laps_data)} vueltas totales")
    print(f"  - {len(events)} incidentes")

# Convertir las 4 rondas
for i in range(1, 5):
    csv_file = f"SuperGT/Ronda {i}.csv"
    output_file = f"SuperGT/Ronda {i}.json"
    try:
        convert_csv_to_json(csv_file, output_file, i)
    except Exception as e:
        print(f"✗ Error en Ronda {i}: {e}")

print("\n¡Conversión completada!")
