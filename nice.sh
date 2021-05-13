#!/bin/bash

result=$(curl -s --location --request GET 'https://brirwhx7ue.execute-api.ap-southeast-2.amazonaws.com/Prod/lists' --header 'Authorization: Bearer 12345')

echo "${result}" | jq '.[] .listId' |
while IFS=$"\n" read -r c; do
    list=$(echo "$c" | sed 's/"//g')
    url="curl -s --location --request GET 'https://brirwhx7ue.execute-api.ap-southeast-2.amazonaws.com/Prod/lists/$list' --header 'Authorization: Bearer 12345'"
    r=$(eval $url)
    echo "${r}" | jq
done