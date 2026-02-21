LANG = {
    "ui": {
        "instructions": "Create a magical storybook for your child. Fill in ALL the details, make payment and download.",
        "language_label": "Language",
        "form_header": "Story Inputs",
        "child_name": "Child's Name",
        "child_age": "Child's Age",
        "interests": "Topics of Interest",
        "objective": "Story Objective",
        "author_name": "Author Name",
        "email": "Parent Email",
        "page_length": "Choose Book Length",
        "help": "Pricing: $0.99 (4 pages), $1.99 (8 pages), $2.99 (12 pages)",
        "continue_to_payment": "Continue to Payment",
        "intake_saved": "Intake saved. Please proceed to payment.",
        "step_2": "Step 2 — Pay with PayPal",
        "pre_payment_info": "You selected **{page_length} pages** ({price}). After payment, please go to the Download page to generate and download your PDF.",
        "pay_button": "Pay",
        "generate": "Generate Story",
        "error_missing_fields": "Please fill in at least the child's name and your email.",
        "submit_success": "Thank you! We are generating your magical story now. This may take a moment and please do not close this page. Please expect an email in about 5 minutes. If it's not in your inbox, kindly check your Spam or Promotions folder.",
        "spinner": "Generating story & sending to your email...",
        "success": "Story generated successfully!",
        "home_help": "👉 Need help? Visit the 'How To Use' page in the sidebar.",
        "how_subtitle": "🧸 How It Works",
        "how_steps": (
            "1. Fill in your child's details on the **Home** page  \n"
            "2. Make payment via the **Continue to Payment** button  \n"
            "3. Our system generates an illustrated storybook into a PDF after the payment is completed  \n"
            "4. You can download the final storybook under the **Download** page in about **5 minutes**"
        ),
        "faq_subtitle": "💬 Frequently Asked Questions",
        "faq_cost_question": "How much does it cost me to generate a personalized story book?",
        "faq_cost_answer": "You will be able to see the price for each book length on the Home page. After you click the Continue to Payment button, you will be directed to PayPal to complete the payment. After payment is completed, you can go to the Download page to generate and download your PDF.",
        "faq_time_question": "How long does it take?",
        "faq_time_answer": "Around 5 to 15 minutes depending on server load.",
        "faq_delivery_question": "Where will I receive the storybook?",
        "faq_delivery_answer": "You will be able to download the storybook PDF from the Download page after payment and generation completion.",
        "faq_delivery_error_question": "What if I can't download the storybook?",
        "faq_delivery_error_answer": (
            "Please try again or contact support if the issue persists."
        ),
        "faq_data_question": "Is my child's data safe?",
        "faq_data_answer": "Yes. No data is shared or used for any purpose besides generating the storybook.",
        "faq_volume_question": "Can I request multiple stories?",
        "faq_volume_answer": "Yes. Feel free to create as many storybooks as you like!",
        "about_subheader": "👋 The Project",
        "about_description": (
            "This project was created to bring joy, imagination, and personalized storytelling "
            "to children and families around the world.  \n"
            "  \n"
            "Each book is generated using AI-powered text, illustration and PDF workflows, "
            "designed with love and care."
        ),
        "support_subheader": "☕ Support My Work",
        "support_description": "If you enjoy the storybooks and want to support ongoing development, consider supporting me on GoGetFunding 👉 **[HERE](https://gogetfunding.com/give-a-child-the-gift-of-their-own-story/)**.",
        "contact_subheader": "📬 Contact",
        "contact_description": (
            "If you need help, feel free to reach out to: jingdu.email@gmail.com"
        ),
        "download_page_title": "Generate & Download",
        "download_no_intake": "No intake found. Please go back to Home and submit the form again.",
        "go_home": "Go to Home",
        "download_intake_found": "✅ Intake found.",
        "page_selected": "Selected pages: **{page_length}**",
        "download_info": "Click below to generate your storybook PDF. Please do not close this tab while generating.",
        "generate_button": "Generate Storybook",
        "spinner": "Generating your storybook... please keep this tab open",
        "generation_complete": "Storybook generation complete! Please download below.",
        "download_button": "Download storybook PDF"
    },

    "prompts": {
        "system": (
            "You are an artful and masterful expert specializing for children storywriting."
            "Write in English. Keep content warm, imaginative, and age-appropriate."
        ),
        "system_title": (
            "You generate short, creative and catchy titles for children's storybook."
        )
    },

    "email": {
        "subject": "Your personalized storybook",
        "body": (
            f"<p>Hello!</p>"
            f"<p>We have generated the personalized storybook in the PDF attachment.</p>"
            "<p>{audio_link}</p>"
            f"<p>✨ Your personalized children storybook is completely <strong>free to enjoy!</strong> Hope you like it!"
            f"<br/>If you love it and want to support the creator, a small donation would help keep the project growing and allow me to build even more magical features for families.</p>"
            f"<p>💛 Support the project: <a href='https://gogetfunding.com/give-a-child-the-gift-of-their-own-story/'>HERE</a>. Every gesture counts and thank you!</p>"
            f"<p>Best regards,<br/>The StoryGenerator Team</p>"
        ),
        "file_name": "storybook.pdf",
        "send_failure": "Failed to send email: {e}",
        "send_success": "Email sent to {email}! If you don't see it, please check your spam/junk folder."
    },

    "pages": {
        "home": {"title": "Storybook Generator"},
        "how_to_use": {"title": "How to Use"},
        "about_and_support": {"title": "About & Support"},
        "download": {"title": "Generate & Download"}
    }
}

# How to add this into the email body
# f"<br/>Click <a href='{story_audio_url}'>HERE</a> to download the audio book.</p>"