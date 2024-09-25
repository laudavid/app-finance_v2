import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image # display an image

# import gspread
# from google.oauth2 import service_account

import altair as alt
import streamlit as st

from utils import load_csv, create_excel_file, submit_answers_page2
from labs.lab1 import Q1_compute_holdingperiod_returns


scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

@st.cache_data()
def two_stocks_charts(df_asset_ex2_merge, risky_asset1_ex2, risky_asset2_ex2):
    df_asset_ex2_graph1 = df_asset_ex2_merge.drop(columns=[f"Dividends ({risky_asset1_ex2})",
                                                            f"Dividends ({risky_asset2_ex2})"]).melt(id_vars=["Year"])
    
    chart1 = alt.Chart(df_asset_ex2_graph1).mark_line(point=True).encode(
        x=alt.X('Year:O'), 
        y="value", 
        color="variable"
        ).properties(title=f'View the stock price evolution of {risky_asset1_ex2} and {risky_asset2_ex2}')

    return chart1 


    
@st.cache_data()
def Q2_return_std_portfolios_risky(asset1_returns, asset2_returns, weight_portfolios, risky_asset1_ex2, risky_asset2_ex2):
    
    asset1_expected_return = np.mean(asset1_returns)
    asset1_std_dev = np.std(asset1_returns, ddof=1)
    asset2_expected_return = np.mean(asset2_returns)
    asset2_std_dev = np.std(asset2_returns, ddof=1)
    
    asset12_corr = np.corrcoef(asset1_returns, asset2_returns)[0,1]
    
    # Compute expected return and std of each portfolio 
    expected_returns_portfolios = np.array([w*asset1_expected_return + (1-w)*asset2_expected_return for w in weight_portfolios])
    std_portfolios = np.array([(w*asset1_std_dev)**2 + ((1-w)*asset2_std_dev)**2 + 2*w*(1-w)*asset12_corr*asset1_std_dev*asset2_std_dev for w in weight_portfolios])
    std_portfolios = np.sqrt(std_portfolios)

    df_exp_std_return_portfolios = pd.DataFrame({risky_asset1_ex2:np.round(weight_portfolios,2),
                                                risky_asset2_ex2:np.round(1-weight_portfolios,2),
                                                "Expected return":np.round(expected_returns_portfolios,4), 
                                                "Standard deviation":np.round(std_portfolios,4)})
    
    return df_exp_std_return_portfolios


@st.cache_data()
def Q3_efficient_portfolios(df):
    df_ex2_q3_efficient = df.sort_values(by=["Expected return"]).reset_index(drop=True)
    min_std_q3 = df_ex2_q3_efficient["Standard deviation"].min()
    min_std_q3_exp = df_ex2_q3_efficient.loc[df_ex2_q3_efficient["Standard deviation"] == min_std_q3,"Expected return"].idxmax()
    efficient_portfolio = df_ex2_q3_efficient.iloc[min_std_q3_exp:].reset_index(drop=True)
    
    return efficient_portfolio


@st.cache_data()
def Q5_tangency_portfolio(df, risky_asset1_ex2, risky_asset2_ex2):
    riskfree_rate = 0.02
    df["Sharpe Ratio"] = np.round(((df["Expected return"] - riskfree_rate)/df["Standard deviation"]),4)
    
    max_sharpe_ratio = df["Sharpe Ratio"].idxmax()
    max_sharpe_ratio_row = df.iloc[max_sharpe_ratio,:]
    
    # Portfolio with max sharpe ratio
    max_sharpe_weight1, max_sharpe_weight2 = max_sharpe_ratio_row[risky_asset1_ex2], max_sharpe_ratio_row[risky_asset2_ex2]
    max_sharpe, max_sharpe_expected, max_sharpe_std = max_sharpe_ratio_row["Sharpe Ratio"], max_sharpe_ratio_row["Expected return"], max_sharpe_ratio_row["Standard deviation"]

    return df, max_sharpe, max_sharpe_weight1, max_sharpe_weight2


@st.cache_data()
def Q6_compute_weights():
    weight_portfoliosR = np.round(np.arange(0,1.01,0.01),2)
    weight_riskfree = 1 - weight_portfoliosR

    weight_risk1_full = []
    weight_risk2_full = []
    weight_riskportfolio = []
    weight_riskfree = []

    # Weights in risky portfolio R (weight=1 for risky portfolio R)
    weight_risk1_portfolioR = []
    weight_risk2_portfolioR = []

    for wp in weight_portfoliosR:
        for w1 in weight_portfoliosR:
            weight_risk1_full.append(w1)
            weight_risk2_full.append(wp-w1)
            weight_riskportfolio.append(wp)
            weight_riskfree.append(1-wp)

            weight_risk1_portfolioR.append(w1/wp)
            weight_risk2_portfolioR.append((wp-w1)/wp)
            
    return weight_risk1_full, weight_risk2_full, weight_riskportfolio, weight_riskfree, weight_risk1_portfolioR, weight_risk2_portfolioR


@st.cache_data()
def Q6_portfolio_tworisky_riskfree(asset1_returns, asset2_returns, risky_asset1_ex2, risky_asset2_ex2, 
                                   max_sharpe_weight1, max_sharpe_weight2):
    
    weight_risk1_full, weight_risk2_full, weight_riskportfolio, weight_riskfree, weight_risk1_portfolioR, weight_risk2_portfolioR = Q6_compute_weights()
    
    df_full_portfolio = pd.DataFrame({risky_asset1_ex2:np.round(weight_risk1_full,2),
                                    f"{risky_asset1_ex2} (in risky portfolio)":np.round(weight_risk1_portfolioR,2),
                                    risky_asset2_ex2:np.round(weight_risk2_full,2),
                                    f"{risky_asset2_ex2} (in risky portfolio)":np.round(weight_risk2_portfolioR,2),
                                    "risky portfolio":np.round(weight_riskportfolio,2),
                                    "risk-free":np.round(weight_riskfree,2)})


    asset1_expected_return = np.mean(asset1_returns)
    asset1_std_dev = np.std(asset1_returns, ddof=1)
    asset2_expected_return = np.mean(asset2_returns)
    asset2_std_dev = np.std(asset2_returns, ddof=1)
    asset12_corr = np.corrcoef(asset1_returns, asset2_returns)[0,1]
    
    # Compute expected return and std of each portfolio 
    expected_returns_portfolios = np.array([w1*asset1_expected_return + w2*asset2_expected_return + w3*0.02 for w1,w2,w3 in zip(weight_risk1_full,weight_risk2_full,weight_riskfree)])
    std_portfolios = np.array([(w1*asset1_std_dev)**2 + (w2*asset2_std_dev)**2 + 2*w1*w2*asset12_corr*asset1_std_dev*asset2_std_dev for w1,w2 in zip(weight_risk1_full,weight_risk2_full)])
    std_portfolios = np.sqrt(std_portfolios)

    df_full_portfolio["Expected return"] = expected_returns_portfolios
    df_full_portfolio["Standard deviation"] = std_portfolios

    # Find efficient portfolios 
    df_efficient_portfolios = df_full_portfolio.loc[(df_full_portfolio[f"{risky_asset1_ex2} (in risky portfolio)"]==max_sharpe_weight1) & (df_full_portfolio[f"{risky_asset2_ex2} (in risky portfolio)"]==max_sharpe_weight2)].drop(columns=[f"{risky_asset1_ex2} (in risky portfolio)",f"{risky_asset2_ex2} (in risky portfolio)"])
    df_efficient_portfolios.reset_index(drop=True, inplace=True)
    
    return df_efficient_portfolios





#################################################################################################################
#                                        EXERCICE 2 - Two risky assets
#################################################################################################################

def lab2_code(select_teacher, select_code, student_ids):

    startdate = datetime.now()
    default_text = ""
    list_risky_assets = ["ACMTA", "ACU", "AIR", "ASA", "BKTI", "CECO", "PRG"]

    ##################################### SIDEBAR ##########################################
    risky_asset1_ex2 = st.sidebar.selectbox('Select the first risky stock ➡️', list_risky_assets)
    
    if risky_asset1_ex2:
        risky_asset2_ex2 = st.sidebar.selectbox('Select the second risky stock ➡️', [elem for elem in list_risky_assets if elem != risky_asset1_ex2])


    ##################################### TITLE ##########################################
    st.markdown("## 02 - Two risky assets")
    st.info("""The purpose of this exercise is to understand how to **construct efficient portfolios** if you can invest in two risky assets.""")
    st.sidebar.markdown("  ")

    
    ##################################### QUESTION 1 #####################################
    st.markdown("   ")
    st.markdown("   ")

    st.subheader("Question 1 📝")
    
    ########### Q1 PART 1
    st.markdown('''<p style="font-size: 22px;"> Download prices for two risky stocks. <b>Compute their realized returns</b>.  
                Next, estimate the <b>expected returns</b> and <b>standard deviations of returns</b> on these two stocks. 
                Finally, compute the <b>correlation of the returns</b> on these two stocks.''',
                unsafe_allow_html=True)

    st.markdown("  ")


    ######################## LOAD DATASETS ############################
    
    ## Dataframe for each stock
    df_asset1_ex2 = load_csv(f"data/stocks/{risky_asset1_ex2}.csv")
    df_asset2_ex2 = load_csv(f"data/stocks/{risky_asset2_ex2}.csv")


    ## Dataframe with both stocks 
    two_assets = [risky_asset1_ex2, risky_asset2_ex2]
    two_assets.sort()
    df_asset_ex2_merge = load_csv(f"data/two_stocks/{two_assets[0]}_{two_assets[1]}.csv")
    
    
    
    ############################### VIEW PLOTS #############################   
    
    chart1 = two_stocks_charts(df_asset_ex2_merge, risky_asset1_ex2, risky_asset2_ex2)
    st.altair_chart(chart1, use_container_width=True)
    
    
    
    ####################### SHOW DOUBLE DATASET + DOWNLOAD BUTTON ############################

    st.markdown(f"**View Price and Dividends for {risky_asset1_ex2} and {risky_asset2_ex2}**")
    st.dataframe(df_asset_ex2_merge, use_container_width=True)
    
    # Convert the DataFrame to Excel bytes
    excel_data = create_excel_file(df_asset_ex2_merge)

    # Use the download button to allow users to download the Excel file
    st.download_button(
        label=f"📥 **Download the {risky_asset1_ex2} and {risky_asset2_ex2} stock data**",
        data=excel_data,
        file_name=f"{risky_asset1_ex2}_{risky_asset2_ex2}_Ex2.xlsx",
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    st.markdown(" ")
    st.markdown(" ")
    
    
    
    
    
    ############################## RISKY STOCK 1 ##################################


    st.subheader(f"Risky stock 1: **{risky_asset1_ex2}** 📋")
    st.markdown("  ")


    ## Compute holding-period returns, expected returns, std 
    asset1_returns = Q1_compute_holdingperiod_returns(df_asset1_ex2)    


    ## Holding-period returns
    st.write(f"**Compute the holding-period returns**")

    # Upload answer
    upload_file = st.file_uploader("Drop your results in an excel file (.xlsx)", key="Ex2.Q1.11",type=['xlsx'])
    answer_2_Q1_1a = ""
    
    if upload_file is not None:
        answer_2_Q1_1a = "Received"

    st.markdown("  ")
    st.markdown("  ")


    ## Expected returns
    st.write(f"**Compute the expected return**")
    answer_2_Q1_1b = st.text_input("Enter your results","", key="Ex2.Q1.12")
    st.markdown("  ")


    ## Standard deviation of returns
    st.write(f"**Compute the standard deviation**")
    answer_2_Q1_1c = st.text_input(f"Enter your results","", key="Ex2.Q2.13")
    st.markdown("  ")


    if st.checkbox(f'**Solutions - Question 1 ({risky_asset1_ex2})** ✅'):
        returns_result = pd.DataFrame({"Year":df_asset1_ex2["Year"].iloc[1:], f"Return ({risky_asset1_ex2})":asset1_returns})
        
        st.success("**Instruction**: *Please select one stock and compute its realized (holding-period) returns. Assume that holding, is one year.*")
        st.dataframe(returns_result)
        
        st.markdown(" ")

        asset_expected_return = np.round(np.mean(asset1_returns),4)
        asset_std_dev = np.round(np.std(asset1_returns, ddof=1), 4)
        
        st.success(f"**Instruction**: *Compute the expected return and standard deviation of the holding-period returns*")
        st.markdown(f"""- **Expected return**: {asset_expected_return} 
- **Standard deviation**: {asset_std_dev}
                    """, unsafe_allow_html=True)
        
        
    st.markdown("  ")
    st.markdown("  ")




    ######################## RISKY ASSET 2 ############################

    st.subheader(f"Risky stock 2: **{risky_asset2_ex2}** 📋")
    st.markdown("  ")


    ## Compute holding-period returns
    asset2_returns = Q1_compute_holdingperiod_returns(df_asset2_ex2)


    ## Holding-period returns
    st.write(f"**Compute the holding-period returns**")
    
    upload_expected_return = st.file_uploader("Drop your results in an excel file (.xlsx)", key="Ex2.Q1.21",type=['xlsx'])
    answer_2_Q1_2a = ""
    if upload_expected_return is not None:
        answer_2_Q1_2a = u"Received"

    st.markdown("  ")


    ## Expected returns
    st.write(f"**Compute the expected return**")
    answer_2_Q1_2b = st.text_input("Enter your results","", key="Ex2.Q1.22")
    st.markdown("  ")


    ## Standard deviation
    st.write(f"**Compute the standard deviation**")
    answer_2_Q1_2c = st.text_input(f"Enter your results","", key="Ex2.Q2.23")
    st.markdown("  ")
    
    
    if st.checkbox(f'**Solutions - Question 1 ({risky_asset2_ex2})** ✅'):
        returns_result = pd.DataFrame({"Year":df_asset2_ex2["Year"].iloc[1:], f"Return ({risky_asset2_ex2})":asset2_returns})
        st.success("**Instruction**: *Please select one stock and compute its realized (holding-period) returns. Assume that holding, is one year.*")
        st.dataframe(returns_result)
        
        st.markdown(" ")

        asset_expected_return = np.round(np.mean(asset2_returns),4)
        asset_std_dev = np.round(np.std(asset2_returns, ddof=1), 4)
        
        st.success(f"**Instruction**: *Compute the expected return and standard deviation of the holding-period returns*")
        st.markdown(f"""- **Expected return**: {asset_expected_return} 
- **Standard deviation**: {asset_std_dev}
                    """, unsafe_allow_html=True)
        
        
    st.markdown("  ")
    st.markdown("  ")



    
    ############## CORRELATION ASSET 1 AND ASSET 2 ##############
    
    st.subheader(f"Correlation between {risky_asset1_ex2} and {risky_asset2_ex2} 📈")
    st.markdown("  ")
    
    # Input answers
    st.write(f"**Compute the correlation between both assets**")
    answer_2_Q1_3 = st.text_input(f"Enter your results","", key="Ex2.Q2.3")
    st.markdown("  ")

    if st.checkbox(f'**Solutions - Question 1 (Correlation)** ✅'):
        asset12_corr = np.corrcoef(asset1_returns, asset2_returns)[0,1]
        st.markdown(f"Correlation between {risky_asset1_ex2} and {risky_asset2_ex2}: **{np.round(asset12_corr,3)}**.")
        

    
    st.markdown("   ")
    st.markdown("   ") 
    st.markdown("   ")     
    st.markdown("   ")
    st.markdown("   ")






    ##################################### QUESTION 2 #####################################

    st.subheader("Question 2 📝")

    st.markdown('''<p style="font-size: 22px;"> Compose different <b>portfolios of two risky assets</b> by investing in one risky asset x% of your wealth and in the other asset (1-x)%.
                Vary x from -50% to 150% with an increment of 1%. Compute the <b>expected returns</b> and <b>standard deviations</b> of the resulting portfolios.''', 
                unsafe_allow_html=True)
    
    st.info("**Hint**: Do not forget about the correlation between the returns on these two stocks.")

    st.markdown("  ")
    st.markdown("  ")
    
    

    # Feasible portfolios graph
    # chart_portfolios = alt.Chart(df_exp_std_return_portfolios).mark_circle(size=40).encode(y="Expected return",x="Standard deviation")

    weight_portfolios = np.round(np.arange(-0.5,1.55,0.01),2)
    df_exp_std_return_portfolios = Q2_return_std_portfolios_risky(asset1_returns, asset2_returns, weight_portfolios, risky_asset1_ex2, risky_asset2_ex2)

    st.write("**Compute the expected return and standard deviation for each portfolio**")

    upload_expected_return = st.file_uploader("Drop your results in an excel file (.xlsx)", key="Q3.21", type=['xlsx'])
    answer_2_Q2 = ""
    if upload_expected_return is not None:
        answer_2_Q2 = "Received"

    st.markdown("  ")
    
    if st.checkbox(f'**Solutions - Question 2** ✅'):
        st.dataframe(df_exp_std_return_portfolios)
    



    st.markdown("   ")
    st.markdown("   ") 
    st.markdown("   ")     
    st.markdown("   ")
    st.markdown("   ") 






    ##################################### QUESTION 3 #####################################

    st.subheader("Question 3 📝")

    st.markdown('''<p style="font-size: 22px;"> Indicate the set of <b>feasible portfolios</b> and the set of <b>efficient portfolios</b>. Next, <b>draw a graph in which you represent the portfolios</b>, that is, the sigma-expected return pairs, you obtain with different combinations of the two risky assets.''', 
                unsafe_allow_html=True)
    
    st.markdown(" ")

    ## 1. Set of feasible portfolio
    st.write("**What is the set of feasible portfolios ?**")
    answer_2_Q3_1 = st.text_area("Write your answer here", default_text, key="Q3.Ex2.11")

    st.markdown("  ")
    st.markdown("   ")


    ## 2. Set of efficient portfolios
   
    st.write("**What is the set of efficient portfolios ?**")
    answer_2_Q3_2 = st.text_area("Write your answer here", default_text, key="Q3.Ex2.12")


    
    st.markdown("  ")
    st.markdown("   ")
    


    ## Draw the set of feasible portfolios 
    st.write("**Draw the set of feasible portfolios**")

    upload_graph = st.file_uploader("Drop the graph as an image (jpg, jpeg, png)", key="Q3.Ex2.13", type=['jpg','jpeg','png'])
    answer_2_Q3_3 = ""
    if upload_graph is not None:
        answer_2_Q3_3 = "Received"
    

        
    st.markdown("   ")
    
    if st.checkbox(f'**Solutions - Question 3** ✅'):
        st.success("**Instruction**: *What is the set of feasible portfolios ?*")
        st.markdown(f"The **set of all portfolios** (standard deviation-expected return) that can be obtained by building portfolios with {risky_asset1_ex2} and {risky_asset2_ex2}.")
        
        df_ex2_q3_efficient = Q3_efficient_portfolios(df_exp_std_return_portfolios)
        
        st.markdown("  ")
        
        st.success("**Instruction**: *What is the set of efficient portfolios ?*")
        st.markdown("The portfolios that **offer the greatest expected rate of return for each level of standard deviation** (risk).")
        # st.dataframe(df_ex2_q3_efficient.iloc[min_std_q3_exp:].reset_index(drop=True))
        st.dataframe(df_ex2_q3_efficient)
        
        st.markdown("  ")
        
        st.success("**Instruction**: *Draw the set of feasible portfolios*")
        
        chart_portfolios_q3 = alt.Chart(df_exp_std_return_portfolios).mark_circle(size=20).encode(
            x=alt.X('Standard deviation:Q'),
            y=alt.Y('Expected return:Q'))
        
        st.altair_chart(chart_portfolios_q3.interactive(), use_container_width=True)
        #st.dataframe(df_exp_std_return_portfolios)

    st.markdown("   ")
    st.markdown("   ") 
    st.markdown("   ")     
    st.markdown("   ")
    st.markdown("   ")





    ##################################### QUESTION 4 #####################################

    st.subheader("Question 4 📝")

    st.markdown('''<p style="font-size: 22px;"> Assume that you cannot short-sell any of the risky assets. 
                Indicate the new <b>set of feasible portfolios</b> and the new <b>set of efficient portfolios</b>.''', 
                unsafe_allow_html=True)
    
    
    st.markdown("  ")


    ## 1. Set of feasible portfolios
    st.write("**What is the set of feasible portfolios ?**")
    
    upload_portfolios = st.file_uploader("Drop your results in an excel file (.xlsx)", key="Q4.Ex2.U11",type=['xlsx'])
    answer_2_Q4_1 = ""
    if upload_portfolios is not None:
        answer_2_Q4_1 = "Received"

        
    st.markdown("  ")
    st.markdown("  ")


    ## 2. Set of efficient portfolios
    st.write("**What is the set of efficient portfolios ?**")
    upload_efficient_portfolios = st.file_uploader("Drop your results in an excel file (.xlsx)", key="Q4.Ex2.U12",type=['xlsx'])
    
    answer_2_Q4_2 = ""
    if upload_efficient_portfolios is not None:
        answer_2_Q4_2 = "Received"

        
    st.markdown("  ")
        
    if st.checkbox(f'**Solutions - Question 4** ✅'):
        df_exp_std_return_portfolios_q4 = df_exp_std_return_portfolios.loc[(df_exp_std_return_portfolios[risky_asset1_ex2]>=0) & (df_exp_std_return_portfolios[risky_asset2_ex2]>=0)]        

        st.success("**Instruction**: *What is the set of feasible portfolios ?*")
        st.markdown(f"The set of feasible portfolios are the **portfolios with only positive or null weights in {risky_asset1_ex2} and {risky_asset2_ex2}.**")
        st.dataframe(df_exp_std_return_portfolios_q4)        
        
        df_ex2_q4_efficient = Q3_efficient_portfolios(df_exp_std_return_portfolios)
        
        st.markdown("  ")
        
        st.success("**Instruction**: *What is the set of efficient portfolios ?*")
        st.dataframe(df_ex2_q4_efficient)
                
        
    st.markdown("   ")
    st.markdown("   ") 
    st.markdown("   ")     
    st.markdown("   ")
    st.markdown("   ")






    ##################################### QUESTION 5 #####################################

    st.subheader("Question 5 📝")

    st.markdown('''<p style="font-size: 22px;"> Assume that you also have a risk-free asset with a rate of return of 2% per annum. 
                <b>Find the tangency portfolio</b>.''', 
                unsafe_allow_html=True)
    
    st.info("**Hint**: Compute the Sharpe ratio (the reward-to-variability ratio) for all feasible portfolios in Question 2. Find the portfolio with the maximal one.")
    st.markdown(" ")

    st.write("**What is the tangency portfolio ?**")
    answer_2_Q5 = st.text_area("Write your answer here", default_text, key="UQ5.Ex2")
    
    df_exp_std_return_portfolios, max_sharpe, max_sharpe_weight1, max_sharpe_weight2 = Q5_tangency_portfolio(df_exp_std_return_portfolios, risky_asset1_ex2, risky_asset2_ex2)

    if st.checkbox(f'**Solutions - Question 5** ✅'):
        st.markdown(f"""The tangency portfolio is the portfolio where you invest **{max_sharpe_weight1}** in {risky_asset1_ex2} and **{max_sharpe_weight2}** in {risky_asset2_ex2}, with a sharpe ratio of **{max_sharpe}**. <br>
                    *The tangency portfolio is highlighted in green in the dataset*""", unsafe_allow_html=True)
        st.dataframe(df_exp_std_return_portfolios.style.highlight_max(color="lightgreen", subset="Sharpe Ratio",axis=0))
        
    st.markdown("   ")
    st.markdown("   ") 
    st.markdown("   ")     
    st.markdown("   ")
    st.markdown("   ")



    ######################################### QUESTION 6 #########################################

    st.subheader("Question 6 📝")

    ### Q5 PART 1
    st.markdown('''<p style="font-size: 22px;">Indicate the <b>set of efficient portfolios</b> that you can achieve if you invest in two risky assets and one risk-free asset.''', 
                unsafe_allow_html=True)

    ## Efficient portfolios ?
    st.write("**What is the set of efficient portfolios ?**")
    
    upload_efficient_portfolios = st.file_uploader("Drop your results in an excel file (.xlsx)", key="UQ6.Ex6",type=['xlsx'])
    answer_2_Q6 = ""
    if upload_efficient_portfolios is not None:
        answer_2_Q6 = "Received"





    if st.checkbox(f'**Solutions - Question 6** ✅'):
        st.markdown(f"""The efficient portfolios are the portfolios with a **combination of the risk-free asset and the tangency portfolio of Question 5.** <br>
                    *The weights for {risky_asset1_ex2} and {risky_asset2_ex2} where computed based on the overall portfolio, not on the risky portfolio (the portfolio with only risky assets).*""", unsafe_allow_html=True)
        
        df_efficient_portfolios = Q6_portfolio_tworisky_riskfree(asset1_returns, asset2_returns, risky_asset1_ex2, risky_asset2_ex2, 
                                                            max_sharpe_weight1, max_sharpe_weight2)
        st.markdown(" ")
        st.dataframe(df_efficient_portfolios)
        
    st.markdown(" ")
    st.markdown(" ")
    st.markdown("#### Congratulations you finished Exercise 2 🎉")




    ######### SUBMIT ANSWERS #########
    list_answer = [answer_2_Q1_1a,
    answer_2_Q1_1b,
    answer_2_Q1_1c,
    answer_2_Q1_2a,
    answer_2_Q1_2b,
    answer_2_Q1_2c,
    answer_2_Q1_3,
    answer_2_Q2,
    answer_2_Q3_1,
    answer_2_Q3_2,
    answer_2_Q3_3,
    answer_2_Q4_1,
    answer_2_Q4_2,
    answer_2_Q5,
    answer_2_Q6]
    
    answers = [x for x in list_answer if x not in [np.nan,"", None]]
    count = len(answers)
    select_assets = "-".join(two_assets)

    list_answers_ = [select_teacher,
    select_code,
    student_ids,
    2,
    select_assets,
    str(datetime.now().date()),
    count,
    f"{round((count/len(list_answer))*100,1)}%"]
    
    list_answers_ += list_answer

    ########################################## SUBMISSION #########################################
        
    
    # Button to trigger submission
    submit_button = st.sidebar.button('**Submit answers Ex2**')    
    
    if 'submitted_page2' not in st.session_state:
        st.session_state['submitted_page2'] = False

    # If the button is clicked, run the submission function
    if submit_button:
        st.session_state['submitted_page2'] = True
        submit_answers_page2(list_answers_)


    # Show the success message if submission is complete
    if st.session_state.get('submitted_page2', True):
        st.sidebar.success('**Your answers have been submitted!**')
            
        st.session_state['submitted_page2'] = False
    
    
    st.sidebar.markdown("""**Note**: The green text box confirming your submission might not appear after clicking the submit button. 
                            This doesn't mean your submission wasn't registered, as it is just an app display issue.""", unsafe_allow_html=True)
