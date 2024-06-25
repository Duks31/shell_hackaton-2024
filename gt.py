import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum

# Load datasets
demand = pd.read_csv("/mnt/data/Demand.csv")
vehicles = pd.read_csv("/mnt/data/Vehicles.csv")
vehicles_fuels = pd.read_csv("/mnt/data/Vehicles_fuels.csv")
fuels = pd.read_csv("/mnt/data/Fuels.csv")
carbon_emissions = pd.read_csv("/mnt/data/Carbon_emissions.csv")

# Preprocess data
vehicles = vehicles.merge(vehicles_fuels, on="ID")

# Initialize the optimization problem
problem = LpProblem("Fleet_Decarbonization", LpMinimize)

# Define decision variables
years = range(2023, 2039)
vehicle_ids = vehicles["ID"].unique()
N_vyr = LpVariable.dicts("NumVehicles", (vehicle_ids, years), lowBound=0, cat="Integer")

# Define the objective function components
C_buy = lpSum(
    [
        N_vyr[v][yr] * vehicles.loc[vehicles["ID"] == v, "Cost"].values[0]
        for v in vehicle_ids
        for yr in years
    ]
)
C_ins = lpSum(
    [
        N_vyr[v][yr] * vehicles.loc[vehicles["ID"] == v, "Cost"].values[0] * 0.1
        for v in vehicle_ids
        for yr in years
    ]
)
C_mnt = lpSum(
    [
        N_vyr[v][yr] * vehicles.loc[vehicles["ID"] == v, "Cost"].values[0] * 0.05
        for v in vehicle_ids
        for yr in years
    ]
)
C_fuel = lpSum(
    [
        N_vyr[v][yr]
        * vehicles.loc[vehicles["ID"] == v, "Fuel Consumption"].values[0]
        * fuels.loc[
            fuels["Fuel Type"] == vehicles.loc[vehicles["ID"] == v, "Fuel"].values[0],
            "Cost per unit",
        ].values[0]
        for v in vehicle_ids
        for yr in years
    ]
)
C_sell = lpSum(
    [
        N_vyr[v][yr] * vehicles.loc[vehicles["ID"] == v, "Cost"].values[0] * 0.2
        for v in vehicle_ids
        for yr in years
    ]
)

# Total cost
C_total = C_buy + C_ins + C_mnt + C_fuel - C_sell
problem += C_total

# Demand constraints: Each year's demand for each size bucket must be met
for year in years:
    for size in demand["Size"].unique():Cost ($/unit_fuel)
        problem += (
            lpSum(
                [
                    N_vyr[v][year]
                    * vehicles.loc[vehicles["ID"] == v, "Yearly range"].values[0]
                    for v in vehicle_ids
                    if vehicles.loc[vehicles["ID"] == v, "Size"].values[0] == size
                ]
            )   
            >= demand[(demand["Year"] == year) & (demand["Size"] == size)][
                "Demand"
            ].sum()
        )

# Carbon emissions constraints: Each year's emissions must not exceed the limit
for year in years:
    problem += (
        lpSum(
            [
                N_vyr[v][year]
                * vehicles.loc[vehicles["ID"] == v, "Fuel Consumption"].values[0]
                * fuels.loc[
                    fuels["Fuel Type"]
                    == vehicles.loc[vehicles["ID"] == v, "Fuel"].values[0],
                    "Carbon Emission per unit",
                ].values[0]
                for v in vehicle_ids
            ]
        )
        <= carbon_emissions.loc[
            carbon_emissions["Year"] == year, "Emission limit"
        ].values[0]
    )

# Solve the problem
problem.solve()

# Extract results and save to CSV
results = []
for v in vehicle_ids:
    for yr in years:
        if N_vyr[v][yr].varValue > 0:
            results.append(
                [
                    yr,
                    v,
                    N_vyr[v][yr].varValue,
                    "Buy",
                    vehicles.loc[vehicles["ID"] == v, "Fuel"].values[0],
                    "D1",
                    vehicles.loc[vehicles["ID"] == v, "Yearly range"].values[0],
                ]
            )

results_df = pd.DataFrame(
    results,
    columns=[
        "Year",
        "ID",
        "Num_Vehicles",
        "Type",
        "Fuel",
        "Distance_bucket",
        "Distance_per_vehicle(km)",
    ],
)
results_df.to_csv("solution.csv", index=False)
