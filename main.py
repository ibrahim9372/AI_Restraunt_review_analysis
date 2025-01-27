from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import pandas as pd
service = Service(ChromeDriverManager().install())
import streamlit as st
import json
import os
from groq import Groq

from streamlit_option_menu import option_menu
import anthropic
import seaborn as sns
import time
import plotly.graph_objs as go
from streamlit.runtime.scriptrunner import RerunException
import matplotlib.pyplot as plt

csv_pink_door = 'yipee_reviews_2.csv'
csv_dynamic_url ='dynamic_url.csv'
csv_module_4 = 'compatitor.csv'
json_pink_door = 'clean.json'

json_dynamic_url = 'dynamic_url_llm.json'


with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

prompt = 'You are a review_analyst. Your task is to extract only the information mentioned in the review, without adding or changing anything. For food, type "food:" followed by any comments about food in one grammatically correct sentence. If no food-related comment is present, leave the food section blank, without stating anything about its absence. Similarly, for service, type "service:" followed by any comments about service in one grammatically correct sentence. If no service-related comment is present, leave the service section blank, without stating anything about its absence. If there is any personal information or mention of personal events (such as anniversaries, celebrations, or personal milestones) in the service comments, do not include those. Do not include any personal information, such as names, contact details, or references to personal events. Do not add any extra words or content, and do not change the meaning of the original review.'

os.environ["ANTHROPIC_API_KEY"] = "placeholder"
os.environ['GROQ_API_KEY'] = 'placeholder'

#Created TensorFlow Lite XNNPACK delegate for CPU.
# Attempting to use a delegate that only supports static-sized tensors with a graph that has dynamic-sized tensors (tensor#58 is a dynamic-sized tensor).

def correct_url(url):
    
    if '&page' in url:
        if url.endswith('&page'):
            url = url + "=1"  
       
    else:
        url = url + '&page=1'
    return url
#_______________________________________________________________________________________________________________________________#
def extract_date(date, today_date):
   
    if 'day ago' in date or 'today':
        return today_date
    
    if 'days ago' in date:
       
        array = date.split(' ')
        days_ago = int(array[1])

        
        year = int(today_date[0:4])
        month = int(today_date[5:7])
        day = int(today_date[8:10])
        new_day = day - days_ago
        if new_day <= 0:  
            new_day += 30
            month -= 1  
        if month <= 0:
            month = 12  
            year -= 1 
        month_str = str(month) if month >= 10 else '0' + str(month)
        new_day_str = str(new_day) if new_day >= 10 else '0' + str(new_day)
        formatted_date = str(year) + '-' + month_str + '-' + new_day_str
        return formatted_date
    
    elif 'Dined on' in date:
       
        array = date.split(' ')
        
      
        year = array[-1]
        day = array[-2].replace(',','')
        month = str(array[-3]).lower()
        month_dict = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04', 'may': '05',
            'june': '06', 'july': '07', 'august': '08', 'september': '09', 'october': '10',
            'november': '11', 'december': '12'
         }
        if month in month_dict:
         month_str = month_dict[month]
        else:
            month_str = '00'
        formatted_date = str(year) + '-' + month_str + '-' + str(day).zfill(2)
        return  formatted_date
#---------------------------------#
    
def extract_name(url):
    driver = webdriver.Chrome(service=service)

    driver.get(url)
    try :
        name = driver.find_element(By.XPATH,'//*[@id="mainContent"]/div/div[2]/div[1]/section[1]/div[1]/div/div[1]/h1')
        return name.text
    except Exception as idk:
        return 'Name not specified'

def module_3_scraapping(csvname, URL, option=0, n=10):
    driver = webdriver.Chrome(service=service)

    reviews_content = []
    reviews_date = []
    overall_rating = []
    food = [] 
    ambiance = []
    service_ratings = []
    count = n
    namebool = True
    filled = False

    if option == 0:
        url_template = "https://www.opentable.com/r/the-pink-door-seattle?page={}"
    else:
        url_template = "https://www.opentable.com/r/" + str(URL) + "?page={}"
        url=url_template+ str(1)

    i = 1

    while not filled and url_template:
        if (option==0):
         url = url_template.format(i)
        else:
            url = correct_url(URL) + str(i)
        
        try:
            driver.get(url)
        except WebDriverException:
            print("No such restaurant exists. Please check your input.")
            break  
        
        driver.implicitly_wait(10)

        reviews = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/div[2]/span[1]')
        dates = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/div[1]/p')
        overall = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/ol/li[1]/span')
        food_ratings = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/ol/li[2]/span')
        service_ratings_elements = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/ol/li[3]/span')
        ambiance_ratings = driver.find_elements(By.XPATH, '//*[@id="restProfileReviewsContent"]/li/div/ol/li[4]/span')
        for review, date, over, foo, sev, am in zip(reviews, dates, overall, food_ratings, service_ratings_elements, ambiance_ratings):
            try:
                if len(reviews_content) < count:
                    reviews_content.append(review.text)
                    reviews_date.append(date.text)
                    overall_rating.append(over.text)
                    food.append(foo.text)
                    service_ratings.append(sev.text)
                    ambiance.append(am.text)
                else:
                    filled = True
                    break

            except Exception as e:
                print(f"Error occurred while processing reviews: {e}")

        i += 1

   
    min_length = min(len(reviews_content), len(reviews_date), len(overall_rating), len(food), len(service_ratings), len(ambiance))

    reviews_content = reviews_content[:min_length]
    reviews_date = reviews_date[:min_length]
    overall_rating = overall_rating[:min_length]
    food = food[:min_length]
    service_ratings = service_ratings[:min_length]
    ambiance = ambiance[:min_length]





    df = pd.DataFrame({'review_content': reviews_content,'date': reviews_date,'overall_rating': overall_rating,'food': food,'service': service_ratings,'ambiance': ambiance })
    df['restaurant']="--"
    timestamp = []
    for index, row in df.iterrows():
        date = row['date']
        formatted_date = extract_date(date, '2024-12-11')
        timestamp.append(formatted_date)

            
    df['timestamp'] = timestamp

    df['restaurant'] = extract_name(correct_url(URL) + str(i))
    df.to_csv(csvname, index=False)
    
    driver.quit()


#-----------------------------------------------------------------------------------------------------------------------------------------------#
def llm_scrapping(csv_name_module_2,csv_name_module_3 ,processed_line,capacity=10):
    max_bay = processed_line + capacity
    while (processed_line != max_bay):
        meow = pd.read_csv(csv_name_module_2, header=0,skiprows=processed_line, nrows=capacity)
        json_list = []
        prev_data = [] 
        client = anthropic.Anthropic()

        with open(csv_name_module_3, 'r') as file:
                prev_data = json.load(file)
        for index, row in meow.iterrows():

            rev = row.iloc[0]
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0,
                system= prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": rev
                            }
                        ]
                    }
                ]
            )
            print(message.content)
            single_review = message.content[0].text
            sections = single_review.split("\n")
            food_comment = ""
            service_comment = ""
            for section in sections:
                if section.lower().startswith("food:"):
                    food_comment = section.replace("food: ", "").strip()
                elif section.lower().startswith("service:"):
                    service_comment = section.replace("service: ", "").strip()
            data = {
                "restaurant_name": row.iloc[6],
                "date": row.iloc[1],
                "overall_rating": row.iloc[2],
                "ambiance_rating": row.iloc[5],
                "food_rating": row.iloc[3],
                "service_rating": row.iloc[4],
                "food_comment": food_comment,
                "service_comment": service_comment
            }
            
            prev_data.append(data)
            processed_line+=1
            print(processed_line)


            
        with open(csv_name_module_3, 'w') as file:
            json.dump(prev_data, file, indent=4)
    
        
    
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def llm_scrapping_2(csv_name_module_2,csv_name_module_3 ,processed_line,capacity=10):
    max_lines = processed_line + capacity
    while (processed_line != max_lines):
        meow = pd.read_csv(csv_name_module_2, header=0,skiprows=processed_line, nrows=capacity)
        json_list = []
        prev_data = [] 
       

        with open(csv_name_module_3, 'r') as file:
                prev_data = json.load(file)
        for index, row in meow.iterrows():

            revi = row.iloc[0]
            client = Groq(
                            api_key=os.environ.get("GROQ_API_KEY"),)
            messages =[
                    {"role": "system", "content": prompt +'dont give two backslashes '},
                    {"role": "user", "content":revi}
                ]

                # Send the messages to the model and get the response
            messages = client.chat.completions.create(model="llama3-8b-8192", messages=messages)
            
            #single_review = message.content[0].text
            single_review= messages.choices[0].message.content
            sections = single_review.split("\n\n")
            food_comment = ""
            service_comment = ""
            for section in sections:
                if section.lower().startswith("food:"):
                    food_comment = section.replace("food: ", "").strip()
                elif section.lower().startswith("service:"):
                    service_comment = section.replace("service: ", "").strip()
            data = {
                "restaurant_name": row.iloc[6],
                "date": row.iloc[1],
                "overall_rating": row.iloc[2],
                "ambiance_rating": row.iloc[5],
                "food_rating": row.iloc[3],
                "service_rating": row.iloc[4],
                "food_comment": food_comment,
                "service_comment": service_comment
            }
            
            prev_data.append(data)
            processed_line+=1
            print(processed_line)


            
        with open(csv_name_module_3, 'w') as file:
            json.dump(prev_data, file, indent=4)
    
        
# ____________________________________________________________________________________________________________________________________________________________________________________________________#

def LLM_model(url,t_rev):
    global csv_dynamic_url, json_dynamic_url
    lines = 0
    max_lines = t_rev
    csv_name_module_2 ="compatitor.csv"
    csv_name_module_3 = "cleaned_compatitor.json"
    dummy= [] 

    with open(json_dynamic_url,'w') as file:
        json.dump(dummy,file,indent=4)
    module_3_scraapping(csv_dynamic_url,url,1,max_lines)
    time.sleep(8)

    llm_scrapping_2(csv_dynamic_url,json_dynamic_url,lines,t_rev)
    
         

#---------------------------------------------------------------------------------------------------------------------------------------------
def review_gui(json_name,count,option):
    with open(json_name, 'r') as file:
        json_reviews = json.load(file)
        json_reviews =json_reviews[:count]
        
    st.header(f"{json_reviews[0]['restaurant_name']}")
    if (option==0):
            #  st.image("pink_door.jpg", caption="")
             st.markdown(f" <div class = overview> <p>{over_view}</p></div>",unsafe_allow_html=True)
             
    # else :
    #     json_reviews =json_reviews[:count]
    #     # count = len(json_reviews)
    st.header(f"Reviews:{count}")
    st.markdown('<div class="review-line"></div>', unsafe_allow_html=True)
    
    for reviews in json_reviews:
            rating  = reviews['overall_rating']
            if (rating==5):
                st.markdown("⭐⭐⭐⭐⭐")
            if (rating==4):
                st.markdown("⭐⭐⭐⭐☆")
            if (rating==3):
                st.markdown("⭐⭐⭐☆☆")
            if (rating==2):
                st.markdown("⭐⭐☆☆☆")
            if (rating==1):
                st.markdown("⭐☆☆☆☆")
            if (rating==0):
                st.markdown("☆☆☆☆☆")
            
            st.markdown(f"<p class='ratings'><b>Date:</b> {reviews['date']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='ratings'><b>Food Rating:</b> {reviews['food_rating']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='ratings'><b>Ambiance:</b> {reviews['ambiance_rating']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='ratings'><b>Service Rating:</b> {reviews['service_rating']}</p>", unsafe_allow_html=True)
            st.markdown('<div class="review">', unsafe_allow_html=True)



            if reviews['food_comment']:
                st.markdown("<div class=label>Food comment:</div>",unsafe_allow_html=True)
                st.markdown(f"<div class='food'>{reviews['food_comment']}</div>", unsafe_allow_html=True)


            if reviews['service_comment']:
                st.markdown("<div class=label>service comment:</div>",unsafe_allow_html=True)
                st.markdown(f"<div class='service'>{reviews['service_comment']}</div>", unsafe_allow_html=True)

            st.markdown('<div class="review-line"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

#-----------------------------------------------------------------------------------------------------------------------------------------#
main_restraunt = "The Pink Door"
over_view ="The Pink Door is an independently owned (never cloned, never genetically modified) restaurant that has been quietly dedicated to fresh & local Italian food since 1981. Its seafood & produce driven menu has been the central theme throughout its wildly popular domain in Seattle's Pike Place Market."
navigation_bar = option_menu(
menu_title = "Main Menu",
options=["Home" , "Reviews" , "Compare","About"],
icons=["house","star","shuffle","info-circle"],
orientation="horizontal",
default_index=0,
menu_icon='cast'
)

total_reviews =10

if navigation_bar=="Home":
    dummy = []
    with open(json_pink_door) as file:
        dummy  = json.load(file)

    pink_reviews_count =  st.number_input('Enter reviews to check' ,5 , len(dummy))
    if (pink_reviews_count!=0):
        review_gui(json_pink_door,pink_reviews_count,0)
  
if navigation_bar=="Reviews":
   total_reviews = st.number_input("Reviews to scarp", min_value=0, max_value=100, step=1)
   dynamic_restraunt_url = st.text_input("Enter URL:",key="dynamic_url",label_visibility="collapsed", placeholder="Enter URL")      
   col1, col2, col3 = st.columns([1, 0.75, 1])  

    
   with col2:
        if st.button("Submit URL", key="dynamic_url_button"):
            if dynamic_restraunt_url != "":
                LLM_model(dynamic_restraunt_url,total_reviews)
                
            else:
                with col1 :
                     st.error("Please enter a valid URL.")
    
   if dynamic_restraunt_url != "":
        dataframe = pd.read_csv(csv_dynamic_url)
        stars = dataframe['overall_rating'].value_counts().sort_index()
        st.bar_chart(stars)
        st.markdown(f"<div class=label>Enter Number of reviews</div>",unsafe_allow_html=True)
        user_review_request = st.number_input("",min_value=0, max_value=dataframe.shape[0], value=0)

        if (user_review_request!=0):
            review_gui(json_dynamic_url,user_review_request,1)
        

if "scraped" not in st.session_state:
    st.session_state.scraped = False  
if navigation_bar=='Compare':
    compatitor_reviews = 50
    compatitor_reviews=st.number_input("Reviews to scarp", min_value=10, max_value=compatitor_reviews, step=1)
    compatitor_url=  st.text_input('Enter url',label_visibility="collapsed", placeholder="Enter URL")
    if(compatitor_url!=""):
        if compatitor_url and not st.session_state.scraped:
                module_3_scraapping(csv_module_4, compatitor_url, 1)
                st.session_state.scraped = True
        user_time_stamp = st.text_input('Enter timestamp',label_visibility="collapsed", placeholder="Enter Timestamp format(2024-12-11 to 2024-11-10)")
        timestamp = user_time_stamp.split(' ')
        start_timestamp = ""
        end_timestamp = ""
        onetime=False
        if len(timestamp)  > 2:
            start_timestamp = timestamp[0]
            end_timestamp = timestamp[2]
            dataframe_1 = pd.read_csv('yipee_reviews.csv')
            dataframe_1['unix'] = pd.to_datetime(dataframe_1['timestamp']).apply(lambda x: x.timestamp())
            t1 = pd.to_datetime(start_timestamp)
            t2 = pd.to_datetime(end_timestamp)
            t1_unix = t1.timestamp()
            t2_unix = t2.timestamp()
            filtered_df_1 = dataframe_1[(dataframe_1['unix'] >= t1_unix) & (dataframe_1['unix'] <= t2_unix)]

            dataframe_2 = pd.read_csv(csv_module_4)
            dataframe_2['unix'] = pd.to_datetime(dataframe_2['timestamp']).apply(lambda x: x.timestamp())
            filtered_df_2 = dataframe_2[(dataframe_2['unix'] >= t1_unix) & (dataframe_2['unix'] <= t2_unix)]
            #------- start of making the plot#---------------------------------------
            filtered_df_1['timestamp'] = pd.to_datetime(filtered_df_1['timestamp'])
            filtered_df_2['timestamp'] = pd.to_datetime(filtered_df_2['timestamp'])


            trace1 = go.Scatter(
            x=filtered_df_1['timestamp'],
            y=filtered_df_1['overall_rating'],
            mode='lines+markers',  
            name='Our restraunt',  
            line=dict(color='purple')
                              )

       
            trace2 = go.Scatter(
            x=filtered_df_2['timestamp'],
            y=filtered_df_2['overall_rating'],
            mode='lines+markers',  
            name='compatitor', 
            line=dict(color='pink')
                        )
            layout = go.Layout(
            title='Time-Series of Overall Ratings',
             xaxis=dict(
            title='Date',
            tickformat='%Y-%m-%d',  
            tickangle=45 
              ),
            yaxis=dict(
            title='Overall Rating'
                 ),
            legend=dict(
            x=0.1, 
            y=1.1,  
            orientation='h' 
                    )
                )

   
            fig = go.Figure(data=[trace1, trace2], layout=layout)
            st.plotly_chart(fig)
            ##---------------hogya shukar---------------------------------------------------##

            #------Bonus time muehehe------------------------------####
            stars_1 = filtered_df_1['overall_rating'].value_counts().sort_index()
            stars_2 = filtered_df_2['overall_rating'].value_counts().sort_index()
            overall_Stars = pd.DataFrame({'our_restarunt' :stars_1 , 'compatitor':stars_2}).fillna(0)

            stars_3 = filtered_df_1['food'].value_counts().sort_index()
            stars_4 = filtered_df_2['food'].value_counts().sort_index()
            food_Stars = pd.DataFrame({'our restarunt' :stars_3 , 'compatitor':stars_4}).fillna(0)

            stars_5 = filtered_df_1['service'].value_counts().sort_index()
            stars_6 = filtered_df_2['service'].value_counts().sort_index()
            service_ratings = pd.DataFrame({'our restarunt' :stars_5 , 'compatitor':stars_6}).fillna(0)

            stars_7 = filtered_df_1['ambiance'].value_counts().sort_index()
            stars_8 = filtered_df_2['ambiance'].value_counts().sort_index()
            ambiance_ratings = pd.DataFrame({'our restarunt' :stars_7 , 'compatitor':stars_8}).fillna(0)

            st.markdown('<div class="review-line"></div>', unsafe_allow_html=True)
            st.write('Bonus comparison graph')
            col1, col2 = st.columns(2)
            with col1:
                 st.write('Overall_ratings')
                 st.bar_chart(overall_Stars)
            with col2:
                 st.write('Food ratings')
                 st.bar_chart(food_Stars)

            col3, col4 = st.columns(2)

            with col3:
                 st.write('service ratings')
                 st.bar_chart(service_ratings)
            with col4:
                 st.write('Ambiance ratings')
                 st.bar_chart(ambiance_ratings)

            st.markdown('<div class="review-line"></div>', unsafe_allow_html=True)

        
            final_review = f'''
Food Rating:  
Our Restaurant: {filtered_df_1['food'].sum()}  
Competitor: {filtered_df_2['food'].sum()}   

Ambiance Rating:
Our Restaurant:{filtered_df_1['ambiance'].sum()} 
Competitor:{filtered_df_2['ambiance'].sum()}  

Service Rating: 
Our Restaurant:{filtered_df_1['service'].sum()} 
Competitor:{filtered_df_2['service'].sum()} 

Overall Rating: 
ur Restaurant:{filtered_df_1['overall_rating'].sum()}  
Competitor: {filtered_df_2['overall_rating'].sum()} 
'''
            
            st.text_area("Overall Review", final_review, height=350, disabled=True)
            save_review= st.checkbox('Save the review')
            if (save_review):
                with open('final_review.txt','w') as file:
                    file.write(final_review)
                file.close() 
                st.success('file saved')

if navigation_bar == 'About' :
    st.markdown("# 🍴 Welcome to **Restaurant Review Analyzer**! - Created By : Mohammad Ibrahim 23i0083" )
    st.markdown("""
    **🔍 What is About?**  
    This app **analyzes restaurant reviews** from Open Table, compares **food 🍔**, **service 🍽️**, and **ambiance 🎶**, and provides a detailed Analysis to help you make the best dining choices!  

    ---

    ### **📊 Key Features:**  
    - ✅**Use of AI for Review seperation**: Utilizes AI to seperate food and service comments in Reviews and Censor Private Information
    - ✅ **Detailed Ratings Analysis:** Compare overall ratings, food quality, and service experience.  
    - 📈 **Time-Series Graphs:** Visualize restaurant performance over time.  
    - 💾 **Save Reviews:** Save analysis results for future reference.  


    ---

    ### **✨ Why Use This App?**  
    - 🔥 **Accurate Insights:** Get a comprehensive view of restaurant performance.  
    - ⚡ **Realiable and encrypted** Filters out any personal information about the customer.  
    - 🧑‍💻 **User-Friendly Interface:** Easy to use, even for beginners!  

    ---

    ### **📢 Let's Get Started!**  
    Use the **menu** above to explore various features of the app.  
    We hope you enjoy your experience! 🎉
    """, unsafe_allow_html=True)
                
            




            

                


    


       
           
           




       




