#!/bin/bash
# Unhappy path tests for the API

# Read username and password
read -r -p "username: " username
read -r -s -p "password: " password
echo

# Login
echo "Logging in..."
curl -i -H "Content-Type: application/json" -X POST -d '{"username": "'$username'", "password": "'$password'"}' -b cookie-jar -c cookie-jar -k https://cs3103.cs.unb.ca:8042/login

# Login again
echo "Logging in again..."
curl -i -H "Content-Type: application/json" -X POST -d '{"username": "'$username'", "password": "'$password'"}' -b cookie-jar -c cookie-jar -k https://cs3103.cs.unb.ca:8042/login

# Attempt to create a shortcut with an invalid URL
echo "Attempting to create a shortcut with an invalid URL..."
curl -i -H "Content-Type: application/json" -X POST -d '{"destination": "not_a_valid_url"}' -b cookie-jar -k https://cs3103.cs.unb.ca:8042/links

# Attempt to delete a non-existent link
echo "Attempting to delete a non-existent link..."
curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k https://cs3103.cs.unb.ca:8042/links/99999

# Create shortcut for a link
echo "Creating a new shortcut..."
curl -i -H "Content-Type: application/json" -X POST -d '{"destination": "https://unb.ca"}' -b cookie-jar -k https://cs3103.cs.unb.ca:8042/links
echo "Shortcut created."

# Extract linkId and shortcut of the created link
echo "Retrieving linkId and shortcut of the created link..."
links_json=$(curl -s -H "Content-Type: application/json" -X GET -b cookie-jar -k https://cs3103.cs.unb.ca:8042/links)
link_id=$(echo "$links_json" | jq '.[-1].linkId')
shortcut=$(echo "$links_json" | jq -r '.[-1].shortcut')

# Logout
echo "Logging out..."
curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k https://cs3103.cs.unb.ca:8042/logout
echo "You have been logged out."

# Attempt to delete a link without authentication
echo "Attempting to delete a link without authentication..."
echo "Deleting the link with linkId: $link_id..."
curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k "https://cs3103.cs.unb.ca:8042/links/$link_id"

# Invalid login credentials
echo "Attempting to log in with invalid credentials..."
curl -i -H "Content-Type: application/json" -X POST -d '{"username": "wrong_username", "password": "wrong_password"}' -c cookie-jar -k https://cs3103.cs.unb.ca:8042/login

echo "Attempting to log in with invalid JSON..."
curl -i -H "Content-Type: application/json" -X POST -d '{"username": "'$username'", "password": ' -b cookie-jar -k https://cs3103.cs.unb.ca:8042/login

# Attempt to aceess user links without being authenticated
echo "Attempting to access user links without authentication..."
curl -i -H "Content-Type: application/json" -X GET -b cookie-jar -k https://cs3103.cs.unb.ca:8042/links

# Logout without being authenticated
echo "Logging out without being authenticated"
curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k https://cs3103.cs.unb.ca:8042/logout

# Attempt to visit a non-existent shortcut
echo "Attempting to visit a non-existent shortcut..."
curl -i -H "Content-Type: application/json" -X GET -k "https://cs3103.cs.unb.ca:8042/999999"
