import json
import re
import pandas as pd

from tools import   get_AREA_am, get_AREA_lm, get_AREA_lu, get_GHG_emissions_by_crop_lvstk_df,\
                    get_all_files, get_begin_end_df, get_non_ag_reduction, get_quantity_df, \
                    get_rev_cost_df, get_water_df
              
from tools.helper_func import get_GHG_category, get_GHG_file_df, get_rev_cost,target_GHG_2_Json



RAW_DATA_ROOT = '/home/jinzhu/docker_data/LUTO_DATA/2023_12_12__09_28_38_hard_mincost_RF5_P1e5_2010-2050_timeseries_-265Mt'
SAVE_DIR = 'data'


# Get all LUTO output files and store them in a dataframe
files = get_all_files(RAW_DATA_ROOT)



####################################################
#         1) Produciton, Revenue, Cost             #
####################################################


# Plot_1-1: Production (Million Tonnes)
quantity_csv_paths = files.query('catetory == "quantity" and base_name == "quantity_comparison" and year_types == "single_year"').reset_index(drop=True)
quantity_df = get_quantity_df(quantity_csv_paths)

quantity_df_wide = quantity_df.pivot_table(index=['year'], columns='Commodity', values='Prod_targ_year (tonnes, ML)').reset_index()
quantity_df_wide.to_csv(f'{SAVE_DIR}/production_1_quantity_df_wide.csv', index=False)


# Plot_1-2: Revenue and Cost data (Billion Dollars)
revenue_df = get_rev_cost_df(files, 'revenue')
keep_cols = ['year', 'value (billion)']
loop_cols = revenue_df.columns.difference(keep_cols)

for idx,col in enumerate(loop_cols):
    take_cols = keep_cols + [col]
    df = revenue_df[take_cols].groupby(['year', col]).sum().reset_index()
    # convert to wide format
    df_wide = df.pivot_table(index=['year'], columns=col, values='value (billion)').reset_index()
    # save to csv
    df_wide.to_csv(f'{SAVE_DIR}/production_2_revenue_{idx+1}_{col}_wide.csv', index=False)

cost_df = get_rev_cost_df(files, 'cost')
keep_cols = ['year', 'value (billion)']
loop_cols = cost_df.columns.difference(keep_cols)

# Plot_1-3: Cost data (Billion Dollars)
for idx,col in enumerate(loop_cols):
    take_cols = keep_cols + [col]
    df = revenue_df[take_cols].groupby(['year', col]).sum().reset_index()
    # convert to wide format
    df_wide = df.pivot_table(index=['year'], columns=col, values='value (billion)').reset_index()
    # save to csv
    df_wide.to_csv(f'{SAVE_DIR}/production_3_cost_{idx+1}_{col}_wide.csv', index=False)


# Plot_1-4: Revenue and Cost data (Billion Dollars)
rev_cost_compare = get_rev_cost(revenue_df,cost_df)
rev_cost_compare.to_csv(f'{SAVE_DIR}/production_4_rev_cost_all.csv', index=False)



####################################################
#                    2) Area Change                #
####################################################

# Plot_2-1: Area (km2)
area_paths = files.query('catetory == "cross_table" and year_types == "single_year"').reset_index(drop=True)


crosstab_lu = area_paths.query('base_name == "crosstab-lumap"').reset_index(drop=True)
lu_area = get_AREA_lu(crosstab_lu)
lu_area_wide = lu_area.pivot(index='Year', columns='Land use', values='Area (km2)').reset_index()
lu_area_wide.to_csv(f'{SAVE_DIR}/area_1_total_area_wide.csv', index=False)

# Plot_2-2_(1-5): Area (km2) by Irrigation
crosstab_lm = area_paths.query('base_name == "crosstab-lmmap"').reset_index(drop=True)
lm_area = get_AREA_lm(crosstab_lm)
lm_area_wide = lm_area.pivot(index='Year', columns='Irrigation', values='Area (km2)').reset_index()
lm_area_wide.to_csv(f'{SAVE_DIR}/area_2_irrigation_area_wide.csv', index=False)

# Plot_2-3_(1-5): Area (km2) by Agricultural management
switches_am = area_paths.query('base_name.str.contains(r"switches.*amstat.*", regex=True)').reset_index(drop=True)
am_area_km2 = get_AREA_am(switches_am)
am_area_km2[['Land use','Agricultural management']] = am_area_km2['Land use'].apply(lambda x: re.findall(r'(.*) \((.*)\)',x)[0]).tolist()
am_area_km2_total = am_area_km2.groupby(['Year','Agricultural management']).sum(numeric_only=True).reset_index()

am_area_km2_total_wide = am_area_km2_total.pivot(index='Year', columns='Agricultural management', values='Area (km2)').reset_index()
am_area_km2_total_wide.to_csv(f'{SAVE_DIR}/area_3_am_total_area_wide.csv', index=False)


# Plot_2-4: Area (km2) by Land use
am_area_km2_wide = am_area_km2.drop(columns='Agricultural management').groupby(['Year','Land use']).sum().reset_index()
am_area_km2_wide = am_area_km2_wide.pivot(index='Year', columns='Land use', values='Area (km2)').reset_index()
am_area_km2_wide.to_csv(f'{SAVE_DIR}/area_4_am_lu_area_wide.csv', index=False)


# Plot_2-5/6: Area (km2) by Land use
begin_end_df_area, begin_end_df_pct = get_begin_end_df(files)
# get_xy_data(begin_end_df_area).to_csv(f'{SAVE_DIR}/area_5_begin_end_area.csv', index=False)
# get_xy_data(begin_end_df_pct).to_csv(f'{SAVE_DIR}/area_6_begin_end_pct.csv', index=False)

heat_area = begin_end_df_area.style.background_gradient(cmap='Oranges', axis=1).format('{:,.0f}')
heat_pct = begin_end_df_pct.style.background_gradient(cmap='Oranges', axis=1).format('{:,.0f}%')

heat_area.to_html(f'{SAVE_DIR}/area_5_begin_end_area.html', index=False)
heat_pct.to_html(f'{SAVE_DIR}/area_6_begin_end_pct.html', index=False)




####################################################
#                       3) GHGs                    #
####################################################
GHG_files = get_GHG_file_df(files)
GHG_files = GHG_files.reset_index(drop=True).sort_values(['year','GHG_sum_t'])
GHG_files['GHG_sum_Mt'] = GHG_files['GHG_sum_t'] / 1e6

# Plot_3-1: GHG of cumulative emissions (Mt)
Net_emission = GHG_files.groupby('year')['GHG_sum_Mt'].sum(numeric_only = True).reset_index()
Net_emission = Net_emission.rename(columns={'GHG_sum_Mt':'Net_emission'})

Net_emission['Net_emission_cum'] = Net_emission['Net_emission'].cumsum()
Net_emission_wide = Net_emission[['year','Net_emission']]
Net_emission_wide.to_csv(f'{SAVE_DIR}/GHG_1_cunsum_emission_Mt.csv',index=False)

# Plot_3-2: GHG from individual emission sectors (Mt)
GHG_files_wide = GHG_files.pivot(index='year', columns='base_name', values='GHG_sum_Mt').reset_index()
GHG_files_wide['Net emission'] = GHG_files_wide[GHG_files_wide.columns[1:]].sum(axis=1)
GHG_files_wide.to_csv(f'{SAVE_DIR}/GHG_2_individual_emission_Mt.csv',index=False)

# Plot_3-3: GHG emission (Mt)
GHG_emmisions_long = get_GHG_category(GHG_files,'Agricultural Landuse')

# Plot_3-3-1: Agricultural Emission by crop/lvstk sectors (Mt)
GHG_Ag_emission_total_crop_lvstk = get_GHG_emissions_by_crop_lvstk_df(GHG_emmisions_long)
GHG_Ag_emission_total_crop_lvstk_wide = GHG_Ag_emission_total_crop_lvstk.pivot(index='Year', columns='Landuse_land_cat', values='Quantity (Mt CO2e)').reset_index()
GHG_Ag_emission_total_crop_lvstk_wide.to_csv(f'{SAVE_DIR}/GHG_3_crop_lvstk_emission_Mt.csv',index=False)

# Plot_3-3-2: Agricultural Emission by crop/lvstk sectors (Mt)
GHG_Ag_emission_total_dry_irr = GHG_emmisions_long.groupby(['Year','Irrigation']).sum()['Quantity (Mt CO2e)'].reset_index()
GHG_Ag_emission_total_dry_irr_wide = GHG_Ag_emission_total_dry_irr.pivot(index='Year', columns='Irrigation', values='Quantity (Mt CO2e)').reset_index()
GHG_Ag_emission_total_dry_irr_wide.to_csv(f'{SAVE_DIR}/GHG_4_dry_irr_emission_Mt.csv',index=False)

# Plot_3-3-3: Agricultural Emission by GHG type sectors (Mt)
GHG_Ag_emission_total_GHG_type = GHG_emmisions_long.groupby(['Year','GHG Category']).sum()['Quantity (Mt CO2e)'].reset_index()
GHG_Ag_emission_total_GHG_type_wide = GHG_Ag_emission_total_GHG_type.pivot(index='Year', columns='GHG Category', values='Quantity (Mt CO2e)').reset_index()
GHG_Ag_emission_total_GHG_type_wide.to_csv(f'{SAVE_DIR}/GHG_5_category_emission_Mt.csv',index=False)

# Plot_3-3-4: Agricultural Emission by Sources (Mt)
GHG_Ag_emission_total_Source = GHG_emmisions_long.groupby(['Year','Sources']).sum()['Quantity (Mt CO2e)'].reset_index()
GHG_Ag_emission_total_Source_wide = GHG_Ag_emission_total_Source.pivot(index='Year', columns='Sources', values='Quantity (Mt CO2e)').reset_index()
GHG_Ag_emission_total_Source_wide.to_csv(f'{SAVE_DIR}/GHG_6_sources_emission_Mt.csv',index=False)


# Plot_3-3-5: GHG emission in start and end years (Mt)
start_year,end_year = GHG_emmisions_long['Year'].min(),GHG_emmisions_long['Year'].max() 

GHG_lu_lm = GHG_emmisions_long\
        .groupby(['Year','Land use category','Land use','Irrigation'])\
        .sum()['Quantity (Mt CO2e)']\
        .reset_index()
        
GHG_lu_lm_df_start = GHG_lu_lm.query('Year == @start_year').reset_index(drop=True)
GHG_lu_lm_df_end = GHG_lu_lm.query('Year == @end_year').reset_index(drop=True)

GHG_lu_lm_df_begin_end = pd.concat([GHG_lu_lm_df_start,GHG_lu_lm_df_end],axis=0)
GHG_lu_lm_df_begin_end_wide = GHG_lu_lm_df_begin_end.pivot(index=['Year','Irrigation'], columns='Land use', values='Quantity (Mt CO2e)').reset_index()
GHG_lu_lm_df_begin_end_wide['Irrigation'] = GHG_lu_lm_df_begin_end_wide.apply(lambda x: f"{x['Irrigation']} ({x['Year']})", axis=1)
GHG_lu_lm_df_begin_end_wide.to_csv(f'{SAVE_DIR}/GHG_7_lu_lm_emission_Mt_wide.csv',index=False)

# Plot_3-3-6: GHG emission in the target year (Mt)
GHG_lu_source = GHG_emmisions_long\
                .groupby(['Year','Land use','Irrigation','Sources'])\
                .sum()['Quantity (Mt CO2e)']\
                .reset_index()
        
GHG_lu_source_target_yr = GHG_lu_source.query(f'Year == {end_year}')
GHG_lu_source_nest_dict = target_GHG_2_Json(GHG_lu_source_target_yr)
            
# save as json
with open(f'{SAVE_DIR}/GHG_8_lu_source_emission_Mt.json', 'w') as outfile:
    json.dump(GHG_lu_source_nest_dict, outfile)



# Plot_3-4: GHG sequestrations by Non-Agrilcultural sector (Mt)
Non_ag_reduction_long = get_GHG_category(GHG_files,'Non-Agricultural Landuse')
Non_ag_reduction_total = get_non_ag_reduction(Non_ag_reduction_long)
GHG_non_ag_crop_lvstk_wide = Non_ag_reduction_total.pivot(index='Year', columns='Land use category', values='Quantity (Mt CO2e)').reset_index()
GHG_non_ag_crop_lvstk_wide.to_csv(f'{SAVE_DIR}/GHG_9_non_ag_crop_lvstk_emission_Mt.csv',index=False)


# Plot_3-5: GHG reductions by Agricultural managements (Mt)
Ag_man_sequestration_long = get_GHG_category(GHG_files,'Agricultural Management')

# Plot_3-5-1: GHG reductions by Agricultural managements in total (Mt)
Ag_man_sequestration_total = Ag_man_sequestration_long.groupby(['Year','GHG Category']).sum()['Quantity (Mt CO2e)'].reset_index()
Ag_man_sequestration_total_wide = Ag_man_sequestration_total.pivot(index='Year',columns='GHG Category',values='Quantity (Mt CO2e)').reset_index()
Ag_man_sequestration_total_wide.to_csv(f'{SAVE_DIR}/GHG_10_GHG_ag_man_df_wide_Mt.csv',index=False)


# Plot_3-5-2: GHG reductions by Agricultural managements in subsector (Mt)
Ag_man_sequestration_crop_lvstk_wide = Ag_man_sequestration_long.groupby(['Year','Land use category','Land category']).sum()['Quantity (Mt CO2e)'].reset_index()
Ag_man_sequestration_crop_lvstk_wide['Landuse_land_cat'] = Ag_man_sequestration_crop_lvstk_wide.apply(lambda x: (x['Land use category'] + ' - ' + x['Land category']) 
                                if (x['Land use category'] != x['Land category']) else x['Land use category'], axis=1)

Ag_man_sequestration_crop_lvstk_wide = Ag_man_sequestration_crop_lvstk_wide.pivot(index='Year',columns='Landuse_land_cat',values='Quantity (Mt CO2e)').reset_index()
Ag_man_sequestration_crop_lvstk_wide.to_csv(f'{SAVE_DIR}/GHG_11_GHG_ag_man_GHG_crop_lvstk_df_wide_Mt.csv',index=False)


# Plot_3-5-3: GHG reductions by Agricultural managements in subsector (Mt)
Ag_man_sequestration_dry_irr_total = Ag_man_sequestration_long.groupby(['Year','Irrigation']).sum()['Quantity (Mt CO2e)'].reset_index()
Ag_man_sequestration_dry_irr_wide = Ag_man_sequestration_dry_irr_total.pivot(index='Year',columns='Irrigation',values='Quantity (Mt CO2e)').reset_index()
Ag_man_sequestration_dry_irr_wide.to_csv(f'{SAVE_DIR}/GHG_12_GHG_ag_man_dry_irr_df_wide_Mt.csv',index=False)


####################################################
#                     4) Water                     #
####################################################
water_paths = files.query('catetory == "water" and year_types == "single_year"').reset_index(drop=True)
water_df = get_water_df(water_paths)

# Plot_4-1: Water use compared to limite (%)
water_df_pct_wide = water_df.pivot(index='year', columns='REGION_NAME', values='PROPORTION_%')
water_df_pct_wide.to_csv(f'{SAVE_DIR}/water_1_percent_to_limit.csv')

# Plot_4-2: Water use compared to limite (ML)
water_df_vol_wide = water_df.pivot(index='year', columns='REGION_NAME', values='TOT_WATER_REQ_ML')
water_df_vol_wide.to_csv(f'{SAVE_DIR}/water_2_volum_to_limit.csv')