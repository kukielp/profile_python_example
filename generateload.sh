#!/bin/bash

START_DATETIME=$(date +%s)

COUNT=10000

for i in $(seq 1 $COUNT); do
    echo "> Running #$i from ${COUNT}... "
    sleep .1
    #curl --location --request GET 'https://ut2stg6wge.execute-api.ap-southeast-2.amazonaws.com/Prod/lists' --header 'Authorization: Bearer 12345'

    result=$(curl -s --location --request GET 'https://wqk1lztjea.execute-api.ap-southeast-2.amazonaws.com/Prod/lists' --header 'Authorization: Bearer 12345')

    echo "${result}" | jq '.[] .listId' |
    while IFS=$"\n" read -r c; do
        list=$(echo "$c" | sed 's/"//g')
        url="curl -s --location --request GET 'https://wqk1lztjea.execute-api.ap-southeast-2.amazonaws.com/Prod/lists/$list' --header 'Authorization: Bearer 12345'" 
        r=$(eval $url)
        echo "${r}" | jq
        curl -s --location --request GET 'https://wqk1lztjea.execute-api.ap-southeast-2.amazonaws.com/Prod/wavefile' &
    done
    #n=$(( ( RANDOM % 10 )  + 1 ))
    #urlFib="curl -s --location --request GET 'https://wqk1lztjea.execute-api.ap-southeast-2.amazonaws.com/Prod/fib/$n'"
    #echo $urlFib
    
    curl -s --location --request GET 'https://wqk1lztjea.execute-api.ap-southeast-2.amazonaws.com/Prod/fib/'$(( ( RANDOM % 10 )  + 1 )) &
    
    result=$(curl -s --location --request GET 'https://wqk1lztjea.execute-api.ap-southeast-2.amazonaws.com/Prod/check' --header 'Authorization: Bearer 12345')
    echo "${result}" | jq 

done

END_DATETIME=$(date +%s)
RUNTIME=$((END_DATETIME - START_DATETIME))

echo "> Duration: ${RUNTIME} seconds ($((RUNTIME / 60)) minutes)"