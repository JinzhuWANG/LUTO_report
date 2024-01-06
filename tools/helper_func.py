from tools.PARAMETERS import GHG_CATEGORY, GHG_FNAME2TYPE, GHG_NAMES, LU_CROPS, LU_LVSTKS, LU_UNALLOW, NON_AG_LANDUSE


import pandas as pd


def sum_lvstk(path:str):
    
    """
    This function is used to sum the rows with the name of ['Beef', 'Dairy', 'Sheep'] into one row, individually

    Parameters:
    path (str): The input path of csv file.

    Returns:
    pandas.DataFrame: The output dataframe containing the data for different types of land use.
    """
    
    df = pd.read_csv(path,index_col=0,header=[0,1])
    # remove the last row and col
    df = df.iloc[:-1,:-1]
    # merge the rows with the name of ['Beef', 'Dairy', 'Sheep'] into one row, individually
    df_lvstk = df.loc[LU_LVSTKS]
    # splitting the index into two columns
    df_lvstk[['lu','land']] = df_lvstk.index.str.split('-').tolist()
    # sum the rows with the same land use
    df_lvstk = df_lvstk.groupby(['lu']).sum(numeric_only=True)
    # remove the rows with the name of ['Beef', 'Dairy', 'Sheep']
    df = df.drop(LU_LVSTKS,axis=0)
    # merge the df_lvstk into df
    df = pd.concat([df,df_lvstk])
    return df


def df_wide2long(df:pd.DataFrame):
    
    """
    This function is used to convert the wide dataframe into long dataframe

    Parameters:
    df (pandas.DataFrame): The input dataframe.

    Returns:
    pandas.DataFrame: The output dataframe containing the data for different types of land use.
    """

    # remove the last row and col, sum the rows of ['Beef', 'Dairy', 'Sheep']
    df = sum_lvstk(df)
    # flatten the multi-index column
    df.columns = ['='.join(col) for col in df.columns.values]
    # melt the dataframe
    df = df.reset_index(names='Source').melt(id_vars=['Source'], value_vars=df.columns[1:])
    # # split the column into two, and remove the original column
    df[['Irrigation','Type']] = df['variable'].str.split('=',expand=True)
    df['Type'] = df['Type'].str.replace('Revenue','Crop')
    # convert the value into billion
    df['value (billion)'] = df['value']/1e9
    df = df.drop(['variable','value'],axis=1)

    return df


# Get dataframe of Revenue V.S. Cost
def get_rev_cost(revenue_df,cost_df):
    """
    This function is used to get the dataframe of Revenue V.S. Cost

    Parameters:
    revenue_df (pandas.DataFrame): The input dataframe containing revenue data.
    cost_df (pandas.DataFrame): The input dataframe containing cost data.

    Returns:
    pandas.DataFrame: The dataframe containing revenue and cost data.
    """
    rev_source = revenue_df.groupby(['year', 'Source']).sum(numeric_only=True).reset_index()
    cost_source = cost_df.groupby(['year', 'Source']).sum(numeric_only=True).reset_index()

    rev_cost_source = rev_source.merge(cost_source, on=['year', 'Source'], suffixes=('_rev', '_cost'))

    # rename columns
    rev_cost_source = rev_cost_source.rename(columns={'value (billion)_rev': 'Revenue (billion)',
                                                    'value (billion)_cost': 'Cost (billion)'})
    # calculate profit
    rev_cost_source['Cost (billion)'] = -rev_cost_source['Cost (billion)']
    rev_cost_source['Profit (billion)'] = rev_cost_source['Revenue (billion)'] + rev_cost_source['Cost (billion)']

    rev_cost_all = rev_cost_source.groupby('year').sum(numeric_only=True).reset_index()

    # add two dummy columns for plotting the color of rev and cost
    rev_cost_all['rev_color'] = 'Revenue'
    rev_cost_all['cost_color'] = 'Cost'
    
    return rev_cost_all


def merge_LVSTK_UAALLOW(df):
    """
    Merges the dataframes for different land use types (crop, non-agricultural, low value stock, and unallowed) 
    into a single dataframe and returns it.

    Parameters:
    df (pandas.DataFrame): The input dataframe containing land use data.

    Returns:
    pandas.DataFrame: The merged dataframe containing land use data for different types of land use.
    """
    df_crop = df[[True if i in LU_CROPS else False for i in  df['Land use']]]

    df_ep = df[[True if i in NON_AG_LANDUSE else False for i in  df['Land use']]]

    df_unallow = df[[True if i in LU_UNALLOW else False for i in  df['Land use']]]
    # df_unallow.index = pd.MultiIndex.from_tuples(tuple(df_unallow['Land use'].str.split(' - ')))
    # df_unallow = df_unallow.groupby(level=0).sum(numeric_only=True).reset_index(names='Land use')

    df_lvstk = df[[True if i in LU_LVSTKS else False for i in  df['Land use']]]
    df_lvstk.index = pd.MultiIndex.from_tuples(tuple(df_lvstk['Land use'].str.split(' - ')))
    df_lvstk = df_lvstk.groupby(level=0).sum(numeric_only=True).reset_index(names='Land use')

    return pd.concat([df_crop,df_ep,df_lvstk,df_unallow]).reset_index(drop=True)


def get_xy_data(df):
    
    """
    This function is used to convert the wide dataframe into long dataframe

    Parameters:
    df (pandas.DataFrame): The input dataframe.

    Returns:
    pandas.DataFrame: The output dataframe containing the data for different types of land use.
    """
    
    val_xy = []
    for col in range(len(df.columns)):
        for row in range(len(df)):
            val_xy.append([col, len(df) - row, df.iloc[row,col]])

    return pd.DataFrame(val_xy)


def get_GHG_file_df(all_files_df):
        
    """
    This function is used to get the dataframe containing the GHG data.

    Parameters:
    all_files_df (pandas.DataFrame): The input dataframe containing the file paths.

    Returns:
    pandas.DataFrame: The dataframe containing the GHG data.
    """
    
    # Get only GHG_seperate files
    GHG_files = all_files_df.query('catetory == "GHG" and base_name != "GHG_emissions" and year_types == "single_year"').reset_index(drop=True)
    GHG_files['GHG_sum_t'] = GHG_files['path'].apply(lambda x: pd.read_csv(x,index_col=0).loc['SUM','SUM'])
    GHG_files = GHG_files.replace({'base_name': GHG_FNAME2TYPE})

    return GHG_files


# Check if the GHG type is valid
def get_GHG_subsector_files(all_files,GHG_type):
    
    """
    This function is used to get the dataframe containing the GHG data for the given GHG type.

    Parameters:
    GHG_files (pandas.DataFrame): The input dataframe containing the GHG data.
    GHG_type (str): The given GHG type.

    Returns:
    pandas.DataFrame: The dataframe containing the GHG data for the given GHG type.
    """
    
    if GHG_type not in ['Agricultural Landuse','Agricultural Management', 
                        'Non-Agricultural Landuse', 'Transition Penalty']:
        
        raise ValueError('GHG_type can only be one of the following: \
                            ["Agricultural Landuse","Agricultural Management", \
                            "Non-Agricultural Landuse", "Transition Penalty"].')

    # Get GHG file paths under the given GHG type
    GHG_files = all_files.query(f'base_name == "{GHG_type}"').reset_index(drop=True)
    
    return GHG_files



def add_crop_lvstk_to_df(all_files,GHG_type):
    
    """
    This function is used to add the crop and livestock data to the dataframe containing the GHG data.

    Parameters:
    GHG_files (pandas.DataFrame): The input dataframe containing the GHG data.
    GHG_type (str): The given GHG type.

    Returns:
    pandas.DataFrame: The dataframe containing the GHG data for the given GHG type.
    """

    # Read GHG emissions of ag lucc
    
    GHG_files = get_GHG_subsector_files(all_files,GHG_type)
    
    CSVs = []
    for _,row in GHG_files.iterrows():
        csv = pd.read_csv(row['path'],index_col=0,header=[0,1,2]).drop('SUM',axis=1)

        # Get the land use and land use category
        if GHG_type != 'Non-Agricultural Landuse':

            # Subset the crop landuse
            csv_crop = csv[[True if i in LU_CROPS else False for i in  csv.index]]
            csv_crop.index = pd.MultiIndex.from_product(([row['year']], csv_crop.index, ['Crop'],['Crop']))

            # Subset the livestock landuse
            csv_lvstk = csv[[True if i in LU_LVSTKS else False for i in  csv.index]]
            lvstk_old_index = csv_lvstk.index.str.split(' - ').tolist()

            # Add the year and land use category
            csv_lvstk.index = pd.MultiIndex.from_tuples(zip([row['year']] * len(lvstk_old_index), 
                                                            [i[0] for i in lvstk_old_index], 
                                                            [i[1] for i in lvstk_old_index],
                                                            ['Livestock']* len(lvstk_old_index)))

            # The csv.index has 4 levels -> [year, land use, land use category, land category]
            # where         year: int,                  [2010, 2011, ...,]
            #               land use: str,              [Apples, Beef, ...]
            #               land category: str          [modified land, natural land]
            #               land use category: str,     [Crop, Livestock]
            csv = pd.concat([csv_crop,csv_lvstk],axis=0)
        else:
            csv = csv[[True if i in NON_AG_LANDUSE else False for i in csv.index]]
            # Add the year and land use category, land category, so that the csv.index has 4 levels
            # which are matches the other GHG emissions data
            csv.index = pd.MultiIndex.from_product(([row['year']], 
                                                    csv.index, 
                                                    ['Non-Agricultural Landuse'],
                                                    ['Non-Agricultural Landuse']))
            
        # Append the csv to the list
        CSVs.append(csv)

    # Concatenate the csvs
    GHG_df = pd.concat(CSVs,axis=0)

    return GHG_df


def read_GHG_to_long(all_files,GHG_type):
    
    """
    This function is used to convert the GHG data into long format.

    Parameters:
    GHG_files (pandas.DataFrame): The input dataframe containing the GHG data.
    GHG_type (str): The given GHG type.

    Returns:
    pandas.DataFrame: The dataframe containing the GHG data for the given GHG type.
    """
    
    GHG_df = add_crop_lvstk_to_df(all_files,GHG_type)
        
    # Define the index levels
    idx_level_name = ['Year','Land use','Land category','Land use category']

    # remove the first level in the multiindex columns
    GHG_df_long = GHG_df.copy()
    GHG_df_long = GHG_df_long.droplevel(0,axis=1)

    # Squeeze the multiindex columns into a single concatenated by "+"
    GHG_df_long.columns = ["+".join(i) for i in GHG_df_long.columns.tolist()]
    GHG_df_long = GHG_df_long.reset_index()
    GHG_df_long.columns = idx_level_name + GHG_df_long.columns.tolist()[4:]

    # Melt the table to long format
    GHG_df_long = GHG_df_long.melt(id_vars=idx_level_name,
                                        value_vars=GHG_df_long.columns.tolist()[3:],
                                        value_name='val_t')

    # Get the GHG emissions in Mt CO2e
    GHG_df_long['Quantity (Mt CO2e)'] = GHG_df_long['val_t'] / 1e6

    # Split the variable column into Irrigation and Sources
    GHG_df_long[['Irrigation','Sources']] = GHG_df_long['variable'].str.split('+',expand=True)

    # Replace the Sources with the GHG names
    GHG_df_long['Sources'] = GHG_df_long['Sources'].apply(lambda x: GHG_NAMES[x] if GHG_NAMES.get(x,None) else x)

    # Drop unnecessary columns and reorder the columns
    GHG_df_long.drop(['val_t','variable'],axis=1,inplace=True)
    GHG_df_long = GHG_df_long.reindex(columns= idx_level_name + ['Irrigation','Sources', 'Quantity (Mt CO2e)'])
    
    return GHG_df_long


def get_GHG_category(all_files,GHG_type):
    
    """
    This function is used to get the GHG data for the given GHG type.

    Parameters:
    GHG_files (pandas.DataFrame): The input dataframe containing the GHG data.
    GHG_type (str): The given GHG type.

    Returns:
    pandas.DataFrame: The dataframe containing the GHG data for the given GHG type.
    """
    
    GHG_df_long = read_GHG_to_long(all_files,GHG_type)

    # 1) get CO2 GHG
    GHG_CO2 = GHG_df_long.query('~Sources.isin(@GHG_CATEGORY.keys())').copy()
    GHG_CO2['GHG Category'] = 'CO2'

    # 2) get non-CO2 GHG
    GHG_nonCO2 = GHG_df_long.query('Sources.isin(@GHG_CATEGORY.keys())').copy()
    GHG_nonCO2['GHG Category'] = GHG_nonCO2['Sources'].apply(lambda x: GHG_CATEGORY[x].keys())
    GHG_nonCO2['Multiplier'] = GHG_nonCO2['Sources'].apply(lambda x: GHG_CATEGORY[x].values())
    GHG_nonCO2 = GHG_nonCO2.explode(['GHG Category','Multiplier']).reset_index(drop=True)
    GHG_nonCO2['Quantity (Mt CO2e)'] = GHG_nonCO2['Quantity (Mt CO2e)'] * GHG_nonCO2['Multiplier']
    GHG_nonCO2 = GHG_nonCO2.drop(columns=['Multiplier'])

    return pd.concat([GHG_CO2,GHG_nonCO2],axis=0).reset_index(drop=True)