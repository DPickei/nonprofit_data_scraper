# nonprofit_data_scraper

This tool automates the collection of various data points across nonprofit public filings (990s)

User enters EIN (nonprofit ID), program outputs csv/db file of personnel information of the board for each EIN


# Data points collected:

  - "name": The name of the board member
  - "city": The city in which the associated nonprofit is filed from
  - "state": The state in which the associated nonprofit is filed from
  - "hours_per_week": The hours worked per week by the board member
  - "years_involved": A comma delimited list of years in which the board member has been with the organization
  - "title": The most recent title held by the board member
  - "organization_name": The name of the nonprofit
  - "ein": The EIN of the organization. This is a unique ID assigned to all recognized nonprofits

_Note  The columns above represent data points currently collected. However, any element within the 990 XML files can be collected._


# Why was this tool made?

This tool was made to execute bulk parsing of nonprofit data not available from the provided [ProPublica API](https://projects.propublica.org/nonprofits/api)

The ProPublica API has a rate limit on the amount of requests that can be made, and limited details on each nonprofit. 
This tool, in conjuction with the required XML files downloaded (see below), offers a much higher degree of customization of data that the user can collect. Almost any attribute a nonprofit disclosed can be aggregated with this tool.


# How to run the code:
1. Populate user input values of assumptions.py

2. execute 'python folder_initialization.py'

3. Download desired years of 990 data from [here](https://www.irs.gov/charities-non-profits/form-990-series-downloads) into 'nonprofit_raw_data > xml_files'. Ignore 'Index file for YYYY (CSV)'.

4. Execute 'object_id_to_zip_address_database_maker'

5. Execute main.py with desired nonprofit EINs in a .db file or manually entered.