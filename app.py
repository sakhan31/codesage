import logging  
import os  
import json  
import streamlit as st  
import requests  
from git import Repo  
import tempfile  
from databricks.sdk import WorkspaceClient  
from graph_code_migration import load_graph as code_migration_graph  
from graph_repo_analysis import load_graph as repo_analysis_graph  
import glob  
import time  
import threading
import shutil
  
 
# Constants  
DATABRICKS_TOKEN = "<databricks-token>"  
  
# Set up logging  
logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)  


# Function to create TensorFlow serving JSON  
def create_tf_serving_json(data):  
    return {'inputs': {name: data[name].tolist() for name in data.keys()} if isinstance(data, dict) else data.tolist()}  

   
# Function to clear a directory  
def clear_directory(directory):  
    for filename in os.listdir(directory):  
        file_path = os.path.join(directory, filename)  
        if os.path.isdir(file_path):  
            shutil.rmtree(file_path)  
        else:  
            os.remove(file_path)   
  
# Cleanup function  
def cleanup_temp_directory(directory):  
    time.sleep(2 * 60)  # Wait for 30 minutes  
    clear_directory(directory)  
    logger.info(f"Temporary directory {directory} cleaned up.")                
  
# Function to get user info  
def get_user_info():  
    headers = st.context.headers  
    return {  
        'user_name': headers.get("X-Forwarded-Preferred-Username"),  
        'user_email': headers.get("X-Forwarded-Email"),  
        'user_id': headers.get("X-Forwarded-User"),  
    }  

user_detail = get_user_info()  
user_name=user_detail.get('user_name') 

if 'previous_operation' not in st.session_state:  
    st.session_state.previous_operation = None 
    
if 'repo_path' not in st.session_state:  
    st.session_state.repo_path = None  
  
if 'repo_time' not in st.session_state:  
    st.session_state.repo_time = None    

if 'chat_history' not in st.session_state:  
    st.session_state.chat_history = []  

 # Create a temporary directory and store it in session state  
if 'temp_dir' not in st.session_state:  
    st.session_state.temp_dir = tempfile.mkdtemp()   
        # Start cleanup thread  
    cleanup_thread = threading.Thread(target=cleanup_temp_directory, args=(st.session_state.temp_dir,))  
    cleanup_thread.start()   
  
# Sidebar for user info  
# with st.sidebar:  
#     user_detail = get_user_info()  
#     st.markdown(  
#     '''  
#     <div style="display: flex; align-items: center;">  
#         <h1 style="color: #34a853; margin: 0; padding-left: 40px;">HackioBros</h1>  
#     </div>  
#     ''', unsafe_allow_html=True  
# )   
#     st.write(f"Hello {user_detail.get('user_name')}!")  
# Sidebar for user info  
with st.sidebar:  
    user_detail = get_user_info()  
  
    # Sidebar Title with a logo/icon  
    st.markdown(  
        '''  
        <div style="display: flex; align-items: center; padding: 10px;">  
            <h1 style="color: #34a853; margin: 0;">HackioBros</h1>  
        </div>  
        ''', unsafe_allow_html=True  
    )  
  
    # Greeting message with styling  
    st.markdown(  
        f'''  
        <div style="padding: 10px; background-color: #f0f0f0; border-radius: 5px;">  
            <h3 style="color: #333;">Hello, {user_detail.get('user_name')}!</h3>  
        </div>  
        ''', unsafe_allow_html=True  
    )  
  
    # Additional sidebar options  
    st.markdown("<hr>", unsafe_allow_html=True)  # Horizontal line for separation  
    # st.subheader("Options")  
    # st.write("Select your preferences:")  
      
    # # Example options  
    # option1 = st.checkbox("Enable Notifications")  
    # option2 = st.selectbox("Select Theme", ["Light", "Dark"])  
      
    st.markdown("<hr>", unsafe_allow_html=True)  # Another horizontal line for separation  
    st.write("About CodeSage:")  
    st.write("Your friendly code assistant for migration and analysis.")  


# Main app layout  
st.markdown('<h1 style="color: #ff6347;">CodeSage</h1>', unsafe_allow_html=True)  
# st.markdown(  
#     '''  
#     <div style="display: flex; align-items: center;">  
#         <h1 style="color: #ff6347; margin: 0;">CodeSage</h1>  
#         <h1 style="color: #34a853; margin: 0; padding-left: 40px;">HackioBros</h1>  
#     </div>  
#     ''', unsafe_allow_html=True  
# )   

# Add columns for better layout  
col1, col2 = st.columns(2)  
  
with col1:  
    operation = st.radio("Select an option:", ('Code Migration', 'Repo-analysis'), index=0)  
    if st.session_state.previous_operation != operation:  
        st.session_state.chat_history = []  # Reset chat history  
        st.session_state.previous_operation = operation  # Update previous operation  
  
    string_data = ""  
    if operation == 'Code Migration': 
        file_source = st.radio("Select file source:", ('Upload'), index=0)  
        if file_source == 'Upload':  
            uploaded_file = st.file_uploader("Choose a file")  
            if uploaded_file is not None:  
                bytes_data = uploaded_file.getvalue()  
                string_data = bytes_data.decode("utf-8")  
    else:  # For repo-analysis  

        file_source = st.radio("Select file source:", ('Azure DevOps Git'), index=0)  
        with st.expander("Azure DevOps Git Authentication", expanded=True):  
            organization = st.text_input("Enter your organization name", "PACE-DevOps")  
            project = st.text_input("Enter your project name", "HSES-LLM-OpenAI")  
            repository_id = st.text_input("Enter your repository name", "HSES-LLM-OpenAI")  
            pat = st.text_input("Enter your personal access token", type='password')  
            folder_id = user_detail.get('user_name')  
            directory_name = f'{folder_id}/code_sages'  
  
            if organization and project and repository_id and pat:  
                local_repo_path = st.session_state.temp_dir  # Use the temp directory from session state  
                clear_directory(local_repo_path) 
                clone_url = f"https://{pat}@dev.azure.com/{organization}/{project}/_git/{repository_id}"  
                Repo.clone_from(clone_url, local_repo_path)  
                st.write("The repository has been successfully cloned! Just a heads-up: it will be automatically deleted after 30 minutes. Feel free to clone it again once the time's up!") 
  
 
  
# Display chat history  
for msg in st.session_state.chat_history:  
    with st.chat_message(msg['role']):  
        st.markdown(msg['content'])  

# tempfile.cleanup()
 
# Accept user input  
if user_input := st.chat_input("What is up?"):  
    # Store user message  
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    local_repo_path = st.session_state.temp_dir  
  
    # Handle operations based on user selection  
    if operation == 'Code Migration':  
        system_prompt = """You are an expert in answering questions related to code migration and analysis.  
        When asked for code migration, follow below set of instructions:  
        1. Use the appropriate migration tools from the list of tools provided.  
        2. Write the content to a file always using the write_file_content tool.  
        3. Provide the migrated code and explanation as output.  
        When asked for code analysis, follow below set of instructions:  
        1. Use the appropriate analysis tools from the list of tools provided.  
        2. Provide the analysis as output.  
        """  
        app = code_migration_graph()  
        prompt = user_input + f"\nContent: {string_data}" 

    elif operation == "Repo-analysis":  
        system_prompt = f"""You are an expert in code migration and file navigation. You are always provided with the current working directory.
        You have access to a set of tools that can help you navigate directories, list files, read file content, and migrate code between different formats.
        Your goal is to assist users in finding the file path of a specific file in a directory structure.
        You can also help users convert code between different programming languages.
 
        If the user asks to migrate files available in folder, you will first need to find the folder path using list_all_directories tool.Do include temp path in response
 
        Your current working directory is {local_repo_path}.
        """
        app = repo_analysis_graph()  
        prompt = user_input 
  
    query = {  
        "messages": [  
            {"role": "system", "content": system_prompt},  
            {"role": "user", "content": prompt}  
        ]  
    }  
    write_file_dir = tempfile.mkdtemp()  
    config = {"configurable": {"directory": write_file_dir}}  
  
    # Display user message in chat message container  
    with st.chat_message("user"):  
        st.markdown(user_input)  
  
    # Display assistant response in chat message container  
    with st.chat_message("assistant"):  
        try:  
            for chunk in app.stream(
                {"messages": [
                    ("system", system_prompt),
                    ("human", prompt)]},
                config=config, stream_mode="values"):
                chunk["messages"][-1].pretty_print()
            # response = app.invoke(query, config=config)
            last_message_content = chunk['messages'][-1].content
            # response = app.invoke(query, config=config)  
            st.session_state.chat_history.append({"role": "assistant", "content": last_message_content})  
            st.markdown(last_message_content)  
            # tempfile.cleanup()
        except Exception as e:  
            st.error(f"Error querying model: {e}")  
  
    # Add download button after response for code migration  
    if operation == 'Code Migration':  
        file_pattern = os.path.join(write_file_dir, 'output.*')  
        matching_files = glob.glob(file_pattern)  
        if matching_files:  
            file_path = matching_files[0]  
            if os.path.exists(file_path):  
                with open(file_path, 'rb') as file:  
                    file_data = file.read()  
                    file_name = os.path.basename(file_path)  
                    if st.download_button(label="Download File", data=file_data, file_name=file_name, mime='application/octet-stream'):  
                        # Delete the file after downloading  
                        os.remove(file_path)  
                        st.success(f"File {file_name} downloaded and deleted successfully.")