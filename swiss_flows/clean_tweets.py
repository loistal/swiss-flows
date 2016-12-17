import pandas as pd
import numpy as np
import os
import csv
import sys

def main(args):

	# Load the dirty tweets
	# Taken from Slack: https://adaepfl.slack.com/archives/twitter/p1480527805000002
	data_path = os.path.dirname('__file__') + '../data/twitter-swisscom/sample.tsv'
	df = pd.read_csv(data_path, sep="\t",encoding='utf-8',  quoting=csv.QUOTE_NONE, header=None, na_values='\\N')

	# Load the schema
	schema_path = os.path.dirname('__file__') + '../data/twitter-swisscom/schema.txt'
	schema = pd.read_csv(schema_path, delim_whitespace=True, header=None)
	schema.drop([9], inplace=True)

	# Assign column names
	df.columns = schema[1]

	# Keep only the useful columns
	useful_col = ['id', 'userId', 'createdAt', 'placeLongitude', 'placeLatitude', 'userLocation']
	df = df[useful_col]

	# Drop rows which have missing values in important columns
	imp_col = ['userId', 'createdAt', 'placeLatitude', 'placeLatitude']
	df = df.dropna(subset=imp_col, how='any')

	# Correct format of palceLatitude column
	df['placeLatitude'] = df['placeLatitude'].apply(remove_t)

	# Write in a file
	name = args[1]
	df.to_csv(name + '.csv')


def remove_t(place_latitude):
    	return place_latitude.replace('\t', '')	

if __name__ == '__main__':
    main(sys.argv)
