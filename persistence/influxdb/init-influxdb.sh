#!/bin/bash

# This script initializes the InfluxDB database for the model train control system.

# Set the InfluxDB database name
DB_NAME="model_train_db"

# Create the database
influx -execute "CREATE DATABASE $DB_NAME"

# Create retention policy
influx -execute "CREATE RETENTION POLICY \"one_year\" ON \"$DB_NAME\" DURATION 365d REPLICATION 1 DEFAULT"

# Create continuous queries or any other setup as needed
# influx -execute "CREATE CONTINUOUS QUERY ..."

echo "InfluxDB initialized with database: $DB_NAME"
