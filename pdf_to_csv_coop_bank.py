import re
import pdfplumber
import pandas as pd
from collections import namedtuple
from decimal import Decimal
from dateutil.parser import parse

path = ''
files = ['COOPBANK.']
line_re = re.compile(r'^\d{2}-[A-Z]{1}[a-z]{2}-\d{2} ')
line_res = re.compile(r'^\d{2}/\d{2}/\d{4}')
line_re1 = re.compile(r'^\d{2}/\d{2}/\d{4}')
line_re2 = re.compile(r'^\d{2}-[A-Z]{1}[a-z]{2}-\d{2}')
line_re3 = re.compile(r'^\d{2}-[A-Z]{1}[a-z]{2}-\d{4}')
line_reDate = re.compile(r"^(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/\d{4}$")
line_re4 = re.compile(r'^\d{2}-[A-Z]{1}[a-z]{2}-')
line_re5 = re.compile(r'^\d{2}-\d{2}-\d{4}')
regex = re.compile(r'^\d{0,4}')
balance_re = re.compile(r'Brought forward Balance')
end_re = re.compile(r'TOTAL VALUE')
endings_re = re.compile(r'"End of Statement"')

ignore_list = [
	"Transaction", "Page", "Opening", 'Value', "Branch", "Currency", "Account",
	"Total", "Closing", "n Date", "Swift Code", "OVERDRAFT FACILITY DETAILS :",
	"TOTAL VALUE", "CLEAR BALANCE AS ON", "End of Statement", "Overdraft Review",
	"Overdraft Limit", "BOOK BALANCE AS ON", "Kindly examine this statement immediately",
	"could change if there are transactions that still need to be processed", "Interest Rate up to", "CONFIDENTIAL",
	"Any communication intimating disagreement with the statement",
	"Failing receipt by the Bank within 15 Days from the day of dispatch",
	"BOOK BALANCE AS AT", "UNCLEARED BALANCE AS AT", "opening balance " "to", "Balance"
]

pass_list = [
					"Kindly examine this statement immediately. Any discrepancies",
					"could change if there are transactions", "CLEAR BALANCE AS ON", "Overdraft Review",
					"BOOK BALANCE AS ON", "TOTAL VALUE", "OVERDRAFT FACILITY DETAILS",
					"Overdraft Limit", "End of Statement", "Interest Rate up to",
					"Failing receipt by the Bank within 15 Days from the day of dispatch"
				]

def parse_date(d):
	"""Return a proper date"""
	try:
		if str(d).__contains__("-"):
			dd = parse(d, dayfirst=True)
			return dd
	except Exception as e:
		return None


def date_extender(desc, reader, ind):
	try:
		k = ind
		m = 1
		while m < 2:
			k += 1
			if regex.search(reader[k].strip()):
				desc += "" + str(regex.search(reader[k]).group(0))
				m += 1
	except Exception as e:
		pass
	return str(desc)


def header_data_extraction(df, **kwargs):
	header = {
		"AccountType": "", "StatementDate": "", "StatementStartDate": "", "StatementEndDate": "",
		"Branch": "", "AccountNo": "", "Currency": "", "AccountOwner": "",
		"Opening Balance": kwargs.get("	opening_balance"), "Opening Balance": kwargs.get("closing_balance"), "PostalAddress": "",
		"AccountEmail": "", "CustomerPhoneNumber": ""}
	line_count = -1
	v = 1
	version = False
	if df.index[-1] > 3:
		if df['DESCRIPTION'][1] == "STATEMENT OF ACCOUNT":
			v = 2
		elif df['DESCRIPTION'][1] == "Account":
			v = 3
	not_found_start = True
	count = -1
	v2 = False
	for row in df['DESCRIPTION']:
		got = False
		row = row.strip()
		count += 1
		try:
			line_count += 1
			if str(row).__contains__("Interim Statement"):
				v2 = True
			if str(row).startswith("Account Type"):
				header["AccountType"] = str(row)
			elif str(row).startswith("Statement Date"):
				header["StatementDate"] = str(row).split("Statement Date ")[1]
			elif str(row).startswith("Statement Period "):
				header["StatementStartDate"] = str(row).split("Statement Period ")[1].split("to")[
					0].strip()
				header["StatementEndDate"] = str(row).split("to")[1].strip()
			elif str(row).startswith("Branch") and str(df.index[count]) == "5":
				header["Branch"] = str(row).split("Branch")[1].strip()
			elif str(row).startswith("Account No"):
				header["AccountNo"] = str(row).split("Account No ")[1].strip()
			elif str(row).startswith("Account Number:"):
				header["AccountNo"] = str(row).split(":")[1].strip()
			elif str(row).startswith("Currency"):
				header["Currency"] = str(row).split("Currency")[1].strip()
			elif str(row).startswith("Account Type"):
				header["AccountType"] = str(row).split("Account Type")[1].strip()
			elif str(row) != "" and str(df.index[count]) == "0" and not v2:
				header["AccountType"] = str(row).replace("'", "").strip()
			elif str(row).startswith("Total Debit Amount"):
				header["TotalDebit"] = str(row).split("Total Debit Amount")[1].strip()
			elif str(row).startswith("Total Credit Amount"):
				header["TotalCredit"] = str(row).split("Total Debit Amount")[1].strip()
			elif str(row).startswith("Currency"):
				header["Currency"] = str(row).split("Currency")[1].strip()
			elif str(row).startswith("Account No"):
				header["AccountNo"] = str(row).split("Account No")[1].strip()
			elif header.get("AccountOwner") == "" and str(row) != "":
				if str(df.index[count]) == "7":
					header["AccountOwner"] = str(row).replace("'", "").strip()
				if str(df.index[count]) == "9":
					header["AccountOwner"] = str(row).replace("'", "").strip()
			elif str(row).startswith("Opening Balance"):
				header["Opening"] = str(row).split("Opening Balance")[1].strip()
			elif str(row).startswith("Closing Balance"):
				header["Closing"] = str(row).split("Closing Balance")[1].strip()
			elif str(row) != "" and str(df.index[count]) == "11" and not v2:
				header["CustomerPhoneNumber"] = str(row).replace("'", "").strip()
			elif str(row).startswith("Branch Name"):
				header["Branch"] = str(row).split("Branch Name")[1].replace(":", " ").strip()
			elif header.get('AccountType') == "":
				if df.index[count] == '12' and row != "":
					header["AccountType"] = str(row).strip()
			if v2 and str(df.index[count]) == "4":
				header["AccountOwner"] = str(row).strip()
			continue

		except Exception as e:
			print(e)
			pass
	print(f"header {header}")
	return header


def desc_extender(desc, reader, ind):
	try:
		k = ind
		m = True
		while m:
			k += 2
			if not line_re.search(reader[k]) and not line_re1.search(reader[k]) \
					and not line_re2.search(reader[k]) and not line_re3.search(reader[k]) \
					and not line_re4.search(reader[k]) and not line_re5.search(reader[k]) \
					and not line_re5.search(reader[k]) and not line_res.search(reader[k]):
				if any(reader[k].__contains__(c) for c in ignore_list):
					continue
				desc += " " + str(reader[k]).strip()
			else:
				m = False
	except Exception as e:
		pass
	return str(desc).replace("'", "")


for filex in files:
	file = path + filex + "pdf"
	lines = []
	val = Decimal()
	is_table_found = False
	header_data = []
	opening_balance = Decimal()
	closing_balance = Decimal()
	table_sub_lines = []
	v2 = False
	v3 = False
	end_found = False
	with pdfplumber.open(file) as pdf:
		pages = pdf.pages
		Line = namedtuple('Line', 'TXN_DATE VALUE_DATE DESCRIPTION MONEY_OUT_OR_IN LEDGER_BALANCE TRX_TYPE')
		for page in pdf.pages:
			text = page.extract_text()
			text_list = text.split('\n')
			text_index = -1
			for line in text_list:
				if line.startswith("Transaction Statements"):
					v3 = True
			if v3:
				if not is_table_found:
					for line in text_list:
						if line.startswith("Posting Date"):

							lines.append(Line(
								'TXN_DATE', 'VALUE_DATE', 'DESCRIPTION', 'MONEY_OUT_OR_IN', 'LEDGER_BALANCE',
								'TRX_TYPE'))
							is_table_found = True
							table_lines = page.extract_table()
							table_sub_lines.extend(table_lines)
							break
						else:
							header_data.append(Line("", "", line, "", "", ""))
				else:

					table_lines = page.extract_table()
					if table_lines:
						table_sub_lines.extend(table_lines)

			else:
				text_list = text.split('\n')
				text_index = -1

				for line in text_list:
					text_index += 1
					items = line.split()
					if not is_table_found:
						if line.startswith("TRANS DATE") or line.startswith("Number") \
								or line.startswith("Transaction Details") or line.startswith("n Date"):
							lines.append(Line(
								'TXN_DATE', 'VALUE_DATE', 'DESCRIPTION', 'MONEY_OUT_OR_IN', 'LEDGER_BALANCE',
								'TRX_TYPE'))
							is_table_found = True
						else:
							header_data.append(Line("", "", line, "", "", ""))

					if any(line.lower().__contains__(x) for x in ["opening balance", "brought forward balance"]):
						# opening_balance = Decimal(line.lower().split("cr")[0].split(" ")[-2].strip().split(" CR ")[-2].replace(",", ""))

						if balance_re.search(line):
							TXN_DATE = "%s" % items[0]
							REFERENCE = "Brought forward Balance"
							if len(items) == 5:
								v2 = True
								items_last_index = items[-1].lower().split("cr")[0].split("dr")[0].replace(",", "")
								LEDGER_BALANCE = Decimal(items_last_index)
								TRX_TYPE = "CR" if line.lower().endswith("cr") else "DR"
							else:
								LEDGER_BALANCE = Decimal(items[-2].replace(",", ""))
								TRX_TYPE = items[-1].strip()
							val = LEDGER_BALANCE
							val = val if TRX_TYPE == "CR" else -val
							lines.append(Line(TXN_DATE, "", REFERENCE, "", LEDGER_BALANCE, TRX_TYPE))
							continue
					elif line.__contains__("closing balance"):
						closing_balance = Decimal(line.lower().split()[-1].replace(",", ""))
						continue
					if end_re.search(line):
						header_data.append(Line("", "", line, "", "", ""))
						end_found = True
						continue
					if end_found or endings_re.search(line):
						header_data.append(Line("", "", line, "", "", ""))
						continue
					if line_re2.search(line) and not v3:
						try:
							TXN_DATE = items[0]
							VALUE_DATE = items[-4]
							if len(items) > 5 and not line_re2.search(items[1]):
								desc = " ".join(items[1: -5])
							elif len(items) > 5 and not line_re2.search(items[1]):
								desc = " ".join(items[1:-2])
							DESCRIPTION = desc_extender(desc, text_list, text_index)
							MONEY_OUT_OR_IN = items[-3]
							LEDGER_BALANCE = items[-2]
							TRX_TYPE = "DR" if Decimal(LEDGER_BALANCE.replace(",", "")) < val else "CR"
							val = Decimal(LEDGER_BALANCE.replace(",", ""))
							lines.append(
								Line(TXN_DATE, VALUE_DATE, DESCRIPTION, MONEY_OUT_OR_IN,
								     LEDGER_BALANCE, TRX_TYPE))
						except Exception as e:
							pass






	df = pd.DataFrame(header_data)
	k = {"opening_balance": opening_balance, "closing_balance": closing_balance}
	header_list = []
	for key, value in header_data_extraction(df, **k).items():
		header_list.append(Line("", "", ''.join([key, ":", str(value)]), "", "", ""))
	final_list = header_list + lines
	df = pd.DataFrame(final_list)
	df.to_csv(path + filex + 'csv')
