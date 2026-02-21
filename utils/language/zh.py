LANG = {
    "ui": {
        "instructions": "为孩子定制魔法故事书，请填写所有信息并完成支付后下载。",
        "language_label": "语言",
        "form_header": "故事输入",
        "child_name": "孩子的名字",
        "child_age": "孩子的年龄",
        "interests": "喜欢的主题",
        "objective": "故事目标",
        "author_name": "作者姓名",
        "email": "家长邮箱",
        "page_length": "选择故事书长度",
        "help": "价格：$0.99（4页），$1.99（8页），$2.99（12页）",
        "continue_to_payment": "继续支付",
        "intake_saved": "信息已保存。请继续支付。",
        "step_2": "第二步 — 使用 PayPal 支付",
        "pre_payment_info": "您选择了 **{page_length} 页**（{price}）。支付后，请前往下载页面生成并下载您的PDF。",
        "pay_button": "支付",
        "generate": "生成故事",
        "error_missing_fields": "请至少填写孩子的名字和您的电子邮件。",
        "submit_success": "谢谢！我们正在为您生成神奇的故事。这可能需要一些时间，请不要关闭此页面。请在大约5分钟内查收电子邮件。如果没有收到，请检查您的垃圾邮件或促销文件夹。",
        "spinner": "正在生成故事并发送到您的邮箱...",
        "success": "故事生成成功！",
        "home_help": "👉 需要帮助？请访问侧边栏的“使用说明”页面。",
        "how_subtitle": "🧸 它是如何运作的",
        "how_steps": (
            "1. 在**首页**填写您孩子的详细信息  \n"
            "2. 点击**继续支付**按钮  \n"
            "3. 我们的系统在支付完成后会生成一个带插图的故事书并打包成PDF  \n"
            "4. 您可以在**下载**页面下载最终的故事书PDF，大约需要**5分钟**"
        ),
        "faq_subtitle": "💬 常见问题解答",
        "faq_cost_question": "生成个性化故事书需要多少钱？",
        "faq_cost_answer": "您可以在首页看到每本故事书长度的价格。点击“继续支付”按钮后，您将被引导到PayPal完成支付。支付完成后，您可以前往下载页面生成并下载您的PDF。",
        "faq_time_question": "需要多长时间？",
        "faq_time_answer": "大约5到15分钟，具体取决于服务器负载。",
        "faq_delivery_question": "我将在何处收到故事书？",
        "faq_delivery_answer": "您将能够在支付和生成完成后从下载页面下载故事书PDF。",
        "faq_delivery_error_question": "如果我没有收到故事书怎么办？",
        "faq_delivery_error_answer": (
            "请再试一次，如果问题仍然存在，请联系支持。"
        ),
        "faq_data_question": "我孩子的数据安全吗？",
        "faq_data_answer": "是的。除了生成故事书外，不会共享或将数据用于任何其他目的。",
        "faq_volume_question": "我可以请求多本故事吗？",
        "faq_volume_answer": "可以。随时创建您喜欢的故事书！",
        "about_subheader": "👋 关于该项目",
        "about_description": (
            "该项目旨在为世界各地的儿童和家庭带来欢乐、想象力和个性化的故事讲述。  \n"
            "  \n"
            "每本书都是使用AI驱动的文本、插图和PDF工作流程生成的，"
            "充满爱心和关怀。"
        ),
        "support_subheader": "☕ 支持我的工作",
        "support_description": "如果您喜欢这些故事书并希望支持持续的发展，请考虑在GoGetFunding上支持我 👉 **[点击这里](https://gogetfunding.com/give-a-child-the-gift-of-their-own-story/)**。",
        "contact_subheader": "📬 联系方式",
        "contact_description": (
            "如果您需要帮助，请随时联系：jingdu.email@gmail.com"
        ),
        "download_page_title": "生成与下载",
        "download_no_intake": "没有找到输入信息。请返回首页并重新提交表单。",
        "go_home": "返回首页",
        "download_intake_found": "✅ 找到输入信息。",
        "page_selected": "选择的页数：**{page_length}**",
        "download_info": "点击下面生成您的故事书PDF。在生成过程中请不要关闭此标签页。",
        "generate_button": "生成故事书",
        "spinner": "正在生成您的故事书...请保持此标签页打开",
        "generation_complete": "故事书生成完成！请在下面下载。",
        "download_button": "下载故事书PDF"
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
        "about_and_support": {"title": "关于与支持"},
        "download": {"title": "生成与下载"}
    }
}
