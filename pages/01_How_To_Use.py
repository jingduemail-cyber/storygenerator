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

# --- Set up the how to use and faq page ---
st.set_page_config(page_title="How to Use", page_icon="❓")

st.markdown("<h1 class='main-title'>❓ How to Use This App</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Everything you need to know before getting started</p>", unsafe_allow_html=True)
st.write("---")

st.header("🧸 How It Works")

st.markdown("""
1. Fill in your child's details on the **Home** page  
2. Click **Generate Storybook**  
3. Our system generates story text, illustrations, audio and packed into a PDF  
4. You will receive the final storybook in about **15 minutes**  
""")

st.write("---")
st.header("💬 Frequently Asked Questions")

with st.expander("How much does it cost me to generate a personalized story book?"):
    st.write("It is completely free. Enjoy!")

with st.expander("How long does it take?"):
    st.write("Around 10–15 minutes depending on server load.")

with st.expander("Where will I receive the storybook?"):
    st.write("At the email address you enter in the form. If you don't see it in your inbox, kindly check your Spam or Promotions folder.")

with st.expander("What if I don't receive the storybook?"):
    st.write("""
- Check your Spam or Promotions folder.  
- Ensure your email address was entered correctly.  
- Try again or contact support if the issue persists.
""")

with st.expander("Is my child's data safe?"):
    st.write("Yes. No data is shared or used for any purpose besides generating the storybook.")

with st.expander("Can I request multiple stories?"):
    st.write("Yes, simply submit the form again with different details.")
    
with st.expander("Can I support the StoryGenerator team?"):
    st.write("Yes, if you enjoy the storybooks and want to support ongoing development, consider supporting me on Give.Asia: https://give.asia/help-jing-0828. Thank you!")

