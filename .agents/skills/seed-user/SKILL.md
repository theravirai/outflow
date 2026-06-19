---
name: seed-user
description: Create a single dummy user in the database
allowed-tools: Read, Bash(python3:*)
---

Read database/db.py to understand the users table
schema and the get_db() helper.

Then write and run a Python script using Bash that:

1. Generates a realistic random user commonly found in Germany:

   * Name: choose a first and last name from commonly used
     German names (for example: Anna, Lukas, Leon, Emma,
     Sophie, Müller, Schmidt, Wagner, Becker, Fischer)
   * Email: derived from the name with a random 2-3 digit
     suffix (e.g. [anna.mueller91@gmail.com](mailto:anna.mueller91@gmail.com))
   * Password: "password123" hashed with werkzeug's
     generate_password_hash
   * created_at: current datetime

2. The generated names should represent realistic residents
   of Germany and may include diverse backgrounds commonly
   found in modern Germany.

3. Check if the generated email already exists in the
   users table. If it does, regenerate until unique.

4. Insert the user into the database using the same
   get_db() pattern found in db.py.

5. Print confirmation:

   * id
   * name
   * email