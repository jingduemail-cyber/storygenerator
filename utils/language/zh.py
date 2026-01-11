LANG = {
    "ui": {
        "instructions": "为孩子定制魔法故事书，请填写所有信息后邮箱收取。",
        "language_label": "语言",
        "form_header": "故事输入",
        "child_name": "孩子的名字",
        "child_age": "孩子的年龄",
        "interests": "喜欢的主题",
        "objective": "故事目标",
        "author_name": "作者姓名",
        "email": "家长邮箱",
        "generate": "生成故事",
        "error_missing_fields": "请至少填写孩子的名字和您的电子邮件。",
        "submit_success": "谢谢！我们正在为您生成神奇的故事。这可能需要一些时间，请不要关闭此页面。请在大约5分钟内查收电子邮件。如果没有收到，请检查您的垃圾邮件或促销文件夹。",
        "spinner": "正在生成故事并发送到您的邮箱...",
        "success": "故事生成成功！",
        "home_help": "👉 需要帮助？请访问侧边栏的“使用说明”页面。",
        "how_subtitle": "🧸 它是如何运作的",
        "how_steps": (
            "1. 在**首页**填写您孩子的详细信息  \n"
            "2. 点击**生成故事书**  \n"
            "3. 我们的系统将生成故事文本、插图、音频并打包成PDF  \n"
            "4. 您将在大约**15分钟**内收到最终的故事书"
        ),
        "faq_subtitle": "💬 常见问题解答",
        "faq_cost_question": "生成个性化故事书需要多少钱？",
        "faq_cost_answer": "完全免费。请享用！",
        "faq_time_question": "需要多长时间？",
        "faq_time_answer": "大约10到15分钟，具体取决于服务器负载。",
        "faq_delivery_question": "我将在何处收到故事书？",
        "faq_delivery_answer": "在您在表单中输入的电子邮件地址。如果您没有在收件箱中看到，请检查您的垃圾邮件或促销文件夹。",
        "faq_delivery_error_question": "如果我没有收到故事书怎么办？",
        "faq_delivery_error_answer": (
            "- 检查您的垃圾邮件或促销文件夹。  \n"
            "- 确保您的电子邮件地址输入正确。  \n"
            "- 如果问题仍然存在，请重试或联系支持。"
        ),
        "faq_data_question": "我孩子的数据安全吗？",
        "faq_data_answer": "是的。除了生成故事书外，不会共享或将数据用于任何其他目的。",
        "faq_volume_question": "我可以请求多本故事吗？",
        "faq_volume_answer": "可以。随时创建您喜欢的故事书！",
        "about_subheader": "👋 关于该项目",
        "about_description": (
            "该项目旨在为世界各地的儿童和家庭带来欢乐、想象力和个性化的故事讲述。  \n"
            "  \n"
            "每本书都是使用AI驱动的文本、插图、音频和PDF工作流程生成的，"
            "充满爱心和关怀。"
        ),
        "support_subheader": "☕ 支持我的工作",
        "support_description": "如果您喜欢这些故事书并希望支持持续的发展，请考虑在GoGetFunding上支持我 👉 **[点击这里](https://gogetfunding.com/give-a-child-the-gift-of-their-own-story/)**。",
        "contact_subheader": "📬 联系方式",
        "contact_description": (
            "如果您需要帮助，请随时联系：jingdu.email@gmail.com"
        )
    },

    "prompts": {
        "system": (
            "你是一位富有创意的儿童故事作家。"
            "请使用简体中文，语言温暖、有想象力，适合儿童阅读。"
        ),
        "system_title": (
            "你为儿童故事书生成简短、有创意且吸引人的标题。"
        )
    },

    "email": {
        "subject": "您的个性化儿童故事书",
        "body": (
            f"<p>您好！</p>"
            f"<p>我们已生成了个性化故事书，请见附件中的PDF文件。"
            "<p>{audio_link}</p>"
            f"<p>✨ 您的个性化儿童故事书完全免费享用！希望您喜欢它！"
            f"<br/>如果您喜欢并想支持创作者，小额捐款将有助于项目的发展，并让我能够为家庭构建更多神奇的功能。</p>"
            f"<p>💛 支持该项目：<a href='https://gogetfunding.com/give-a-child-the-gift-of-their-own-story/'>点击这里</a>。每一份心意都值得感谢！</p>"
            f"<p>此致，<br/>故事生成器团队</p>"
        ),
        "file_name": "故事书.pdf",
        "send_failure": "发送邮件失败：{e}",
        "send_success": "邮件已发送至 {email}！如果您没有看到，请检查您的垃圾邮件/垃圾文件夹。"
    },

    "pages": {
        "home": {"title": "故事书生成器"},
        "how_to_use": {"title": "使用说明"},
        "about_and_support": {"title": "关于与支持"}
    }
}
