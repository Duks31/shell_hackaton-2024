from pyomo.environ import *

# Model
model = ConcreteModel()

# Sets
model.years = RangeSet(2023, 2038)
model.vehicle_types = Set()  # Populate with vehicle types from Vehicles.csv
model.size_buckets = Set()  # Populate with size buckets
model.distance_buckets = Set()  # Populate with distance buckets
model.fuel_types = Set()  # Populate with fuel types

# Parameters
model.purchase_cost = Param(model.vehicle_types, within=NonNegativeReals)

model.yearly_range = Param(model.vehicle_types, within=NonNegativeReals)

model.fuel_consumption = Param(model.vehicle_types, model.fuel_types, within=NonNegativeReals)

model.fuel_cost = Param(model.fuel_types, model.years, within=NonNegativeReals)

model.emission_factors = Param(model.fuel_types, within=NonNegativeReals)

model.demand = Param(model.years, model.size_buckets, model.distance_buckets, within=NonNegativeReals)

model.carbon_limits = Param(model.years, within=NonNegativeReals)

model.resale_value = Param(model.years, within=NonNegativeReals)

model.insurance_cost = Param(model.years, within=NonNegativeReals)

model.maintenance_cost = Param(model.years, within=NonNegativeReals)

# Variables
model.num_vehicles_bought = Var(model.vehicle_types, model.years, within=NonNegativeIntegers)
model.num_vehicles_used = Var(model.vehicle_types, model.years, within=NonNegativeIntegers)
model.num_vehicles_sold = Var(model.vehicle_types, model.years, within=NonNegativeIntegers)
model.distance_traveled = Var(model.vehicle_types, model.years, within=NonNegativeReals)
model.fuel_used = Var(model.vehicle_types, model.fuel_types, model.years, within=NonNegativeReals)

# Constraints
def demand_satisfaction_rule(model, year, size_bucket, distance_bucket):
    return sum(model.distance_traveled[v, year] for v in model.vehicle_types if (v.size_bucket == size_bucket and v.distance_bucket >= distance_bucket)) >= model.demand[year, size_bucket, distance_bucket]
model.demand_satisfaction = Constraint(model.years, model.size_buckets, model.distance_buckets, rule=demand_satisfaction_rule)

def emission_limit_rule(model, year):
    return sum(model.fuel_used[v, f, year] * model.fuel_consumption[v, f] * model.emission_factors[f] for v in model.vehicle_types for f in model.fuel_types) <= model.carbon_limits[year]
model.emission_limit = Constraint(model.years, rule=emission_limit_rule)

def vehicle_lifecycle_rule(model, v, year):
    return sum(model.num_vehicles_bought[v, y] for y in model.years if y <= year) - sum(model.num_vehicles_sold[v, y] for y in model.years if y <= year) == model.num_vehicles_used[v, year]
model.vehicle_lifecycle = Constraint(model.vehicle_types, model.years, rule=vehicle_lifecycle_rule)

# Objective function
def total_cost_rule(model):
    return sum(model.num_vehicles_bought[v, year] * model.purchase_cost[v] for v in model.vehicle_types for year in model.years) \
           + sum(model.fuel_used[v, f, year] * model.fuel_cost[f, year] for v in model.vehicle_types for f in model.fuel_types for year in model.years) \
           + sum(model.num_vehicles_used[v, year] * model.maintenance_cost[year] for v in model.vehicle_types for year in model.years) \
           + sum(model.num_vehicles_used[v, year] * model.insurance_cost[year] for v in model.vehicle_types for year in model.years) \
           - sum(model.num_vehicles_sold[v, year] * model.resale_value[year] for v in model.vehicle_types for year in model.years)
model.total_cost = Objective(rule=total_cost_rule, sense=minimize)

# Solve
solver = SolverFactory('glpk')
solver.solve(model)

# Results
model.num_vehicles_bought.display()
model.num_vehicles_used.display()
model.num_vehicles_sold.display()
model.distance_traveled.display()
model.fuel_used.display()