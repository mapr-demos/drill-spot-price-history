#!/usr/bin/python

from datetime import datetime
from datetime import timedelta
import subprocess
import os
import json

start_date = datetime(2014,12,1)
end_date = datetime.today() - timedelta(days=1)

command_tmpl = "aws ec2 describe-spot-price-history --start-time %s --end-time %s"
date = start_date
while date < end_date:
	start_date_str = date.strftime("%Y-%m-%dT%H:%M:%S")
	end_date_str = (date + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S") 

	dir = os.path.join("data", str(date.year), "%02d" % date.month, "%02d" % date.day)
	print "%s: " % dir,
	try:
		os.makedirs(dir)
	except OSError as e:
		if e.errno == 17:
			pass

	path = os.path.join(dir, "prices.json")
	if not os.path.exists(path):
		print "creating",
		with file(path, "w") as f:
			command = command_tmpl % (start_date_str, end_date_str)
			args = command.split(' ')
			output = subprocess.check_output(args)
			if len(output) > 0:
				try:
					data = json.loads(output)
				except ValueError:
					raise
				for row in data['SpotPriceHistory']:
					f.write("%s\n" % json.dumps(row))
	print "done"
	date+=timedelta(days=1)
