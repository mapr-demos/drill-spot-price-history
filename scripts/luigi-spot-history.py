#!/usr/bin/env python

from datetime import datetime
from datetime import timedelta
import subprocess
import os
import errno
import json

import luigi

class SpotHistory(luigi.Task):
	destination = luigi.Parameter(default="/tmp/spot-price-history")
	regions = [ 
		"eu-central-1",
		"sa-east-1",
		"ap-northeast-1",
		"eu-west-1",
		"us-east-1",
		"us-west-1",
		"us-west-2",
		"ap-southeast-2",
		"ap-southeast-1" ]

	def requires(self):
		return [ SpotHistoryByRegion(destination=self.destination, region=r) for r in self.regions ]

class SpotHistoryByRegion(luigi.Task):
	history_start_date = luigi.DateParameter(default=(datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"))
	region = luigi.Parameter(default="us-east-1")
	destination = luigi.Parameter(default="/tmp/spot-price-history")

	def run(self):
		with self.output().open("w") as f:
			self.write_history_file(f)

	def output(self):
		the_date = self.history_start_date
		the_region = self.region
		output_path = os.path.join(self.destination, '%s' % the_region, '%s' % the_date, 'history.json')
		try:
			os.makedirs(os.path.dirname(output_path))
		except OSError, e:
			if e.errno == errno.EEXIST:
				pass
			else:
				raise

		return luigi.LocalTarget(output_path)

	def write_history_file(self, fileobj):
		command_tmpl = "aws --region %s ec2 describe-spot-price-history --start-time %s --end-time %s"
		start_date = self.history_start_date
		end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

		command = command_tmpl % (self.region, start_date, end_date)
		args = command.split(' ')
		output = subprocess.check_output(args)
		if len(output) > 0:
			try:
				data = json.loads(output)
			except ValueError:
				raise
			for row in data['SpotPriceHistory']:
				fileobj.write("%s\n" % json.dumps(row))

if __name__ == '__main__':
    luigi.run(main_task_cls=SpotHistory)
