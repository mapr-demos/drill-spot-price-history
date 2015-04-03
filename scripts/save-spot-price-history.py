#!/usr/bin/python

from datetime import datetime
from datetime import timedelta
import subprocess
import os
import json

def write_history_file(region, start_date, end_date, dir, filename):
	command_tmpl = "aws --region %s ec2 describe-spot-price-history --start-time %s --end-time %s"
	tmp_path = os.path.join(dir, "_%s" % filename)
	path = os.path.join(dir, filename)

	if not os.path.exists(path):
		with file(tmp_path, "w") as f:
			command = command_tmpl % (region, start_date, end_date)
			args = command.split(' ')
			output = subprocess.check_output(args)
			if len(output) > 0:
				try:
					data = json.loads(output)
				except ValueError:
					raise
				for row in data['SpotPriceHistory']:
					f.write("%s\n" % json.dumps(row))
		try:
			os.rename(tmp_path, path)
		except OSError as e:
			raise	
		print "done"


def main():
	start_date = datetime.today() - timedelta(days=90)
	end_date = datetime.today() - timedelta(days=1)
	regions = [ "eu-central-1","sa-east-1","ap-northeast-1","eu-west-1","us-east-1","us-west-1","us-west-2","ap-southeast-2" ]
	"ap-southeast-1"

	date = start_date
	while date < end_date:
		start_date_str = date.strftime("%Y-%m-%dT%H:%M:%S")
		end_date_str = (date + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S") 

		dir = os.path.join("history", str(date.year), "%02d" % date.month, "%02d" % date.day)
		try:
			os.makedirs(dir)
		except OSError as e:
			if e.errno == 17:
				pass

		for region in regions:
			print "%s: %s " % (dir, region)
			write_history_file(region, start_date_str, end_date_str, dir, "%s-prices.json" % region)
		date+=timedelta(days=1)

if __name__ == "__main__": main()
