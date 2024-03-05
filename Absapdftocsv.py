import re
import pdfplumber
from write_csv_file import write_csv

headers = {
    "Postal Address": '',
    "Branch Name": '',
    "Account Number": '',
    "Currency": '',
    "Start Date": '',
    "End Date": '',
    "Uncleared Balance": '',
    "Opening Balance": '',
    "Closing Balance": '',
    "Total Debit Amount": '',
    "Total Credit Amount": ''
}

transaction_date = list()
description = list()
debit = list()
credit = list()
balance = list()

with pdfplumber.open("./107_42400487.pdf") as pdf:
    dates_set = False
    address_set = False
    for page in pdf.pages:
        page_text = page.extract_text().split("\n")
        for x in range(len(page_text)):
            line = page_text[x]
            print(line)

            # get start and end dates
            if line.startswith("From ") and not dates_set:
                dates = line.replace("From ", '').replace("To ", '').split(" ")
                headers['Start Date'] = dates[0]
                headers['End Date'] = dates[1]
                dates_set = True

            # get headers
            if line.startswith("P.O BOX") and not address_set:
                headers["Postal Address"] = "".join([str(line), ", ", str(page_text[x+2]), "-", str(page_text[x+4])])
                address_set = True
            elif line.startswith("Branch Name"):
                headers["Branch Name"] = str(line).split("Branch Name ")[1].strip()
            elif line.startswith("Account Number"):
                headers["Account Number"] = str(line).split("Account Number ")[1].strip()
            elif line.startswith("Currency"):
                headers["Currency"] = str(line).split("Currency ")[1].strip()
            elif line.startswith("Uncleared Balance"):
                headers["Uncleared Balance"] = str(line).split("Uncleared Balance: ")[1].strip()
            elif line.startswith("Opening Balance"):
                headers["Opening Balance"] = str(line).split("Opening Balance: ")[1].strip()
            elif line.startswith("Closing Balance"):
                headers["Closing Balance"] = str(line).split("Closing Balance: ")[1].strip()
            elif line.startswith("Total Debit Amount"):
                headers["Total Debit Amount"] = str(line).split("Total Debit Amount: ")[1].strip()
            elif line.startswith("Total Credit Amount"):
                headers["Total Credit Amount"] = str(line).split("Total Credit Amount: ")[1].strip()

            if re.search(r'^\d{2}/\d{2}/\d{4}', line):
                split_line = line.split()
                transaction_date.append(split_line[0])
                desc = " ".join(split_line[1: -3])
                if (x+1 in range(len(page_text))) and (not re.search(r'^\d{2}/\d{2}/\d{4}', page_text[x+1])) and (re.search(r'^\d{2}/\d{2}/\d{4}', page_text[x+2])):
                    desc = " ".join([desc, page_text[x+1]])
                description.append(desc)
                debit.append(split_line[-3])
                credit.append(split_line[-2])
                balance.append(split_line[-1])

write_csv(headers, ['Transaction Date', 'Description', 'Debit', 'Credit', 'Balance'], [transaction_date, description, debit, credit, balance], "absa")