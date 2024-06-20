import pyomo.environ as pyo

# \test Problems

# model = pyo.ConcreteModel()

# model.x1 = pyo.Var(domain = pyo.NonNegativeReals)
# model.x2 = pyo.Var(domain = pyo.NonNegativeReals)

# model.constraints = pyo.ConstraintList()
# model.constraints.add( model.x1 * 10 + 1 >= model.x2)
# model.constraints.add( model.x1*(0.2) + 4 >= model.x2)
# model.constraints.add( model.x1*(-0.2) + 6 >= model.x2)

# model.objective = pyo.Objective(rule = lambda model: model.x1 + model.x2*10, sense = pyo.maximize)

# solver = pyo.SolverFactory("glpk")
# # solver = pyo.SolverFactory("gurobi")

# result = solver.solve(model)

# print(result)
# print(model.x1(), model.x2())

# ------------------------------ #2

# bakery problem

# model = pyo.ConcreteModel(name = "Bakery")

# model.x1 = pyo.Var(name = "White Bread ", domain = pyo.NonNegativeReals)
# model.x2 = pyo.Var(name = "wheat bread", domain = pyo.NonNegativeReals)
# model.x3 = pyo.Var(name = "rye bread", domain = pyo.NonNegativeReals)

# model.constraints = pyo.ConstraintList()
# model.constraints.add(model.x1 * 0.5 + model.x2 * 0.8 + model.x3 * 0.6 <= 100)
# model.constraints.add(model.x1 * 1 + model.x2 * 1.2 + model.x3 * 0.8 <= 8)

# def my_model(model):
#     '''
#     Objective fucntion
#     x1 = white bread
#     x2 = wheat br ead
#     x3 = rye bread

#     2x1 + 3x2 + 1.5x3
#     '''
#     return (model.x1 * 2) + (model.x2 * 3) + (model.x3 * 1.5)

# model.objective = pyo.Objective(expr = my_model, sense = pyo.maximize)

# solver = pyo.SolverFactory("glpk")

# result = solver.solve(model)

# print(result)
# print(" white Bread: ", model.x1(), "\n", "Wheat Bread: ",model.x2(), "\n", "Rye Bread: ", model.x3(), "\n")

# print(model.pprint())