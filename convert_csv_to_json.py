import csv
import json
import re
from datetime import datetime

def parse_time_to_ms(time_str):
    """Convierte tiempo MM:SS.mmm a milisegundos"""
    if not time_str or time_str == '-':
        return 0
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return int((minutes * 60 + seconds) * 1000)
        return 0
    except:
        return 0

def convert_csv_to_json(csv_file, output_file, ronda_number):
    """Convierte CSV de Assetto Corsa a JSON"""
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraer información básica
    track_match = re.search(r'Track:,\s*"([^,]+),\s*([^"]+)"', content)
    track_name = track_match.group(1) if track_match else "unknown"
    track_config = track_match.group(2) if track_match else ""
    
    # Extraer resultados de carrera
    race_section = content.split("Race result")[1].split("Race laps")[0]
    lines = race_section.strip().split('\n')
    
    result = []
    cars = []
    laps_data = []
    
    # Parsear resultados
    for line in lines[2:]:  # Skip header
        if not line.strip() or line.startswith("'"):
            continue
        
        parts = [p.strip(' "') for p in line.split(',')]
        if len(parts) < 10:
            continue
            
        try:
            pos = parts[0]
            team = parts[2]
            vehicle = parts[3]
            driver = parts[4]
            num_laps = int(parts[5]) if parts[5].isdigit() else 0
            time_str = parts[6]
            best_lap_str = parts[7]
            
            if num_laps == 0:
                continue
            
            # Calcular tiempo total
            if "+" in time_str:
                total_time = parse_time_to_ms(best_lap_str) * num_laps
            else:
                total_time = parse_time_to_ms(time_str)
            
            best_lap = parse_time_to_ms(best_lap_str)
            
            result.append({
                "BallastKG": 0,
                "CarId": len(result),
                "CarModel": vehicle,
                "ClassID": "f06f18d6-77d5-4309-b17e-a9923583f6db",
                "Disqualified": False,
                "DriverGuid": f"driver_{len(result)}",
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
                "CarId": len(cars),
                "Driver": {
                    "Guid": f"driver_{len(cars)}",
                    "GuidsList": [f"driver_{len(cars)}"],
                    "Name": driver,
                    "Nation": "",
                    "Team": team,
                    "ClassID": "f06f18d6-77d5-4309-b17e-a9923583f6db"
                },
                "Model": vehicle,
                "Restrictor": 0,
                "Skin": f"skin0{len(cars) % 8}",
                "ClassID": "f06f18d6-77d5-4309-b17e-a9923583f6db",
                "MinPing": 0,
                "MaxPing": 0
            })
        except Exception as e:
            print(f"Error parsing line: {line[:50]}... - {e}")
            continue
    
    # Parsear vueltas - MEJORADO
    laps_section_match = re.search(r'Race laps\n\'=+\n(.*?)(?:\n\nRace best laps|Average|$)', content, re.DOTALL)
    if laps_section_match:
        laps_section = laps_section_match.group(1)
        
        current_driver = None
        current_car_id = 0
        
        lines = laps_section.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detectar nombre de piloto
            if line.startswith('"') and not re.match(r'"[0-9]+ "', line):
                driver_match = re.match(r'"([^"]+)"', line)
                if driver_match:
                    current_driver = driver_match.group(1)
                    # Buscar el CarId del piloto
                    current_car_id = next((c["CarId"] for c in cars if c["Driver"]["Name"] == current_driver), -1)
                    i += 1
                    continue
            
            # Parsear vuelta
            if current_driver and current_car_id >= 0 and re.match(r'"[0-9]+ "', line):
                try:
                    # Parsear la línea de vuelta
                    parts = re.findall(r'"([^"]*)"', line)
                    if len(parts) >= 8:
                        lap_time_str = parts[4]
                        sector1_str = parts[5]
                        sector2_str = parts[6]
                        sector3_str = parts[7]
                        
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
                    pass
            
            i += 1
    
    # Crear JSON final
    json_data = {
        "Version": 7,
        "EventName": f"Super GT - Ronda {ronda_number}",
        "Grip": 0.98,
        "Temperature": 25,
        "Humidity": 45,
        "Cars": cars,
        "Events": [],
        "Laps": laps_data,
        "Result": result,
        "TrackName": track_name,
        "TrackConfig": track_config,
        "Type": "RACE",
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "SessionFile": f"ronda{ronda_number}.json",
        "ChampionshipID": "supergt",
        "RaceWeekendID": f"ronda{ronda_number}"
    }
    
    # Guardar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Convertido: {csv_file} -> {output_file}")
    print(f"  - {len(result)} pilotos")
    print(f"  - {len(laps_data)} vueltas")

# Convertir las 4 rondas
for i in range(1, 5):
    csv_file = f"SuperGT/Ronda {i}.csv"
    output_file = f"SuperGT/Ronda {i}.json"
    try:
        convert_csv_to_json(csv_file, output_file, i)
    except Exception as e:
        print(f"✗ Error en Ronda {i}: {e}")

print("\n¡Conversión completada!")
