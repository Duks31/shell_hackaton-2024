import pandas as pd
import pyomo.environ as pyo
import csv

# Helper functions
def read_vehicle_cost(file_path):
    """
    This function reads the vehicle cost from the file and returns a dictionary of vehicle cost

    parameters: file_path: str: path to the file containing the vehicle cost
    """
    data = pd.read_csv(file_path)
    vehicle_cost = {}
    for _, row in data.iterrows():
        vehicle_cost[row["ID"]] = row["Cost ($)"]

    return vehicle_cost


def read_vehicle_range(file_path):
    """
    This function reads the vehicle range from the file and returns a dictionary of vehicle range

    parameters: file_path: str: path to the file containing the vehicle range
    """
    data = pd.read_csv(file_path)
    vehicle_range = {}
    for _, row in data.iterrows():
        vehicle_range[row["ID"]] = row["Yearly range (km)"]

    return vehicle_range


def read_fuel_cost(file_path):
    """
    This function reads the fuel cost from the file and returns a dictionary of fuel cost

    parameters: file_path: str: path to the file containing the fuel cost
    """
    data = pd.read_csv(file_path)
    fuel_cost = {}
    for _, row in data.iterrows():
        key = f"{row['Fuel']}_{int(row['Year'])}"
        fuel_cost[key] = float(row["Cost ($/unit_fuel)"])

    return fuel_cost


def read_fuel_consumption(file_path):
    """
    This function reads the fuel consumption from the file and returns a dictionary of fuel consumption

    parameters: file_path: str: path to the file containing the fuel consumption
    """
    data = pd.read_csv(file_path)
    fuel_consumption = {}
    for _, row in data.iterrows():
        fuel_consumption[row["ID"]] = row["Consumption (unit_fuel/km)"]

    return fuel_consumption


def read_fuel_emission_factors(file_path):
    """
    This function reads the fuel consumption from the file and returns a dictionary of fuel emissions

    parameters: file_path: str: path to the file containing the fuel consumption
    """
    data = pd.read_csv(file_path)
    emission_cost = {}
    for _, row in data.iterrows():
        key = f"{(row['Fuel'])}_{int(row['Year'])}"
        emission_cost[key] = float(row["Emissions (CO2/unit_fuel)"])

    return emission_cost


def read_demand(file_path):
    """
    This function reads the demand of cars from the file and returns a dict of demand in Km

    parameters: file_path: str: path to file the containing the demand of the cars
    """
    data = pd.read_csv(file_path)
    demand = {}
    for _, row in data.iterrows():
        key = f"{int(row['Year'])}_{row['Size']}_{row['Distance']}"
        demand[key] = row["Demand (km)"]

    return demand


def read_carbon_emission(file_path):
    """
    This function reads the carbon limits of each years

    parameters: file_path: str: path to the file containing the carbon emissions
    """
    data = pd.read_csv(file_path)
    carbon_emission = {}
    for _, row in data.iterrows():
        carbon_emission[row["Year"]] = row["Carbon emission CO2/kg"]

    return carbon_emission


def read_vehicle_mapping(file_path):
    data = pd.read_csv(file_path)
    vehicle_mapping = {}
    for _, row in data.iterrows():
        vehicle_id = row["ID"]
        size = row["Size"]
        distance = row["Distance"]
        vehicle_mapping[vehicle_id] = (size, distance)

    return vehicle_mapping


def read_vehicle_fuel_mapping(file_path):
    data = pd.read_csv(file_path)
    vehicle_fuel_mapping = {}
    for _, row in data.iterrows():
        vehicle_id = row["ID"]
        fuel = row["Fuel"]
        vehicle_fuel_mapping[vehicle_id] = fuel
    return vehicle_fuel_mapping


# Data

purchased_cost_data = read_vehicle_cost("dataset/vehicles.csv")

vehicle_range_data = read_vehicle_range("dataset/vehicles.csv")

fuel_cost_data = read_fuel_cost("dataset/fuels.csv")

fuel_consumption_data = read_fuel_consumption("dataset/vehicles_fuels.csv")

emission_factor = read_fuel_emission_factors("dataset/fuels.csv")

demand_data = read_demand("dataset/demand.csv")

carbon_limit_data = read_carbon_emission("dataset/carbon_emissions.csv")

vehicle_to_size_distance = read_vehicle_mapping("dataset/vehicles.csv")

vehicle_to_fuel = read_vehicle_fuel_mapping("dataset/vehicles_fuels.csv")

# Model
model = pyo.ConcreteModel()

# Set
model.years = pyo.Set(initialize=range(2023, 2039))
model.vehicle_types = pyo.Set(initialize=purchased_cost_data.keys())
model.size_buckets = pyo.Set(initialize=["S1", "S2", "S3", "S4"])
model.distance_buckets = pyo.Set(initialize=["D1", "D2", "D3", "D4"])
model.fuel_types = pyo.Set(initialize=["Electricity", "B20", "LNG", "BioLNG", "HVO"])

# Parameters

# Cost of buying vehicles
model.purchase_cost = pyo.Param(
    model.vehicle_types, initialize=purchased_cost_data, within=pyo.NonNegativeReals
)

# vehicle ranges
model.vehicle_range = pyo.Param(
    model.vehicle_types, initialize=vehicle_range_data, within=pyo.NonNegativeReals
)

# fuel cost
model.fuel_cost = pyo.Param(
    model.fuel_types,
    model.years,
    initialize=lambda model, f, y: fuel_cost_data[f"{f}_{y}"],
    within=pyo.NonNegativeReals,
)

# fuel consumption
model.fuel_consumption = pyo.Param(
    model.vehicle_types, initialize=fuel_consumption_data, within=pyo.NonNegativeReals
)

# fuel emission factors
model.emission_factor = pyo.Param(
    model.fuel_types,
    model.years,
    initialize=lambda model, f, y: emission_factor[f"{f}_{y}"],
    within=pyo.NonNegativeReals,
)

# demand
model.demand = pyo.Param(
    model.years,
    model.size_buckets,
    model.distance_buckets,
    initialize=lambda model, y, s, d: demand_data[f"{y}_{s}_{d}"],
    within=pyo.NonNegativeReals,
)

# carbon limits
model.carbon_limit = pyo.Param(
    model.years, initialize=carbon_limit_data, within=pyo.NonNegativeReals
)

# resale value
resale_percentage = {
    1: 0.90,
    2: 0.80,
    3: 0.70,
    4: 0.60,
    5: 0.50,
    6: 0.40,
    7: 0.30,
    8: 0.30,
    9: 0.30,
    10: 0.30,
}

# insurance value
insurance_percentage = {
    1: 0.05,
    2: 0.06,
    3: 0.07,
    4: 0.08,
    5: 0.09,
    6: 0.10,
    7: 0.11,
    8: 0.12,
    9: 0.13,
    10: 0.14,
}

# maintenance value
maintenance_percentage = {
    1: 0.01,
    2: 0.03,
    3: 0.05,
    4: 0.07,
    5: 0.09,
    6: 0.11,
    7: 0.13,
    8: 0.15,
    9: 0.17,
    10: 0.19,
}


# Variables
model.num_vehicles_bought = pyo.Var(
    model.vehicle_types, model.years, within=pyo.NonNegativeIntegers, bounds=(0, None)
)
model.num_vehicles_used = pyo.Var(
    model.vehicle_types, model.years, within=pyo.NonNegativeIntegers, bounds=(0, None)
)
model.num_vehicles_sold = pyo.Var(
    model.vehicle_types, model.years, within=pyo.NonNegativeIntegers, bounds=(0, None)
)
model.num_vehicles_traveled = pyo.Var(
    model.vehicle_types, model.years, within=pyo.NonNegativeIntegers, bounds=(0, None)
)
model.fuel_used = pyo.Var(
    model.fuel_types, model.years, within=pyo.NonNegativeReals, bounds=(0, None)
)


# Constraints
def demand_satisfaction_constraint(model, y, s, d):
    return (
        sum(
            model.num_vehicles_traveled[v, y] * model.vehicle_range[v]
            for v in model.vehicle_types
        )
        >= model.demand[y, s, d]
    )


model.demand_satisfaction_constraint = pyo.Constraint(
    model.years,
    model.size_buckets,
    model.distance_buckets,
    rule=demand_satisfaction_constraint,
)


def size_distance_bucket_constraint(model, v, y):
    size, distance = vehicle_to_size_distance[v]
    return sum(
        model.num_vehicles_used[v, y]
        for v in model.vehicle_types
        if vehicle_to_size_distance[v] == (size, distance)
    ) == sum(
        model.num_vehicles_bought[v, y]
        for v in model.vehicle_types
        if vehicle_to_size_distance[v] == (size, distance)
    ) - sum(
        model.num_vehicles_sold[v, y]
        for v in model.vehicle_types
        if vehicle_to_size_distance[v] == (size, distance)
    )


model.size_distance_bucket_constraint = pyo.Constraint(
    model.vehicle_types, model.years, rule=size_distance_bucket_constraint
)


def carbon_emission_constraint(model, y):
    return (
        sum(
            model.fuel_used[f, y] * model.emission_factor[f, y]
            for f in model.fuel_types
        )
        <= model.carbon_limit[y]
    )


model.carbon_emission_constraint = pyo.Constraint(
    model.years, rule=carbon_emission_constraint
)


def purchase_year_constraint(model, v, y):
    purchase_year = int(v.split("_")[-1])
    if y == purchase_year:
        return model.num_vehicles_bought[v, y] >= 0
    else:
        return model.num_vehicles_bought[v, y] == 0


model.purchase_year_constraint = pyo.Constraint(
    model.vehicle_types, model.years, rule=purchase_year_constraint
)


def vehicle_life_constraint(model, v, y):
    if y <= max(model.years) - 10:
        return model.num_vehicles_used[v, y] <= sum(
            model.num_vehicles_bought[v, yr] for yr in range(y, y + 10)
        )
    else:
        return model.num_vehicles_used[v, y] <= sum(
            model.num_vehicles_bought[v, yr] for yr in range(y, max(model.years) + 1)
        )


model.vehicle_life_constraint = pyo.Constraint(
    model.vehicle_types, model.years, rule=vehicle_life_constraint
)


def vehicle_inventory_balance_constraint(model, v, y):
    if y == min(model.years):
        # For the first year, there are no vehicles carried over from a previous year
        return model.num_vehicles_used[v, y] == model.num_vehicles_bought[v, y]
    else:
        return (
            model.num_vehicles_used[v, y]
            == model.num_vehicles_used[v, y - 1]
            + model.num_vehicles_bought[v, y]
            - model.num_vehicles_sold[v, y]
        )


model.vehicle_inventory_balance_constraint = pyo.Constraint(
    model.vehicle_types, model.years, rule=vehicle_inventory_balance_constraint
)


def sales_limit_constraint(model, v, y):
    return model.num_vehicles_sold[v, y] <= 0.2 * sum(
        model.num_vehicles_used[v, yr] for yr in range(min(model.years), y + 1)
    )


model.sales_limit_constraint = pyo.Constraint(
    model.vehicle_types, model.years, rule=sales_limit_constraint
)


# Objective function
def objective_function(model):
    total_cost = sum(
        model.purchase_cost[v] * model.num_vehicles_bought[v, y]
        - resale_percentage.get(y - int(v.split("_")[-1]), 0.30)
        * model.purchase_cost[v]
        * model.num_vehicles_sold[v, y]
        + model.purchase_cost[v]
        * insurance_percentage.get(y - int(v.split("_")[-1]), 0.14)
        + model.purchase_cost[v]
        * maintenance_percentage.get(y - int(v.split("_")[-1]), 0.19)
        for v in model.vehicle_types
        for y in model.years
    )

    fuel_cost = sum(
        model.fuel_cost[f, y] * model.fuel_used[f, y]
        for f in model.fuel_types
        for y in model.years
    )

    return total_cost + fuel_cost


model.objective = pyo.Objective(rule=objective_function, sense=pyo.minimize)


# Solver
solver = pyo.SolverFactory("glpk")
results = solver.solve(model)

print(pyo.value(model.objective))

# Result
model.display()

# # saving the result to a csv file

# # Open the CSV file to write the results
# with open('submission.csv', 'w', newline='') as csvfile:
#     fieldnames = ['Year', 'ID', 'Num_Vehicles', 'Type', 'Fuel', 'Distance_bucket', 'Distance_per_vehicle(km)']
#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#     # Write the header
#     writer.writeheader()

#     # Write the results for bought vehicles
#     for year in model.years:
#         for v in model.vehicle_types:
#             num_vehicles_bought = pyo.value(model.num_vehicles_bought[v, year])
#             if num_vehicles_bought > 0:
#                 print(f"Year: {year}, ID: {v}, Num_Vehicles_Bought: {num_vehicles_bought}")  # Debugging print
#                 writer.writerow({
#                     'Year': year,
#                     'ID': v,
#                     'Num_Vehicles': num_vehicles_bought,
#                     'Type': 'Buy',
#                     'Fuel': vehicle_to_fuel[v],  # Include fuel type
#                     'Distance_bucket': vehicle_to_size_distance[v][1],
#                     'Distance_per_vehicle(km)': 0.0
#                 })

#     # Write the results for used vehicles
#     for year in model.years:
#         for v in model.vehicle_types:
#             num_vehicles_used = pyo.value(model.num_vehicles_used[v, year])
#             if num_vehicles_used > 0:
#                 size, distance = vehicle_to_size_distance[v]
#                 fuel = vehicle_to_fuel[v]  # Include fuel type
#                 print(f"Year: {year}, ID: {v}, Num_Vehicles_Used: {num_vehicles_used}, Fuel: {fuel}, Distance: {distance}")  # Debugging print
#                 writer.writerow({
#                     'Year': year,
#                     'ID': v,
#                     'Num_Vehicles': num_vehicles_used,
#                     'Type': 'Use',
#                     'Fuel': fuel,
#                     'Distance_bucket': distance,
#                     'Distance_per_vehicle(km)': pyo.value(model.vehicle_range[v])
#                 })

# print("Submission file created successfully.")
