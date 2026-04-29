from pymongo import MongoClient

# Replace with MongoDB i put on TEAMS
MONGO_URI = "mongodb+srv://<user>:<pws>@cluster0.wg80hfn.mongodb.net/"

client = MongoClient(MONGO_URI)

db = client["Urban_data_explorer"]

users_collection = db["users"]
counters_collection = db["counters"]

# # Insert sample user data
# users_data = [
#     {
#         "user_id": 1,
#         "name": "Alice",
#         "age": 25,
#         "city": "Paris",
#         "interests": ["fashion", "art", "data"]
#     },
#     {
#         "user_id": 2,
#         "name": "Bob",
#         "age": 30,
#         "city": "Lyon",
#         "interests": ["sports", "music"]
#     }
#  ]
#
# users_collection.insert_many(users_data)

# -------------------
# # Insert sample counter data
# counter_data = {
#     "page": "homepage",
#     "visits": 1
# }
#
# counters_collection.insert_one(counter_data)

print("Database and sample data created successfully!")
