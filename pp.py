import pulp

# Model
# model = LpProblem("manu", sense = LpMaximize)

# objective
# x1 = LpVariable("x1", lowBound = 0)
# x2 = LpVariable("x2", lowBound = 0)
# x3 = LpVariable("x3", lowBound = 0)
# x4 = LpVariable("x4", lowBound = 0)

# objective function
# model += 20 * x1 + 12 *x2 + 40 * x3 + 25 * x4

# constraints
# model += x1 + x2 + x3 + x4 <= 50
# model += 3 * x1 + 2 * x2 + x3  <= 100
# model += x2 + 2 * x3 + 3 * x4 <= 90
# model += x1 >= 0
# model += x2 >= 0
# model += x3 >= 0
# model += x4 >= 0

# model.solve()

# print(model)

# print("Status: ", LpStatus[model.status])
# for var in model.variables():
#     print(var.name, " = ", var.varValue)
#     print("Objective: ", value(model.objective))

# print(f"x1: {x1.value()}")
# print(f"x2: {x2.value()}")
# print(f"x3: {x3.value()}")
# print(f"x4: {x4.value()}")

# model = pulp.LpProblem("manu", sense = pulp.LpMinimize)

# # objective
# x1 = pulp.LpVariable("x1", lowBound = 0)
# x2 = pulp.LpVariable("x2", lowBound = 0)

# # objective function 
# model += - x1  - 2 * x2

# # constraints

# model += 2 * x1 + x2 <= 20 
# model += - 4 * x1 + 5 * x2 <= 10
# model += x1 - 2 * x2 <= 2
# model += - x1 + 5 * x2 == 15
# model += x1 >= 0
# model += x2 >= 0

# model.solve()

# print(f"x1: {x1.value()}")
# print(f"x2: {x2.value()}")
# print(f"Objective: {model.objective.value()}")

