#!/bin/bash
# Read username and password
read -r -p "username: " username
read -r -s -p "password: " password
echo

# Default URL
default_url="https://unb.ca/"

# Read URL with default option
read -r -p "URL [${default_url}]: " url
url=${url:-$default_url} # If no URL is entered, use the default URL.

echo "Using URL: $url"

# Login
echo "Logging in..."
curl -i -H "Content-Type: application/json" -X POST -d '{"username": "'$username'", "password": "'$password'"}' -b cookie-jar -c cookie-jar -k https://cs3103.cs.unb.ca:8042/login

# Show user links
echo "Here is the list of link you have:"
curl -i -H "Content-Type: application/json" -X GET -b cookie-jar -k https://cs3103.cs.unb.ca:8042/user/links

# Create shortcut for a link
echo "Creating a new shortcut..."
curl -i -H "Content-Type: application/json" -X POST -d '{"destination": "'$url'"}' -b cookie-jar -k https://cs3103.cs.unb.ca:8042/user/links

# Show user links again
echo "Here is the list of link you have, after adding the new link:"
curl -i -H "Content-Type: application/json" -X GET -b cookie-jar -k https://cs3103.cs.unb.ca:8042/user/links

# Extract linkId and shortcut of the created link
echo "Retrieving linkId and shortcut of the created link..."
links_json=$(curl -s -H "Content-Type: application/json" -X GET -b cookie-jar -k https://cs3103.cs.unb.ca:8042/user/links)
link_id=$(echo "$links_json" | jq '.[-1].linkId')
shortcut=$(echo "$links_json" | jq -r '.[-1].shortcut')
echo "linkId: $link_id"
echo "shortcut: $shortcut"

echo "Visit the shortcut..."
echo "You can also visit it on a browser; it should redirect you to the destination full URL:"
echo "https://cs3103.cs.unb.ca:8042/$shortcut"
curl -i -H "Content-Type: application/json" -X GET -k "https://cs3103.cs.unb.ca:8042/$shortcut"

# Ask user if they want to delete the link
read -p "Do you want to delete the last created link? (y/n): " confirm
if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    echo "Deleting the link with linkId: $link_id..."
    curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k "https://cs3103.cs.unb.ca:8042/user/links/$link_id"
else
    echo "The link will not be deleted."
fi

# Logout
echo "Logging out..."
curl -i -H "Content-Type: application/json" -X DELETE -b cookie-jar -k https://cs3103.cs.unb.ca:8042/logout
echo "You have been logged out."
