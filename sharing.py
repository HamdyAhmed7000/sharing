import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import base64
import os
from uuid import uuid4
from datetime import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import altair as alt

st.set_page_config(page_title="PDF & Excel ANALYZER", layout="wide")

# Set OpenAI API Key
os.environ["OPENAI_API_KEY"] = "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"
model = ChatOpenAI(model_name="gpt-4", temperature=0)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_archive" not in st.session_state:
    st.session_state.chat_archive = []
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = str(uuid4())
if "excel_data_text" not in st.session_state:
    st.session_state.excel_data_text = ""
if "df" not in st.session_state:
    st.session_state.df = None

# Sidebar with chat archive and New Chat
st.sidebar.title("💬 PDF & Excel ANALYZER")
if st.sidebar.button("➕ New Chat"):
    st.session_state.chat_archive.append({
        "id": st.session_state.active_chat_id,
        "messages": st.session_state.messages.copy(),
        "title": next((part["text"] for msg in st.session_state.messages if isinstance(msg, HumanMessage) for part in msg.content if part["type"] == "text"), "Untitled")
    })
    st.session_state.messages = []
    st.session_state.active_chat_id = str(uuid4())
    st.session_state.excel_data_text = ""
    st.session_state.df = None

# Display archived chats
st.sidebar.subheader("📁 Archives")
for chat in st.session_state.chat_archive:
    if st.sidebar.button(f"𞴂 {chat.get('title', 'Untitled')}", key=chat.get("id", str(uuid4()))):
        st.session_state.messages = chat["messages"]
        st.session_state.active_chat_id = chat["id"]

# File upload at the top
st.title("📄 Upload File")
uploaded_file = st.file_uploader("Upload a PDF or Excel file", type=["pdf", "xlsx"], label_visibility="collapsed")

# File validation and error handling
if uploaded_file is not None:
    st.markdown(f"**Uploaded:** {uploaded_file.name}")
    
    # Check if file type is valid
    if uploaded_file.name.endswith(".xlsx"):
        try:
            # Check file size (for large files)
            if uploaded_file.size > 10 * 1024 * 1024:  # 10 MB limit
                st.error("The file size is too large. Please upload a file smaller than 10MB.")
            else:
                # Try reading the Excel file
                df = pd.read_excel(uploaded_file)
                
                # Check if the DataFrame is empty
                if df.empty:
                    st.error("The uploaded Excel file is empty. Please upload a valid Excel file with data.")
                else:
                    # Check if required columns are missing (optional)
                    required_columns = ['Column1', 'Column2']  # Example required columns
                    missing_cols = [col for col in required_columns if col not in df.columns]
                    if missing_cols:
                        st.warning(f"Warning: The following required columns are missing: {', '.join(missing_cols)}")
                    
                    # Save DataFrame to session state
                    st.session_state.df = df
                    st.dataframe(df)
                    st.session_state.excel_data_text = df.to_markdown(index=False)
        except Exception as e:
            st.error(f"An error occurred while reading the Excel file: {e}")
    
    else:
        st.error("Invalid file format! Please upload an Excel file (.xlsx).")

else:
    st.session_state.excel_data_text = ""
    st.session_state.df = None

# --- Interactive Excel Data Exploration Section ---

if st.session_state.df is not None:
    st.subheader("🔍 Explore the Data")
    
    # Filter Data by Column
    st.write("### Filter Data")
    columns = st.session_state.df.columns.tolist()
    selected_column = st.selectbox("Select a column to filter by", columns)
    unique_values = st.session_state.df[selected_column].dropna().unique().tolist()
    selected_value = st.selectbox(f"Select a value from {selected_column}", unique_values)
    
    filtered_df = st.session_state.df[st.session_state.df[selected_column] == selected_value]
    st.write(f"**Filtered Data (based on {selected_column} = {selected_value}):**")
    st.dataframe(filtered_df)
    
    # Column Selection for Analysis
    st.write("### Column Selection for Analysis")
    selected_columns_for_analysis = st.multiselect(
        "Select columns to analyze", options=columns, default=columns[:2]
    )
    
    if selected_columns_for_analysis:
        st.write("### Analyzed Data")
        st.dataframe(st.session_state.df[selected_columns_for_analysis])

    # Data Cleaning: Remove duplicates or fill missing values
    st.write("### Data Cleaning Options")
    clean_option = st.selectbox("Choose a cleaning option", options=["None", "Remove Duplicates", "Fill Missing Values"])
    
    if clean_option == "Remove Duplicates":
        cleaned_df = st.session_state.df.drop_duplicates()
        st.write("Duplicates removed:")
        st.dataframe(cleaned_df)
    elif clean_option == "Fill Missing Values":
        fill_value = st.selectbox("Choose fill value", options=["None", "Mean", "Median", "Mode"])
        if fill_value != "None":
            if fill_value == "Mean":
                filled_df = st.session_state.df.fillna(st.session_state.df.mean())
            elif fill_value == "Median":
                filled_df = st.session_state.df.fillna(st.session_state.df.median())
            elif fill_value == "Mode":
                filled_df = st.session_state.df.fillna(st.session_state.df.mode().iloc[0])
            st.write(f"Missing values filled with {fill_value}:")
            st.dataframe(filled_df)
        else:
            st.write("No data cleaning applied.")

# Graphs Section - Plotly, Seaborn, Altair
if st.session_state.df is not None:
    with st.expander("📊 Show Graphs"):
        numeric_cols = st.session_state.df.select_dtypes(include='number').columns.tolist()
        
        if numeric_cols:
            chart_type = st.selectbox("Select Graph Type", options=["Line Chart", "Bar Chart", "Scatter Plot", "Pie Chart", "Heatmap", "Altair Chart"])

            x_axis = st.selectbox("X-axis", options=numeric_cols)
            y_axis = st.selectbox("Y-axis", options=numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
            
            if chart_type == "Line Chart" and st.button("Plot Line Graph"):
                fig = px.line(st.session_state.df, x=x_axis, y=y_axis, title=f"{y_axis} over {x_axis}")
                st.plotly_chart(fig)

            elif chart_type == "Bar Chart" and st.button("Plot Bar Graph"):
                fig = px.bar(st.session_state.df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
                st.plotly_chart(fig)

            elif chart_type == "Scatter Plot" and st.button("Plot Scatter Graph"):
                fig = px.scatter(st.session_state.df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
                st.plotly_chart(fig)

            elif chart_type == "Pie Chart" and st.button("Plot Pie Chart"):
                pie_data = st.session_state.df.groupby(x_axis).sum().reset_index()
                fig = px.pie(pie_data, names=x_axis, values=y_axis, title=f"{y_axis} Distribution")
                st.plotly_chart(fig)

            elif chart_type == "Heatmap" and st.button("Plot Heatmap"):
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.heatmap(st.session_state.df.corr(), annot=True, cmap="coolwarm", ax=ax)
                st.pyplot(fig)

            elif chart_type == "Altair Chart" and st.button("Plot Altair Graph"):
                chart = alt.Chart(st.session_state.df).mark_point().encode(
                    x=x_axis,
                    y=y_axis,
                    color=x_axis
                ).properties(
                    title=f"{y_axis} vs {x_axis} (Altair)"
                )
                st.altair_chart(chart, use_container_width=True)

# Fixed input at bottom
with st.container():
    user_input = st.chat_input("Ask a question...")
    if user_input:
        # Compose message
        hidden_context = f"The following Excel data is provided for analysis:\n{st.session_state.excel_data_text}\n"
        full_prompt = hidden_context + f"User Question: {user_input}"

        message_content = [
            {"type": "text", "text": full_prompt}
        ]

        human_msg = HumanMessage(content=message_content)
        st.session_state.messages.append(HumanMessage(content=[{"type": "text", "text": user_input}]))

        with st.spinner("⏳ GPT is typing..."):
            time.sleep(0.5)
            try:
                response = model.invoke([human_msg])
                st.session_state.messages.append(AIMessage(content=response.content))
            except Exception as e:
                st.error(f"An error occurred: {e}")
