import pandas as pd
from glob import glob


from tools.helper_func import add_data_2_html


ROOT_DIR = '/home/jinzhu'

# Get all html files needs data insertion
html_df = pd.DataFrame([['production',f"{ROOT_DIR}/VIS_LUTO_JS/pages/production_profit.html"],
                        ["area",f"{ROOT_DIR}/VIS_LUTO_JS/pages/area_change.html"],
                        ["GHG",f"{ROOT_DIR}/VIS_LUTO_JS/pages/GHG Emmisions.html"],
                        ["water",f"{ROOT_DIR}/VIS_LUTO_JS/pages/water_usage.html"]])

html_df.columns = ['name','path']

# Append data files to html files
all_data_files = glob(f"{ROOT_DIR}/VIS_LUTO_JS/data/*")
all_data_files = [i for i in all_data_files if 'html' not in i]
html_df['data_path'] = html_df.apply(lambda x: [i for i in all_data_files if x['name'] in i ],axis=1)


# Parse html files
for idx,row in html_df.iterrows():
    
    html_path = row['path']
    data_pathes  = row['data_path']

    # Add data to html
    add_data_2_html(html_path,data_pathes)