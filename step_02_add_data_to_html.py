import os
from lxml import etree
import pandas as pd
from glob import glob
from lxml import etree
from lxml.etree import Element

from tools.helper_func import list_all_files


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
html_one = html_df['path'][0]
paths_one  = html_df['data_path'][0]


# Step 1: Parse the HTML file
parser = etree.HTMLParser()
tree = etree.parse(html_one, parser)

# Step 2: Find the target div
content_div = tree.xpath('.//div[@class="content"]')[0]

# Step 3: Create a new div element
new_div = Element("div",)
new_div.set("id", "data_csv")
new_div.set("style", "display: none;")

# Create and append five <pre> elements
for data_path in paths_one:
        
    # get the base name of the file
    data_name = os.path.basename(data_path).split('.')[0]
    
    with open(data_path, 'r') as file:
        raw_string = file.read()
    
    pre_element = etree.SubElement(new_div, "pre")
    pre_element.set("id", f"{data_name}_csv")
    pre_element.text = raw_string

    
    
    
# Step 4: Insert the new div
content_div.addnext(new_div)
    
# Step 5: Save the changes
tree.write(html_one, method="html")