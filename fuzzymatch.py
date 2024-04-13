#TO DO - refactor to not use Google Sheets

#import fuzzywuzzy
import fuzzywuzzy.fuzz
import fuzzywuzzy.process
import gspread
import pandas as pd

google_sheet_name = "Example spreadsheet"
data_to_fuzzymatch_worksheet = "DirtyList"
data_to_fuzzymatch_column_index = 2 #column number of the dirty data to fuzzymatch (remember to start counting at 0)
accepted_values_worksheet = "CleanCompanyNames" #name of the worksheet with the accepted values
accepted_values_column_index = 0 #column number of the accepted values(remember to start counting at 0)


def open_google_sheet(google_sheet_name): #returns sheet object (sh)
    gc = gspread.oauth(
    credentials_filename='INSERT_CREDENTIALS_FILENAME_HERE',)
    sh = gc.open(google_sheet_name)
    return sh
def get_dataframe_from_google_sheet(sh, worksheet_name): #returns dataframe with all value from worksheet
    worksheet = sh.worksheet(worksheet_name)
    data = worksheet.get_all_values()
    #count number of columns
    num_columns = len(data[0])
    #headers = data.pop(0)#remove first row and save as headers
    #if data doesn't have headers, use this line instead:
    #create headers going from column1 to columnX
    headers = ['column'+str(i) for i in range(1, num_columns+1)]
    df = pd.DataFrame(data, columns=headers)
    return df
def fuzzy_match(dirty_list, accepted_list): #returns best match from accepted list for each item in dirty list
    matched_list = []
    for item in dirty_list:
        match = fuzzywuzzy.process.extractOne(item, accepted_list)
        if match:
            matched_list.append([match[0], match[1]])
        else:
            matched_list.append(['No Match',''])
    print('length of matched list: ')
    print(len(matched_list))
    return matched_list
def open_google_sheet_in_browser(worksheet_url): #opens google sheet in web browser
    import webbrowser
    webbrowser.open(worksheet_url)
    return 


##### Get data to fuzzymatch from google sheet
sheet = open_google_sheet(google_sheet_name)
dirty_dataframe = get_dataframe_from_google_sheet(sheet, data_to_fuzzymatch_worksheet)
# get names to fuzzymatch from correct column of the dataframe
dirty_company_list = dirty_dataframe.iloc[:, data_to_fuzzymatch_column_index]
#print(dirty_company_list)

##### Get accepted company list from google sheet
accepted_dataframe = get_dataframe_from_google_sheet(sheet, accepted_values_worksheet)
accepted_company_list = accepted_dataframe.iloc[:, accepted_values_column_index]

##### fuzzy match the two lists
matched_list = fuzzy_match(dirty_company_list, accepted_company_list)

##### create dataframe from matched list
matched_list = pd.DataFrame(matched_list, columns=['Matched Company Name', 'Match Confidence'])
print(matched_list)
#####add matched list dataframe to dirty dataframe
dirty_dataframe = pd.concat([dirty_dataframe, matched_list], axis=1)
print(dirty_dataframe)

##### save dataframe to new worksheet
worksheet_name = "Matched_Company_Names" + time.strftime("%Y%m%d")
worksheet = sheet.add_worksheet(worksheet_name, rows="1000", cols="20")
worksheet.update([dirty_dataframe.columns.values.tolist()] + dirty_dataframe.values.tolist())
worksheet_url = worksheet.url

##### open_google_sheet(worksheet.url)
open_google_sheet_in_browser(worksheet_url)

