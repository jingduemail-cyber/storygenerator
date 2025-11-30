# --- Set up global page formatting and styles ---
import streamlit as st

st.set_page_config(
    page_title="Personalized Storybook Generator",
    page_icon="📚",
    layout="centered"
)

# Global CSS for clean, modern UI
st.markdown("""
<style>
    .main-title {
        font-size: 40px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 20px;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 24px;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Create About and Support page ---
st.set_page_config(page_title="About", page_icon="💛")

st.markdown("<h1 class='main-title'>💛 About This Project</h1>", unsafe_allow_html=True)
st.write("---")

st.markdown("""
### 👋 Hello!

This project was created to bring joy, imagination, and personalized storytelling 
to children and families around the world.

Each book is generated using AI-powered text, illustration, audio and PDF workflows, 
designed with love and care.

""")

st.write("---")
st.header("☕ Support My Work")

st.markdown("""
If you enjoy the storybooks and want to support ongoing development,  
consider supporting me on Give.Asia.

**Your support keeps this project running** 💛  
""")

st.markdown("""
**Give.Asia:**  
👉 https://give.asia/help-jing-0828
""")

st.write("---")
st.header("📬 Contact")

st.markdown("""
If you need help, feel free to reach out:  
**jingdu.email@gmail.com**
""")
