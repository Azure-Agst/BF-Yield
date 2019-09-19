# BF-AFK-Yield.py
# Copyright (C) 2019 Andrew "Azure-Agst" Augustine
# (...Does a file this small even warrant a copyright? Lmao.)

# Imports
import math
import os

# Clear Console
os.system('cls')

# Title
print("Destiny 2 BF-AFK Yield Calculator v1.0")
print("Copyright (C) 2019 Azure-Agst")

# User Input
planet = int(input("\nHow much Dusk/Data? "))

# Engrams
engrams = math.floor(planet/55)
print("\n - Engrams:", engrams)

# Shards
minshards = engrams*6
maxshards = engrams*10
print(" - LShards: [Min: {}, Max: {}, Est: {}]".format(minshards, maxshards, engrams*8))

# Curated Drops
curated = round(engrams/10) # 10% is an estimated value based of my IRL stats
print(" - Curated rolls:", curated)

# Pause to end
input("\nPress any key to exit...")

