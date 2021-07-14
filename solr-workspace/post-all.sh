#!/bin/bash

find ./solr-occur/*.csv -exec post -c taibif_occurrence  {} \;
