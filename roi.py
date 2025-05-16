import streamlit as st
import altair as alt
import pandas as pd
from fpdf import FPDF  # Import FPDF for PDF generation
import requests  # Import requests for HubSpot API
import io
import plotly.io as pio  # Import plotly.io
import plotly.graph_objects as go  # Import plotly graph objects


st.set_page_config(page_title="X-WAM ROI Calculator", page_icon=":moneybag:", layout="wide")
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.markdown("""
<div class="custom-header">
    <img src="https://trimaxmowers.com/wp-content/uploads/Trimax_Colour.webp" alt="Trimax Logo">
    <div class="nav">
        <a href="#">Products</a>
        <a href="#">Support</a>
        <a href="#">About</a>
        <a href="#">Contact</a>
    </div>
</div>
""", unsafe_allow_html=True)



# Helper functions
def calculate_hours_needed(acres_weekly_goal, effective_width, cutting_speed=4.35):
    acres_per_hour_per_mower = (effective_width / 5280) * cutting_speed * 640
    total_hours = acres_weekly_goal / acres_per_hour_per_mower
    return total_hours

def calculate_num_mowers(total_hours, hours_per_week_per_mower):
    return int(total_hours / hours_per_week_per_mower) + (total_hours % hours_per_week_per_mower > 0)

def calculate_annual_costs(num_mowers, fuel_consumption_rate, labor_rate, hours_per_week, weeks_per_year,
                         capital_cost_per_mower, lifespan_years, autonomy_cost=0, fuel_price=2.5):
    annual_fuel_cost = num_mowers * fuel_consumption_rate * hours_per_week * weeks_per_year * fuel_price
    annual_labor_cost = num_mowers * labor_rate * hours_per_week * weeks_per_year
    annual_capital_cost = (num_mowers * capital_cost_per_mower) / lifespan_years
    total_annual_cost = annual_fuel_cost + annual_labor_cost + annual_capital_cost + autonomy_cost
    return {
        "total_annual_cost": total_annual_cost,
        "annual_fuel_cost": annual_fuel_cost,
        "annual_labor_cost": annual_labor_cost,
        "annual_capital_cost": annual_capital_cost
    }

def calculate_autonomous_costs(num_tractors, overseer_salary, kit_cost, annual_fees, lifespan_years):
    annual_kit_cost = (num_tractors * kit_cost) / lifespan_years
    total_annual_autonomy_cost = overseer_salary + annual_kit_cost + (num_tractors * annual_fees)
    return total_annual_autonomy_cost

# Function to create PDF report
def create_pdf_report(name, email, phone, savings_labor, savings_autonomous, chart_data_labor, chart_data_autonomous):  # Added chart_data
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="X-WAM ROI Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Name: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Email: {email}", ln=True)
    pdf.cell(200, 10, txt=f"Phone: {phone}", ln=True)
    pdf.cell(200, 10, txt="Annual Savings:", ln=True, align='L')
    if savings_labor is not None:
        pdf.cell(200, 10, txt=f"  With Paid Operators: ${savings_labor:,.2f}", ln=True)
    if savings_autonomous is not None:
        pdf.cell(200, 10, txt=f"  With Autonomous Tractor: ${savings_autonomous:,.2f}", ln=True)

    # Add chart to PDF
    if chart_data_labor is not None:
        pdf.cell(200, 10, txt="Annual Cost Comparison (Labor)", ln=True, align='L')
        chart_data_labor.save('chart1.png')
        pdf.image("chart1.png", w=150)

    if chart_data_autonomous is not None:
        pdf.cell(200, 10, txt="Annual Cost Comparison (Autonomous)", ln=True, align='L')
        # Convert Altair chart to Plotly figure
        chart_autonomous_plotly = alt.to_json(chart_data_autonomous)
        # Load the JSON string into a Plotly figure
        fig_autonomous = go.Figure(data=chart_autonomous_plotly)
        # Save Plotly figure to a PNG file
        pio.write_image(fig_autonomous, "chart_autonomous.png")
        pdf.image("chart_autonomous.png", w=150)

    pdf.output("xwam_roi_report.pdf")  #save

def format_variables(**kwargs):
    """
    Formats a dictionary of variables into a string with bold keys, similar to the provided format.

    Args:
        **kwargs: A dictionary of variables.  The keys are variable names,
                  and the values are their corresponding values.

    Returns:
        A string with each variable formatted as "**Variable Name:** Value"
        and separated by newlines.
    """
    formatted_string = ""
    for key, value in kwargs.items():
        # Capitalize the key and surround it with bold markdown
        formatted_key = f"<strong>{key.replace('_', ' ').title()}</strong>"  # Replace underscores and title case
        formatted_string += f"<p>{formatted_key}: {value}</p>"
    return formatted_string.strip()  # Remove trailing newline

def send_data_to_hubspot2(name, email, phone, weekly_goal, working_days, hours_per_day, mower_width_24ft, mower_width_38ft,
                        capital_cost_24ft, capital_cost_38ft, operation_type, labor_rate, fuel_consumption_24ft,
                        fuel_consumption_38ft, overseer_salary, kit_cost, annual_fees):
    print(email)
    print(phone)
    print(name)

# Function to send data to HubSpot
def send_data_to_hubspot(name, email, phone, weekly_goal, working_days, hours_per_day, mower_width_24ft, mower_width_38ft,
                        capital_cost_24ft, capital_cost_38ft, operation_type, labor_rate, fuel_consumption_24ft,
                        fuel_consumption_38ft, overseer_salary, kit_cost, annual_fees):
    # Replace with your actual HubSpot API key and form ID
    HUBSPOT_API_KEY = st.secrets["hubspot"]["api_key"]  #chage
    HUBSPOT_FORM_ID = "YOUR_HUBSPOT_FORM_ID"  #change
    HUBSPOT_PORTAL_ID = "YOUR_HUBSPOT_PORTAL_ID" #change

    url = f"https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HUBSPOT_API_KEY}"
    }

    my_variables = {
        "weekly_goal": weekly_goal,
        "working_days": working_days,
        "hours_per_day": hours_per_day,
        "mower_width_24ft": mower_width_24ft,
        "mower_width_38ft": mower_width_38ft,
        "capital_cost_24ft": capital_cost_24ft,
        "capital_cost_38ft": capital_cost_38ft,
        "operation_type": operation_type,
        "labor_rate": labor_rate,
        "fuel_consumption_24ft": fuel_consumption_24ft,
        "fuel_consumption_38ft": fuel_consumption_38ft,
        "overseer_salary": overseer_salary,
        "kit_cost": kit_cost,
        "annual_fees": annual_fees,
    }

    formatted_output = format_variables(**my_variables)

    data = {
        "properties": {
            "email": email,
            "firstname": name,
            "phone": phone,
            "input_data": formatted_output
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        print("Data sent to HubSpot successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to HubSpot: {e}")
        st.error(f"Failed to send data to HubSpot. Please check your connection and try again. Error Details: {e}")


def main():
    
    st.title("X-WAM ROI Calculator")
    st.markdown("Calculate the potential return on investment (ROI) of using X-WAM mowers.",
                    unsafe_allow_html=True)

    # --- Input Columns ---
    col1, col2, col3 = st.columns(3)
    with st.container():
        with col1:
            st.header("Running & Capital Cost")
            weekly_goal = st.number_input("Weekly Goal (acres)", value=2000.0, min_value=100.0, max_value=10000.0, step=100.0)
            working_days = st.number_input("Working Days per Week", value=5, min_value=1, max_value=7, step=1)
            hours_per_day = st.number_input("Hours per Day", value=7, min_value=1, max_value=24, step=1)
            hours_per_week_per_mower = working_days * hours_per_day
            weeks_per_year = 52
            lifespan_years = st.number_input("Mower Life", value=7, min_value=1, max_value=15, step=1)

            # --- Mower Width Selection ---
            
            mower_width_38ft = 37

            # --- Capital Costs ---
            capital_cost_24ft = st.slider("Capital Cost Of Current Machine ($)", min_value=50000, max_value=300000,
                                            value=138000, step=5000)
            mower_width_24ft = st.number_input("Current Mower Width", value=24, min_value=1, max_value=38, step=1)
            capital_cost_38ft = 175000
            #st.slider("Capital Cost for 38ft Mower ($)", min_value=100000, max_value=500000,value=175000, step=5000)
        
        with col2:
            st.header("Operation Details")
            # --- Operation Type Selection ---
            operation_type = st.radio("Operation Type", ["Labor", "Autonomous"], index=0)

            # --- Labor Rate ---
            if operation_type == "Labor":
                labor_rate = st.slider("Hourly Labor Rate ($/hr)", min_value=10, max_value=50, value=24, step=1)
            else:
                labor_rate = 0

            # --- Fuel Consumption ---
            fuel_consumption_24ft = st.number_input("Fuel Consumption Rate 24ft (gal/hr)", value=4.0, min_value=1.0,
                                                    max_value=10.0, step=0.1)
            fuel_consumption_38ft = st.number_input("Fuel Consumption Rate 38ft (gal/hr)", value=4.75, min_value=1.0,
                                                    max_value=10.0, step=0.1)

            # --- Autonomous Costs ---
            if operation_type == "Autonomous":
                overseer_salary = st.number_input("Overseer Annual Salary ($)", value=80000, min_value=0, step=10000)
                kit_cost = st.number_input("Autonomous Kit Cost per Tractor ($)", value=75000, min_value=0, step=10000)
                annual_fees = st.number_input("Annual Fees per Tractor ($)", value=20000, min_value=0, step=1000)
            else:
                overseer_salary = 0
                kit_cost = 0
                annual_fees = 0

    # --- Calculations ---
    # 24 ft Mower Calculations
    total_hours_24ft = calculate_hours_needed(weekly_goal, mower_width_24ft)
    num_mowers_24ft = calculate_num_mowers(total_hours_24ft, hours_per_week_per_mower)

    # 38 ft Mower Calculations
    total_hours_38ft = calculate_hours_needed(weekly_goal, mower_width_38ft)
    num_mowers_38ft = calculate_num_mowers(total_hours_38ft, hours_per_week_per_mower)

    savings_labor = None
    savings_autonomous = None
    if operation_type == "Labor":
        # --- Scenario 1: Hourly Labor ---
        costs_24_labor = calculate_annual_costs(num_mowers_24ft, fuel_consumption_24ft, labor_rate,
                                                hours_per_week_per_mower,
                                                weeks_per_year, capital_cost_24ft, lifespan_years)
        costs_38_labor = calculate_annual_costs(num_mowers_38ft, fuel_consumption_38ft, labor_rate,
                                                hours_per_week_per_mower,
                                                weeks_per_year, capital_cost_38ft, lifespan_years)
        savings_labor = costs_24_labor["total_annual_cost"] - costs_38_labor["total_annual_cost"]
        savings_percentage_labor = (savings_labor / costs_24_labor["total_annual_cost"]) * 100
        result_text = f"A Trimax 38ft mower will provide <h3>{savings_percentage_labor:.2f}%</h3> increased efficiency/cost savings equating to <b>${savings_labor:,.2f}.</b>"
        if savings_percentage_labor < 0:
            result_text = "Please consider adjusting inputs or contact us for a detailed analysis."

    elif operation_type == "Autonomous":
        # --- Scenario 2: Autonomous Tractor with Mowers ---
        autonomy_cost_24 = calculate_autonomous_costs(num_mowers_24ft, overseer_salary, kit_cost, annual_fees,
                                                        lifespan_years)
        autonomy_cost_38 = calculate_autonomous_costs(num_mowers_38ft, overseer_salary, kit_cost, annual_fees,
                                                        lifespan_years)

        costs_24_auto = calculate_annual_costs(num_mowers_24ft, fuel_consumption_24ft, 0, hours_per_week_per_mower,
                                                weeks_per_year, capital_cost_24ft, lifespan_years, autonomy_cost_24)
        costs_38_auto = calculate_annual_costs(num_mowers_38ft, fuel_consumption_38ft, 0, hours_per_week_per_mower,
                                                weeks_per_year, capital_cost_38ft, lifespan_years, autonomy_cost_38)
        savings_autonomous = costs_24_auto["total_annual_cost"] - costs_38_auto["total_annual_cost"]
        savings_percentage_autonomous = (savings_autonomous / costs_24_auto["total_annual_cost"]) * 100
        result_text = f"A Trimax 38ft mower will provide <h3>{savings_percentage_autonomous:.2f}%</h3> increased efficiency/cost savings equating to <b>${savings_autonomous:,.2f}.</b>"
        if savings_percentage_autonomous < 0:
            result_text = "Please consider adjusting inputs or contact us for a detailed analysis."
    
    else:
        result_text = "Please select operation type."

    # --- Output ---
    with col3:
        st.header("Results")
        st.markdown(result_text, unsafe_allow_html=True)


        chart_labor = None
        chart_autonomous = None
        if operation_type == "Labor":
            chart_data_labor = pd.DataFrame({
                'Mower Size': ['24ft', '38ft'],
                'Annual Cost': [costs_24_labor["total_annual_cost"], costs_38_labor["total_annual_cost"]]
            })
            chart_labor = alt.Chart(chart_data_labor).mark_bar().encode(
                x='Mower Size',
                y='Annual Cost',
                color='Mower Size',
                tooltip=['Mower Size', 'Annual Cost']
            ).properties(
                title='Annual Cost Comparison (Labor)'
            )
            

        elif operation_type == "Autonomous":
            chart_data_autonomous = pd.DataFrame({
                'Mower Size': ['24ft', '38ft'],
                'Annual Cost': [costs_24_auto["total_annual_cost"], costs_38_auto["total_annual_cost"]]
            })
            chart_autonomous = alt.Chart(chart_data_autonomous).mark_bar().encode(
                x='Mower Size',
                y='Annual Cost',
                color='Mower Size',
                tooltip=['Mower Size', 'Annual Cost']
            ).properties(
                title='Annual Cost Comparison (Autonomous)'
            )
            
        else:
            chart_data_labor = None
            chart_data_autonomous = None

        disable_report_button = (
            (operation_type == "Labor" and savings_percentage_labor < 0) or
            (operation_type == "Autonomous" and savings_percentage_autonomous < 0)
        )
        b1, b2 = st.columns(2)
        with b1:
            but1 = st.button('Generate Graph', disabled=disable_report_button)
        with b2:
            but2 = st.button('Contact us')

        if but1:
            if chart_labor is not None:
                st.altair_chart(chart_labor, use_container_width=True)  # Display chart
            if chart_autonomous is not None:
                st.altair_chart(chart_autonomous, use_container_width=True)  # Display chart
            #create_pdf_report("name", "email", "phone", savings_labor, savings_autonomous, chart_labor, chart_autonomous)  # Create PDF with chart data
            #with open("xwam_roi_report.pdf", "rb") as pdf_file:
            #    st.download_button(label="Download Report",
            #                data=pdf_file,
            #                file_name="xwam_roi_report.pdf",
            #                mime="application/pdf",

            #    )
            #st.success("Report generated and ready for download!")

        # Add some CSS for styling
        if "show_user_form" not in st.session_state:
            st.session_state.show_user_form = False
        if "form_submitted" not in st.session_state:
            st.session_state.form_submitted = False     

        if but2:
            st.session_state.show_user_form = True
        if st.session_state.show_user_form:
            st.subheader("User Information")
            name = st.text_input("Name", value=st.session_state.get("name", ""), key="name")
            email = st.text_input("Email", value=st.session_state.get("email", ""), key="email")
            phone = st.text_input("Phone", value=st.session_state.get("phone", ""), key="phone")
            print(phone)
            if st.button("Submit"):
                send_data_to_hubspot(st.session_state["name"], st.session_state["email"], st.session_state["phone"], weekly_goal, working_days, hours_per_day, mower_width_24ft, mower_width_38ft, capital_cost_24ft, capital_cost_38ft, operation_type, labor_rate, fuel_consumption_24ft, fuel_consumption_38ft, overseer_salary, kit_cost, annual_fees)
                st.session_state.form_submitted = True
        
        if st.session_state.form_submitted:
            st.success("Thanks to reaching Trimax support! We will share detailed report soon to your email address.")

if __name__ == "__main__":
    main()
