# v1 build for story generator app
import os
from dotenv import find_dotenv, load_dotenv
import openai
import streamlit as st

load_dotenv(find_dotenv())

openai.api_key = os.getenv("OPENAI_API_KEY")

st.header("Personalized Children Story Generator")

your_name = st.text_input('Your Name')
your_email = st.text_input('Your Email')
child_name = st.text_input('Child Name')
child_age = st.text_input('Child Age')
child_interest = st.text_area('Child Interest (e.g., adventures, animals, science, etc.)')
story_objective = st.text_area('Story Objective (e.g., build courage, teach a lesson, entertain, etc.)')

def app():
    
    if st.button('Generate Story'):
        personalized_story = generate_personalized_story(
            your_name=your_name,
            your_email=your_email,
            child_name=child_name,
            child_age=child_age,
            child_interest=child_interest,
            story_objective=story_objective
        )
        #print(personalized_story)
        with st.expander("Personalized Story"):
            st.text_area("Generated Personalized Story", 
                         personalized_story, height=500)


def generate_personalized_story(your_name,
                                your_email,
                                child_name,
                                child_age,
                                child_interest,
                                story_objective):
    prompt_template = """ 
     Write a personalized story to {child_name}, who is {child_age} years old, and is interested in {child_interest}. 
    The story should aim to {story_objective}. 
    The story should be engaging, age-appropriate, imaginative and tailor to the child's interests.
    Make sure to incorporate the following elements in the personalized story:
        - A captivating beginning that grabs the child's attention.
        - A clear plot with a problem and a resolution.
        - Relatable characters that the child can connect with.
        - Vivid descriptions to stimulate the child's imagination.
        - A positive message or moral that aligns with the story objective.
    At the end of the story, include a short note from {your_name} to {child_name}, encouraging them to embrace the story's message.
    Also, make sure that the personalized story is typo free.
    """
    prompt = prompt_template.format(
         your_name=your_name,
         your_email=your_email,
         child_name=child_name,
         child_age=child_age,
         child_interest=child_interest,
         story_objective=story_objective)
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an artful and masterful expert specializing for children storytelling."},
            {"role": "user", "content": prompt}
           ])
    return response.choices[0].message.content

def main():
    app()
 
    
if __name__ == "__main__":
    main()

