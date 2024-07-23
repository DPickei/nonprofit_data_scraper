# nonprofit_data_scraper

This tool automates the collection of various data points across nonprofit public filings (990s)

User enters EIN (nonprofit ID), the program creates a csv/db file of personnel information for the board for each EIN. 

See "outputs / csv_outputs / sample_csv_output.csv" for an example of this output.


# Data points collected:

  - "person_name": The name of the board member
  - "city": The city in which the associated nonprofit is filed from
  - "state": The state in which the associated nonprofit is filed from
  - "hours_per_week": The hours worked per week by the board member
  - "years_of_service": A comma delimited list of years in which the board member has been with the organization
  - "title": The most recent title held by the board member
  - "organization_name": The name of the nonprofit

_Note  The columns above represent data points currently collected. However, any element within the 990 XML files can be collected._


# Why was this tool made?

This tool was made to allow for convenient collection of data nonprofits disclose.

The existing [API](https://projects.propublica.org/nonprofits/api) from [ProPublica](https://www.propublica.org/) carries two restrictions that served as inspiration for the creation of this tool.

1. Rate limits on the amount of requests that can be made

2. Limited elements can be captured by the API. Parsing the XML files directly allows the user to filter and collect 990 data based on any attribute a nonprofit discloses in their 990.


# How to run the code:
1. Populate user input values of assumptions.py

2. Execute 'python folder_initialization.py'

3. Download desired years of 990 data [here](https://www.irs.gov/charities-non-profits/form-990-series-downloads) into 'nonprofit_raw_data > xml_files'. Ignore 'Index file for YYYY (CSV)'.

4. Execute 'object_id_to_zip_address_database_maker'

5. Execute main.py with desired nonprofit EINs in a .db file or manually entered.