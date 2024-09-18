# imports
import pandas as pd 
import pyomo.environ as pe 
import pyomo.opt as po
import csv
from collections import defaultdict


data = pd.read_csv('dataset/vehicles.csv')
data_v = pd.read_csv("dataset/vehicles_fuels.csv")

def read_vehicle_data(file_path):

    data = pd.read_csv(file_path)
    vehicle_cost = {}
    vehicle_range = {}
    for _, row in data.iterrows():
        vehicle_cost[row["ID"]] = row["Cost ($)"]
        vehicle_range[row["ID"]] = row["Yearly range (km)"]

    return vehicle_cost, vehicle_range

def read_vehicle_fuel_data(file_path):

    data = pd.read_csv(file_path)
    vehicle_consumption = defaultdict(lambda: 0.0) 
    for _, row in data.iterrows():
        key = (row['ID'], row['Fuel'])
        vehicle_consumption[key] = row["Consumption (unit_fuel/km)"]

    return vehicle_consumption

def read_demand_data(file_path):
    data = pd.read_csv(file_path)
    vehicle_demand = {}
    for _, row in data.iterrows():
        key = (row['Year'], row['Size'], row['Distance'])
        vehicle_demand[key] = row["Demand (km)"]
    
    return vehicle_demand

def read_fuel_data(file_path):
    data = pd.read_csv(file_path)
    fuel_emissions = {}
    fuel_cost = {}
    for _, row in data.iterrows():
        key = (row['Fuel'], row['Year'])
        fuel_emissions[key] = row['Emissions (CO2/unit_fuel)']
        fuel_cost[key] = row['Cost ($/unit_fuel)']
    
    return fuel_emissions, fuel_cost


years = (range(2023, 2039))
vehicles = data["ID"]
size_bucket = {'S1', 'S2', 'S3', 'S4'}
distance_bucket = {'D1', 'D2', 'D3', 'D4'}
fuel_types = {'Electricity', 'B20', 'LNG', 'BioLNG', 'HVO'}
vehicle_cost, vehicle_range = read_vehicle_data("dataset/vehicles.csv")
vehicle_consumption = read_vehicle_fuel_data("dataset/vehicles_fuels.csv")
vehicle_demand = read_demand_data("dataset/demand.csv")
fuel_emissions, fuel_cost = read_fuel_data("dataset/fuels.csv")


### Model

model = pe.ConcreteModel()


# Set

model.years = pe.Set(initialize = years)
model.vehicles = pe.Set(initialize = vehicles)
model.size = pe.Set(initialize = size_bucket)
model.distance = pe.Set(initialize = distance_bucket)
model.fuel = pe.Set(initialize = fuel_types)
carbon_emission = {
    2023: 11677957,
    2024: 10510161,
    2025: 9459145,
    2026: 8513230,
    2027: 7661907,
    2028: 6895716,
    2029: 6206145,
    2030: 5585530,
    2031: 5026977,
    2032: 4524279,
    2033: 4071851,
    2034: 3664666,
    2035: 3298199,
    2036: 2968379,
    2037: 2671541,
    2038: 2404387
}


# parameters

model.carbon_emissions = pe.Param(model.years, initialize = carbon_emission)
model.vehicle_cost = pe.Param(model.vehicles, initialize = vehicle_cost)
model.vehicle_range = pe.Param(model.vehicles, initialize = vehicle_range)
model.vehicle_consumption = pe.Param(model.vehicles, model.fuel, initialize = vehicle_consumption, default = 0.0)
model.vehicle_demand = pe.Param(model.years, model.size, model.distance, initialize = vehicle_demand)
model.fuel_emissions = pe.Param(model.fuel, model.years, initialize = fuel_emissions)
model.fuel_cost = pe.Param(model.fuel, model.years, initialize = fuel_cost)


# variables 

model.number_vehicles_bought = pe.Var(model.vehicles, model.years, domain = pe.NonNegativeIntegers)
model.number_vehicles_use = pe.Var(model.vehicles, model.fuel, model.years, domain = pe.NonNegativeIntegers)
model.number_vehicles_sold = pe.Var(model.vehicles, model.years, domain = pe.NonNegativeIntegers)
model.number_vehicles_distance = pe.Var(model.vehicles, model.fuel, model.years, domain = pe.NonNegativeIntegers)


# constraint 1

model.size_constraint = pe.ConstraintList()

size_to_vehicles = {size: list(data[data["Size"] == size]["ID"]) for size in size_bucket}

for year in years:
    for size in size_bucket:
        for distance in distance_bucket:
            model.size_constraint.add(
                sum(model.number_vehicles_distance[v, f, year] for v in size_to_vehicles[size] for f in fuel_types) >= model.vehicle_demand[year, size, distance]
            )    


# constraint 2

model.distance_constraint = pe.ConstraintList()

# Vehicle belonging to distance bucket Dx can satisfy all demands for distance bucket D1 to 
# Dx. For example, vehicle belonging to distance bucket D4 can satisfy demand of D1, D2, 
# D3, D4buckets; similarly, D3 can satisfy D1, D2, D3 but NOT D4

distance_satisfies = {
    'D1': ['D1'],
    'D2': ['D1', 'D2'],
    'D3': ['D1', 'D2', 'D3'],
    'D4': ['D1', 'D2', 'D3', 'D4']
}

for year in years:
    for size in size_bucket:
        for distance in distance_bucket:
            valid_distances = distance_satisfies[distance]
            model.distance_constraint.add(
                sum(model.number_vehicles_distance[v, f, year] 
                    for v in vehicles 
                    for f in fuel_types
                    if data[data["ID"] == v]["Distance"].values[0] in valid_distances
                    ) >= model.vehicle_demand[year, size, distance]
            )


# constraints 3

model.carbon_emission_constraint = pe.ConstraintList()

# total carbon emission by fleet operation each year should be within the respective year's carbon emission limit provided in the carbon_emission csv file

for year in years:
    model.carbon_emission_constraint.add(
        sum(
            model.number_vehicles_distance[v, f, year] *
            model.number_vehicles_use[v, f, year] *
            model.vehicle_consumption[v, f] *
            model.fuel_emissions[f, year]
            for v in vehicles
            for f in fuel_types
        ) <= model.carbon_emissions[year]
    )


# constraints 4

model.yearly_demand_constraint = pe.ConstraintList()

# Total yearly demand for each year must be satisfied for each distance and size bucket

vehicles_ids_by_size = { size: data[data['Size'] == size]['ID'].tolist() for size in size_bucket}

for year in years:
    for size in size_bucket:
        for distance in distance_bucket:
            demand_value = model.vehicle_demand[year, size, distance]
            if demand_value > 0:
                model.yearly_demand_constraint.add(
                    sum(
                        model.number_vehicles_distance[v, f, year] *
                        model.number_vehicles_use[v, f, year]
                        for v in vehicles_ids_by_size[size]
                        for f in fuel_types
                    ) >= demand_value
                )


# constraint 5

model.vehicle_purchase_constraint = pe.ConstraintList()

# Vehicle model of year 20xx can only be bought in the year 20xx. For example, 
# Diesel_S1_2026 can only be bought in 2026 and not in any subsequent or previous years.

vehicle_model_year = {}
for v in vehicles:
    year = int(v.split('_')[-1])
    vehicle_model_year[v] = year

for v in vehicles:
    model_year = vehicle_model_year[v]
    for year in years:
        if year != model.years:
            model.vehicle_purchase_constraint.add(
                model.number_vehicles_bought[v, year] == 0
            )


# constraint 6

model.vehicle_lifetime_constraint = pe.ConstraintList()

# Every vehicle has a 10-year life and must be sold by the end of 10th year. For example, a 
# vehicle bought in 2025 must be sold by the end of 2034. 

for v in vehicles:
    for purchase_year in years:
        sell_years = range(purchase_year, min(purchase_year + 10, max(years) + 1))
        model.vehicle_lifetime_constraint.add(
            sum(model.number_vehicles_sold[v, sell_year] for sell_year in sell_years) >= model.number_vehicles_bought[v, purchase_year]
        )


# constraint  7

# You cannot buy/sell a vehicle mid-year. All buy operations happen at the beginning of the 
# year and all sell operations happen at the end of the year

model.use_after_purchase_constraint = pe.ConstraintList()

for v in vehicles:
    for year in years:
        model.use_after_purchase_constraint.add(        
            sum(model.number_vehicles_use[v, f, year] for f in fuel_types) <= 
            sum(model.number_vehicles_bought[v, y] for y in years if y <= year)
        )

model.sell_at_end_of_year_constraint = pe.ConstraintList()

for v in vehicles:
    for year in years:
        model.sell_at_end_of_year_constraint.add(
            sum(model.number_vehicles_sold[v, y] for y in years if y <= year) <=
            sum(model.number_vehicles_bought[v, y] for y in years if y <= year)
        )


# constraint 8 

# Every year at most 20% of the vehicles in the existing fleet can be sold

model.sell_limit_constraint = pe.ConstraintList()

for year in years:
    for v in vehicles:
        existing_fleet = sum(model.number_vehicles_bought[v,y] - model.number_vehicles_sold[v, y] for y in years if y <= year)
        model.sell_limit_constraint.add(
            model.number_vehicles_sold[v, year] <=  0.2 * existing_fleet
        )


# cost profiles

resale_value = {1: 0.90, 2: 0.80, 3: 0.70, 4: 0.60, 5: 0.50, 6: 0.40, 7: 0.30, 8: 0.30, 9: 0.30, 10: 0.30}
insurance_cost = {1: 0.05, 2: 0.06, 3: 0.07, 4: 0.08, 5: 0.09, 6: 0.10, 7: 0.11, 8: 0.12, 9: 0.13, 10: 0.14}
maintenance_cost = {1: 0.01, 2: 0.03, 3: 0.05, 4: 0.07, 5: 0.09, 6: 0.11, 7: 0.13, 8: 0.15, 9: 0.17, 10: 0.19}
# Objective function

def total_cost(model):

    # buying cost
    buying_cost = sum(
        model.number_vehicles_bought[v, year] * model.vehicle_cost[v] 
        for v in model.vehicles for year in model.years
    ) 

    # Insurance cost
    ins_cost = sum ( 
        insurance_cost[min(year - y + 1, 10)] *
        model.vehicle_cost[v] * 
        model.number_vehicles_bought[v, y]
        for v in model.vehicles for year in model.years for y in model.years if y <= year
    ) 

    # Maintaenance cost
    mnt_cost = sum(
       model.vehicle_cost[v] * maintenance_cost[min(year - y + 1, 10)] *
        model.number_vehicles_bought[v, y]
        for v in model.vehicles for year in model.years for y in model.years if y <= year
    ) 

    # fuel cost
    fuel_cost = sum(
        model.number_vehicles_distance[v, f, year] * 
        model.vehicle_consumption[v, f] *
        model.fuel_cost[f, year]
        for v in model.vehicles for f in model.fuel for year in model.years
    )

    # selling cost
    sl_cost = sum(
        model.number_vehicles_sold[v, year] * model.vehicle_cost[v] *
        resale_value[min(year - y + 1, 10)]
        for v in model.vehicles for year in model.years for y in model.years if y <= year
    ) 

    return buying_cost + ins_cost + mnt_cost + fuel_cost - sl_cost

model.total_cost = pe.Objective(rule = total_cost, sense = pe.minimize)


model_instance = model.create_instance()
solver = po.SolverFactory('ipopt')


result = solver.solve(model_instance, tee = True)


# submission
def create_submission(model, output_file):
    results = []
    
    # Collect buy results
    for year in model.years:
        for v in model.vehicles:
            if pe.value(model.number_vehicles_bought[v, year]) > 0:
                results.append({
                    "Year": year,
                    "ID": v,
                    "Num_Vehicles": int(pe.value(model.number_vehicles_bought[v, year])),
                    "Type": "Buy",
                    "Fuel": None,
                    "Distance_bucket": None,
                    "Distance_per_vehicle(km)": 0.0
                })

    # Collect use results
    for year in model.years:
        for v in model.vehicles:
            for f in model.fuel:
                if pe.value(model.number_vehicles_use[v, f, year]) > 0:
                    for distance_bucket in distance_satisfies:
                        results.append({
                            "Year": year,
                            "ID": v,
                            "Num_Vehicles": int(pe.value(model.number_vehicles_use[v, f, year])),
                            "Type": "Use",
                            "Fuel": f,
                            "Distance_bucket": distance_bucket,
                            "Distance_per_vehicle(km)": pe.value(model.number_vehicles_distance[v, f, year])
                        })

    # Collect sell results
    for year in model.years:
        for v in model.vehicles:
            if pe.value(model.number_vehicles_sold[v, year]) > 0:
                results.append({
                    "Year": year,
                    "ID": v,
                    "Num_Vehicles": int(pe.value(model.number_vehicles_sold[v, year])),
                    "Type": "Sell",
                    "Fuel": None,
                    "Distance_bucket": None,
                    "Distance_per_vehicle(km)": 0.0
                })

    # Convert results to DataFrame and save as CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_file, index=False)

# Example usage
create_submission(model, 'submission.csv')