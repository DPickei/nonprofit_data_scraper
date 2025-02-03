# nonprofit_data_scraper

This tool automates the collection of various data points across nonprofit public filings (990s)

User enters EIN (nonprofit ID), the program creates a csv/db file of personnel information for the board for each EIN. 

See "outputs / csv_outputs / sample_csv_output.csv" for an example of this output.


# Data points collected:
  - "ein": EIN of the organization
  - "person_name": The name of the board member
  - "city": The city in which the associated nonprofit is filed from
  - "state": The state in which the associated nonprofit is filed from
  - "hours_per_week": The hours worked per week by the board member
  - "years_of_service": A comma delimited list of years in which the board member has been with the organization
  - "title": The most recent title held by the board member
  - "organization_name": The name of the nonprofit

_Note  The columns above represent data points currently collected. However, any element within the 990 XML files can be collected._


# Why was this tool made?

This tool was made to allow for comprehensive collection of data nonprofits disclose.

The existing [API](https://projects.propublica.org/nonprofits/api) from [ProPublica](https://www.propublica.org/) carries two restrictions that served as inspiration for the creation of this tool.

1. Rate limits on the amount of requests that can be made

2. Limited elements can be captured by the API. Parsing the XML files directly allows the user to filter and collect 990 data based on any attribute a nonprofit discloses in their 990.


# How to run the code:

0. Install dependencies into a virtual environment

1. Download desired years of 990 data  
  - Download from [here](https://www.irs.gov/charities-non-profits/form-990-series-downloads)  
  - Download into 'nonprofit_raw_data > xml_files'  
  - Note: No need to download 'Index file for YYYY (CSV)'  

2. Populate config values  
  - ein_list: EINs of organizations you wish to gather data from. To find the EIN of an organization, use [this](https://projects.propublica.org/nonprofits/) search page  
  - max_hours_filter: Maximum number of hours a person can have. This filter exists because board members will usually work under 40 hours and full-time employees will usually work about 40, so this filter allows us to differentiate between the two roles in some approximate way.  

3. Execute main.py  
  - Note: On the first execution of main.py, a function will be triggered to create a database, which may take some time to complete.
