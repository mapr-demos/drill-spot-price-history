#!/usr/bin/python

from datetime import datetime
from datetime import timedelta
import subprocess
import os

start_date = datetime(2015,2,1)
end_date = datetime.today()

# aws ec2 describe-spot-price-history --start-time $(date +%Y-%m-$start_day) --end-time $(date +%Y-%m-$end_day)

command_tmpl = "aws ec2 describe-spot-price-history --start-time %s --end-time %s"

date = start_date
while date < end_date:
	start_date_str = date.strftime("%Y-%m-%d")
	end_date_str = (date+timedelta(days=1)).strftime("%Y-%m-%d") 
	
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
			f.write(output)
	print "done"
	date+=timedelta(days=1)
